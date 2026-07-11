# 第8章 Kubernetes 入门

> **版本**：v0.1（初稿） | **编写日期**：2026-07-07 | **状态**：writing
> **前置章节**：第7章 容器化基础 | **后续章节**：第9章 服务网格与网关
> **建议学时**：3 学时（理论 2 + 实践 1）

---

## 8.0 学习目标

学完本章后，你将能够：

| 层次 | 目标 |
|------|------|
| **知识** | 理解 Kubernetes 集群的 Master-Node 架构与声明式管理哲学；掌握 Pod、Deployment、Service 三种核心资源的定义模型与生命周期；了解 ConfigMap 与 Secret 的适用场景与安全边界；认识 Helm 在包管理中的价值定位 |
| **能力** | 使用 `kubectl` 完成应用的部署、扩缩容、滚动更新和基础故障排查；独立编写符合生产规范的 YAML 资源清单文件；利用 Helm 安装和管理第三方 Chart |
| **素养** | 建立"期望状态调谐"的分布式系统设计思维，理解控制循环在自愈系统中的核心地位；养成配置与代码分离、基础设施声明化的工程习惯 |

---

## 8.1 情境导入：Hermes Delivery 的成长之痛

在第7章中，Hermes Delivery 完成了微服务容器化。四个核心服务——`order-service`（订单服务）、`dispatch-service`（调度服务）、`tracking-service`（轨迹追踪服务）和 `notification-service`（通知服务）——各自打包为 Docker 镜像，并用一个 `docker-compose.yml` 编排启动。

这个方案在开发和功能验证阶段表现良好。但随着产品进入内测，真实用户的涌入让隐藏的问题浮出水面：

**场景一：资源失衡**

周五下午五点半，订单量突然飙升到平时的三倍。`order-service` 的 CPU 占用率冲到 95%，响应时间从 50 毫秒恶化到 3 秒。与此同时，同一台机器上的 `notification-service` 正悠闲地消耗着 5% 的 CPU——它的工作高峰在订单完成后才到来。Docker Compose 把四个服务捆绑在同一台虚拟机上，资源分配的粒度太粗，没有办法说"给订单服务单独加两台机器"。

**场景二：凌晨报警**

某个周二的凌晨三点，运维工程师李明的手机响了。`dispatch-service` 因为一个边界条件 bug 导致进程崩溃。李明睡眼惺忪地登录服务器，找到挂掉的容器，手动执行 `docker restart dispatch-service`。他心想："如果系统能自己发现服务挂了并重启就好了。"——这个渴望就是对**自愈能力**的朴素表达。

**场景三：上线前的配置噩梦**

上线前最后一次全链路测试，需要在测试环境复现生产配置。数据库密码、消息队列地址、日志级别、第三方 API 密钥散落在四个地方：`docker-compose.yml` 里、各服务的环境变量文件中、启动脚本里、甚至直接写死在代码里。运维同事花了整整一个下午才确认测试环境的配置与生产环境一致——而且没有人敢保证没有遗漏。

这三个场景指向同一个结论：Docker 解决了"单台机器上的进程隔离"问题，但没有解决"多台机器上的服务编排"问题。Docker 让每个服务变成了标准化集装箱，但谁来管理这支集装箱船队？谁来告诉每艘船装什么、停哪、坏了怎么换？

这个"港口调度系统"，就是 **Kubernetes**（常缩写为 K8s，因为 k 和 s 之间有 8 个字母）。本章将带领你从零搭建 Hermes Delivery 的 Kubernetes 集群，用声明式的方式管理微服务生命周期——让凌晨三点的报警成为历史。

---

## 8.2 Kubernetes 核心架构

### 8.2.1 集群全景：两类节点的分工

一个 Kubernetes 集群由两类节点组成：**控制平面（Control Plane）**和**工作节点（Worker Node）**。理解它们的分工是理解 Kubernetes 运作方式的基础。

控制平面是集群的大脑，负责全局决策——哪些 Pod 调度到哪些节点、集群状态是否正确、如何响应故障。工作节点是集群的手脚，负责真正运行容器化的应用程序。

```
                        ┌─────────────────────────────────────────┐
                        │        Control Plane (Master 节点)        │
                        │                                          │
                        │  ┌──────────────┐  ┌──────────────────┐  │
                        │  │  API Server  │  │    Scheduler     │  │
                        │  │  (唯一入口)   │  │   (调度决策)     │  │
                        │  └──────┬───────┘  └────────┬─────────┘  │
                        │         │                   │            │
                        │  ┌──────┴───────────────────┴─────────┐  │
                        │  │              etcd                  │  │
                        │  │     (分布式 KV 存储：集群的"记忆")   │  │
                        │  └────────────────┬───────────────────┘  │
                        │                   │                      │
                        │  ┌────────────────┴───────────────────┐  │
                        │  │       Controller Manager           │  │
                        │  │  (Deployment/ReplicaSet/Node...    │  │
                        │  │   各种控制器持续运行)               │  │
                        │  └────────────────────────────────────┘  │
                        └─────────────────┬───────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
    ┌─────────▼─────────┐      ┌─────────▼─────────┐      ┌─────────▼─────────┐
    │   Worker Node 1   │      │   Worker Node 2   │      │   Worker Node 3   │
    │ ┌───────────────┐ │      │ ┌───────────────┐ │      │ ┌───────────────┐ │
    │ │    kubelet    │ │      │ │    kubelet    │ │      │ │    kubelet    │ │
    │ │  (节点代理)    │ │      │ │  (节点代理)    │ │      │ │  (节点代理)    │ │
    │ └───────┬───────┘ │      │ └───────┬───────┘ │      │ └───────┬───────┘ │
    │ ┌───────▼───────┐ │      │ ┌───────▼───────┐ │      │ ┌───────▼───────┐ │
    │ │  Container    │ │      │ │  Container    │ │      │ │  Container    │ │
    │ │  Runtime      │ │      │ │  Runtime      │ │      │ │  Runtime      │ │
    │ └───────┬───────┘ │      │ └───────┬───────┘ │      │ └───────┬───────┘ │
    │ ┌───────▼───────┐ │      │ ┌───────▼───────┐ │      │ ┌───────▼───────┐ │
    │ │ Pod  │ Pod    │ │      │ │ Pod  │ Pod    │ │      │ │ Pod  │ Pod    │ │
    │ └──────┴────────┘ │      │ └──────┴────────┘ │      │ └──────┴────────┘ │
    │ ┌──────────────┐  │      │ ┌──────────────┐  │      │ ┌──────────────┐  │
    │ │  kube-proxy  │  │      │ │  kube-proxy  │  │      │ │  kube-proxy  │  │
    │ └──────────────┘  │      │ └──────────────┘  │      │ └──────────────┘  │
    └───────────────────┘      └───────────────────┘      └───────────────────┘
```

**图 8-1 Kubernetes 集群架构全景**

### 8.2.2 控制平面四大组件

控制平面由四个核心组件构成，它们协同工作，构成了集群的中央神经系统：

**API Server**：集群的"前台窗口"。所有对集群的操作——无论是运维人员通过 `kubectl` 发出的指令，还是 Controller Manager 自身发起的调谐操作——都必须经过 API Server。它是唯一直接读写 etcd 的组件。这层统一入口的设计保证了操作的**可审计性**和**一致性**。

**etcd**：集群的"记忆"。这是一个基于 Raft 共识算法的分布式键值存储，保存着集群的全部状态——有哪些节点、运行着哪些 Pod、每个 Service 的端点列表是什么。etcd 是 Kubernetes 最关键的组件：如果 etcd 数据丢失，整个集群就失忆了，所有运行的工作负载虽然没有立刻消失，但 Kubernetes 不再知道它们的存在，也就无法管理和修复它们。

**Scheduler**：集群的"调度员"。当一个新 Pod 被创建但尚未分配节点时，Scheduler 监听 API Server 中的"待调度 Pod"事件，根据资源需求（CPU/内存）、亲和性规则、节点健康状况等因素，为每个 Pod 选择一个最优的 Worker Node。Hermes Delivery 中，如果 `order-service` 的 Pod 需要 256Mi 内存，Scheduler 只会把它分配到剩余内存大于 256Mi 的节点上。

**Controller Manager**：集群的"自动化巡检员"。它不是单一进程，而是多个控制器的集合体——Deployment Controller、ReplicaSet Controller、Node Controller 等。每个控制器都在执行同一个模式：**观察 → 比对 → 调谐**。例如，ReplicaSet Controller 观察到期望副本数为 3 但实际只有 2 个 Pod 在运行，于是通过 API Server 创建一个新 Pod。

### 8.2.3 工作节点三大守护进程

每个 Worker Node 上运行着三个关键进程：

**kubelet**：每个节点上的"现场监工"。它接收 API Server 下发的 Pod 定义，调用容器运行时（如 containerd）在本地创建和管理容器，并持续上报节点和 Pod 的健康状态。

**kube-proxy**：每个节点上的"网络管家"。它维护本节点的 iptables/IPVS 规则，确保发往某个 Service Cluster IP 的流量能被正确地负载均衡到后端的 Pod 实例上。

**Container Runtime**：真正运行容器的软件。Kubernetes 早期强依赖 Docker，但自 v1.24 起已移除对 Docker 的原生支持，转而通过 CRI（Container Runtime Interface）支持 containerd、CRI-O 等运行时。对学习者而言，镜像仍可用 `docker build` 构建，这与第 7 章完全兼容。

### 8.2.4 声明式管理：理解调谐循环

Docker Compose 采用**命令式**风格："启动三个 order-service 容器，端口映射到 8080"。你发出命令，它执行；如果容器挂了，它就停在那里——除非你再次发出命令。

Kubernetes 采用**声明式**风格：你提交一份 YAML 文件说"我希望任何时候都有 3 个 `order-service` Pod 在运行"。然后 Kubernetes 的 Controller Manager 进入一个**控制循环**（Control Loop）：

```
      ┌─────────────┐
      │  期望状态    │  ← 你提交的 YAML（replicas: 3）
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐     不一致      ┌──────────────┐
      │  观察实际状态 │ ───────────→  │  执行调谐操作  │
      └──────┬──────┘                └──────┬───────┘
             │                              │
             │     一致                      │
             ▼                              │
      ┌─────────────┐                       │
      │  什么都不做   │  ←────────────────────┘
      └─────────────┘
```

**图 8-2 调谐循环（Reconciliation Loop）**

这个循环永不停止。如果你在凌晨三点手动 `kill` 了一个 Pod，Controller Manager 会在几秒内发现"期望状态 = 3，实际状态 = 2"，然后自动创建一个新 Pod。Kubernetes 不会报警、不会抱怨、不会问为什么——它只是安静地把世界修正回你声明的样子。这就是**自愈**的本质。

> **思想实验**：假设你有一份声明"我书桌上的笔筒里永远有 3 支笔"。一个"笔筒控制器"每秒检查一次：如果只有 2 支，它取 1 支放进笔筒；如果有人偷偷拿走一支，它再补上。Kubernetes 就是这样一个永不疲倦的"笔筒控制器"。

---

## 8.3 Pod：原子调度单元

### 8.3.1 为什么不是"容器"而是 Pod

如果你刚学完第 7 章的 Docker，很自然地会问：Kubernetes 为什么不直接调度容器，而要引入一个 Pod 的概念？

答案是：**调度容器太细粒度了，有时你需要原子地调度一组紧密协作的容器**。Pod 是 Kubernetes 中**最小的、原子性的**调度单元——Scheduler 不会把 Pod 内的不同容器分散到不同 Node 上，要么一起调度，要么都不调度。

一个 Pod 内的所有容器共享：
- **网络命名空间**：同一个 Pod 内的容器共享一个 IP 地址和一个端口空间。这意味着 `container-A` 可以通过 `localhost:8080` 访问 `container-B`，无需任何网络配置。
- **IPC 命名空间**：可以通过 System V 信号量或 POSIX 消息队列通信。
- **存储卷（Volume）**：Pod 上挂载的 Volume 对所有容器可见。

```
┌──────────────────────────────────────┐
│               Pod                    │
│  Pod IP: 10.244.1.5                 │
│                                     │
│  ┌────────────────┐ ┌────────────┐  │
│  │  order-service │ │  日志采集器  │  │
│  │  (主容器)       │ │  (Sidecar) │  │
│  │  端口: 8080    │ │  读取 /logs│  │
│  └───────┬────────┘ └─────┬──────┘  │
│          │                │          │
│          └───────┬────────┘          │
│                  │                   │
│          ┌───────▼────────┐          │
│          │ 共享 Volume     │          │
│          │ /var/log/app   │          │
│          └────────────────┘          │
└──────────────────────────────────────┘
```

**图 8-3 Pod 内部结构：主容器 + Sidecar 容器共享网络和存储**

### 8.3.2 单容器 Pod 与多容器 Pod

> **最佳实践**：绝大多数情况下，**一个 Pod 只运行一个业务容器**。多容器 Pod 是为特定场景设计的，最常见的场景是**边车模式**（Sidecar Pattern）。

边车模式中，一个辅助容器运行在主容器旁边，增强主容器的功能但不修改主容器代码。典型案例：

| 场景 | 主容器 | 边车容器 |
|------|--------|----------|
| 日志采集 | 业务应用（写日志到文件） | Filebeat/Fluentd（读取文件，发送到日志中心） |
| 服务网格代理 | 业务应用 | Envoy sidecar（处理流量加密、遥测） |
| 配置热更新 | 业务应用 | Config Reloader（监听配置变更，通知主进程） |

Hermes Delivery 中，`order-service` 和它的日志采集器可以放在同一个 Pod 中。

### 8.3.3 第一个 Pod YAML：Hermes 订单服务

```yaml
# pod-order-service.yaml
apiVersion: v1
kind: Pod
metadata:
  name: order-service
  labels:
    app: order-service
    tier: backend
spec:
  containers:
    - name: order-service
      image: hermes-delivery/order-service:1.0
      ports:
        - containerPort: 8080
          name: http
      env:
        - name: DB_HOST
          value: "postgres-service"
        - name: LOG_LEVEL
          value: "info"
      resources:
        requests:          # 调度器用于决策的"最低保障"
          memory: "128Mi"
          cpu: "250m"      # 250 毫核 = 0.25 CPU 核心
        limits:            # 容器允许使用的"硬上限"
          memory: "256Mi"
          cpu: "500m"
      livenessProbe:       # 存活探针：容器是否"活着"
        httpGet:
          path: /health
          port: 8080
        initialDelaySeconds: 10
        periodSeconds: 15
```

> **代码 8-1**：`pod-order-service.yaml` —— 手动定义一个运行 order-service 的 Pod

这里有一个值得深究的细节：`resources.requests` 和 `resources.limits`。Scheduler 用 `requests` 来决定 Pod 能放在哪个节点上（"这个节点还有 256Mi 内存吗？"），而 kubelet 用 `limits` 来限制 Pod 的实际用量。如果容器试图使用超过 `limits` 的内存，它会被 OOM Killer 杀掉并重启。

> **经验之谈**：许多生产事故都源于没有正确设置 `resources`——一个"无限制"的 Pod 可能吃光整个节点的内存，导致同节点的其他 Pod 被驱逐。始终为每个容器设置 `requests` 和 `limits`，这是 Kubernetes 最佳实践中的第一条。

### 8.3.4 Pod 是"临时的"

Pod 的生命周期是**短暂的（Ephemeral）**。当 Pod 被删除（无论手动还是因节点故障），它的 IP 地址被回收、本地写入的文件被清除、甚至名字都可能永远不再使用。Kubernetes 从不"重启"一个 Pod——它销毁旧的，创建新的。

这就是为什么你永远不应该在 Kubernetes 中手动创建裸 Pod（Bare Pod）。裸 Pod 一旦消失就永远消失了——没有控制器会复活它。接下来介绍的 **Deployment** 正是为解决这个问题而生。

---

## 8.4 Deployment：声明式副本管理

### 8.4.1 Deployment 解决了什么

裸 Pod 有三个致命缺陷：
1. **不自愈**：Pod 挂了就挂了，没人管。
2. **无法滚动更新**：要升级镜像版本，必须先删旧 Pod 再建新 Pod——服务中断。
3. **无法扩缩容**：调整副本数需要手动创建或删除 Pod。

Deployment 是 Pod 之上的**控制器**。你声明期望的 Pod 数量、镜像版本、更新策略，Deployment Controller 保证实际状态始终向期望状态靠拢。

```
Deployment (order-service)
    │
    ├── 管理 ──→ ReplicaSet v1 (image: 1.0)
    │                ├── Pod (order-service-abc123)
    │                ├── Pod (order-service-def456)
    │                └── Pod (order-service-ghi789)
    │
    └── 滚动更新时创建 ──→ ReplicaSet v2 (image: 2.0)
                             ├── Pod (order-service-jkl012)
                             └── Pod (order-service-mno345) ...逐步替换
```

**图 8-4 Deployment → ReplicaSet → Pod 的层级管理关系**

注意到中间多了一层 **ReplicaSet** 吗？你通常不直接操作 ReplicaSet——Deployment 帮你管理它。但 ReplicaSet 的存在是实现滚动更新的关键：更新镜像时，Deployment 创建一个新的 ReplicaSet（使用新镜像），逐步增加新 ReplicaSet 的 Pod 数量，同时减少旧 ReplicaSet 的 Pod 数量。更新完成后，旧 ReplicaSet 保留（副本数缩为 0），作为回滚的依据。

### 8.4.2 Deployment YAML 详解

```yaml
# deployment-order-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  labels:
    app: order-service
spec:
  replicas: 3                         # 期望：始终保持 3 个副本
  revisionHistoryLimit: 5             # 保留最近 5 个 ReplicaSet（用于回滚）
  strategy:
    type: RollingUpdate               # 滚动更新策略
    rollingUpdate:
      maxSurge: 1                     # 更新期间最多允许超出期望数 1 个 Pod
      maxUnavailable: 1               # 更新期间最多允许不可用 1 个 Pod
  selector:
    matchLabels:
      app: order-service              # Deployment 通过此标签找到"自己的" Pod
  template:                           # Pod 模板（blueprint）
    metadata:
      labels:
        app: order-service
        version: "1.0"
    spec:
      containers:
        - name: order-service
          image: hermes-delivery/order-service:1.0
          ports:
            - containerPort: 8080
          envFrom:
            - configMapRef:
                name: hermes-config   # 引用第 8.6 节将创建的 ConfigMap
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: hermes-secret
                  key: DB_PASSWORD
          resources:
            requests:
              memory: "128Mi"
              cpu: "250m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          readinessProbe:              # 就绪探针：容器是否准备好接收流量？
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5     # 容器启动后等 5 秒再开始探测
            periodSeconds: 10          # 每 10 秒探测一次
          livenessProbe:               # 存活探针：容器是否需要重启？
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
```

> **代码 8-2**：`deployment-order-service.yaml` —— Hermes Delivery 订单服务的 Deployment 清单

两个探针的区别很重要，容易混淆：
- **readinessProbe（就绪探针）**：决定 Pod 是否**接收流量**。如果探测失败，Pod 从 Service 的端点列表中移除，但**不会重启**。
- **livenessProbe（存活探针）**：决定容器是否需要**重启**。如果探测失败，kubelet 杀掉容器并根据 `restartPolicy` 重建。

Hermes Delivery 中，`order-service` 启动后需要 5 秒初始化数据库连接，所以 `readinessProbe` 的 `initialDelaySeconds` 设为 5——在连接就绪之前，负载均衡器不会把流量导给它。

### 8.4.3 滚动更新：零停机部署

滚动更新是 Deployment 的默认更新策略，也是现代运维的标志性能力。假设你更新 `order-service` 的镜像从 1.0 到 2.0：

```bash
kubectl set image deployment/order-service \
  order-service=hermes-delivery/order-service:2.0
```

在 Kubernetes 内部，发生的步骤如下：

```
步骤 1: [v1 Pod A][v1 Pod B][v1 Pod C]           # 初始状态：3 个 v1 副本

步骤 2: [v1 Pod A][v1 Pod B][v1 Pod C][v2 Pod D]  # maxSurge=1，先创建 1 个 v2

步骤 3: [v1 Pod A][v1 Pod B][v2 Pod D][v2 Pod E]  # v2 Pod D 就绪后，停掉 C，创建 E

步骤 4: [v1 Pod A][v2 Pod D][v2 Pod E][v2 Pod F]  # 继续替换...  

步骤 5: [v2 Pod D][v2 Pod E][v2 Pod F]             # 更新完成：3 个 v2 副本
```

**图 8-5 滚动更新步骤示意（maxSurge=1, maxUnavailable=1）**

整个过程用户无感知——Service 只把流量导向处于 Ready 状态的 Pod（readinessProbe 通过的 Pod）。

如果新版本有问题（频繁崩溃、探测失败），Kubernetes 会自动停止滚动更新，保留一部分旧版本 Pod 继续服务。你可以随时回滚：

```bash
# 查看更新历史
kubectl rollout history deployment/order-service

# 回滚到上一个版本
kubectl rollout undo deployment/order-service

# 回滚到指定版本
kubectl rollout undo deployment/order-service --to-revision=2
```

### 8.4.4 扩缩容：应对流量洪峰

回到 Hermes Delivery 的场景——周五下午订单量飙升。在 Kubernetes 中，扩容只是修改一个数字：

```bash
kubectl scale deployment order-service --replicas=5
```

几秒内，两个新的 `order-service` Pod 被创建（只要集群有足够资源）。当高峰期过去后：

```bash
kubectl scale deployment order-service --replicas=3
```

如果流量具有明显的周期性（比如每天中午 12 点订单高峰），你还可以配置 **HorizontalPodAutoscaler**（HPA），让 Kubernetes 根据 CPU 或自定义指标自动调整副本数——但这属于进阶话题，我们将在第 11 章韧性设计部分展开。

---

## 8.5 Service：稳定的网络身份证

### 8.5.1 Pod IP 不可靠：问题的根源

Deployment 让 Pod 具备了自愈和滚动更新能力，但这带来一个新问题：**Pod 的 IP 地址不稳定**。每次重建 Pod，IP 都会变。如果 `dispatch-service` 内部硬编码了 `order-service` 某个 Pod 的 IP（如 `10.244.1.5`），当那个 Pod 被滚动更新替换后，`dispatch-service` 就会调用失败。

你需要一个"前台接待员"——不管后台哪个 Pod 在值班，前台总是同一个人接电话。这就是 **Service**。

### 8.5.2 Service 的工作机制

Service 通过**标签选择器（Label Selector）**与 Pod 建立关联。当 Deployment 创建 Pod 时，Pod 上带有标签（如 `app: order-service`）；Service 声明"我服务所有带 `app=order-service` 标签的 Pod"。

无论 Pod 如何新生或消亡，只要标签匹配且 readinessProbe 通过，Service 就自动将其加入负载均衡池。

```
                    ┌──────────────────────────┐
                    │      Service              │
                    │  名称: order-service       │
                    │  Cluster IP: 10.96.0.42   │
                    │  端口: 8080               │
                    │  选择器: app=order-service│
                    └──────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼─────┐  ┌──────▼───────┐  ┌─────▼─────────┐
    │  Pod A        │  │  Pod B       │  │  Pod C         │
    │  10.244.1.5   │  │  10.244.2.3  │  │  10.244.3.7    │
    │  Ready: true  │  │  Ready: true │  │  Ready: true   │
    │  app=order    │  │  app=order   │  │  app=order     │
    └───────────────┘  └──────────────┘  └────────────────┘
```

**图 8-6 Service 与 Pod 的对应关系：标签选择器是纽带**

### 8.5.3 Service 的三种类型

| 类型 | 可访问范围 | 使用场景 | Hermes Delivery 中的用途 |
|------|-----------|----------|-------------------------|
| **ClusterIP**（默认） | 仅集群内部 | 微服务间互相调用 | `order-service` 供 `dispatch-service` 内部调用 |
| **NodePort** | 集群外（通过 Node IP:30000-32767） | 开发调试、临时暴露 | 本地 Minikube 开发时快速访问前端 |
| **LoadBalancer** | 集群外（云厂商 LB） | 生产环境对外入口 | 将 `order-service` 的 REST API 暴露给外部客户端 |

### 8.5.4 Service YAML 与集群 DNS

```yaml
# service-order.yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
  labels:
    app: order-service
spec:
  type: ClusterIP
  selector:
    app: order-service         # 选择带有此标签的 Pod
  ports:
    - name: http
      protocol: TCP
      port: 8080               # Service 对外暴露的端口
      targetPort: 8080         # Pod 上容器的端口
```

> **代码 8-3**：`service-order.yaml` —— 为 order-service Pod 提供稳定的访问入口

创建 Service 后，Kubernetes 内置的 DNS 服务（CoreDNS）会自动注册一条 DNS 记录。集群内**任何 Pod** 都可以通过以下 DNS 名称访问 `order-service`：

- `order-service`（同一命名空间内，最常用）
- `order-service.default`（指定命名空间）
- `order-service.default.svc.cluster.local`（完整限定名）

Hermes Delivery 中，`dispatch-service` 需要调用 `order-service` 时，它的代码里只需写目标 URL `http://order-service:8080/api/orders`——不需要知道任何 Pod IP。这就是 Kubernetes 的服务发现机制。

---

## 8.6 ConfigMap 与 Secret：让配置和代码说再见

### 8.6.1 硬编码的代价

在第 7 章中，Hermes Delivery 各服务的配置（数据库地址、日志级别、消息队列地址）要么硬编码在代码中，要么通过环境变量传入。这导致一个严重问题：**镜像与环境耦合**。同一个 `order-service:1.0` 镜像，在开发环境连接的是 `dev-postgres`，在上线前却需要连接到 `staging-postgres`——你不得不重新构建镜像或手动覆盖环境变量。

Kubernetes 的配置管理哲学是：**镜像只包含应用程序本身，配置从外部注入**。ConfigMap 和 Secret 是两种注入载体。

### 8.6.2 ConfigMap：非敏感的、以数据为中心的配置

```yaml
# configmap-order.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: order-config
data:
  # 键值对形式（适合注入为环境变量）
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  LOG_LEVEL: "info"
  RABBITMQ_HOST: "rabbitmq-service"
  MAX_RETRY_COUNT: "3"
---
# 也可以存放整个配置文件
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
        listen 80;
        location /api/ {
            proxy_pass http://order-service:8080;
        }
    }
```

> **代码 8-4**：ConfigMap 的两种用法——键值对注入为环境变量，或整体挂载为文件

在 Deployment 中引用 ConfigMap 有三种方式：

```yaml
# 方式一：将整个 ConfigMap 的所有键注入为环境变量
envFrom:
  - configMapRef:
      name: order-config

# 方式二：选择性注入特定键
env:
  - name: DB_HOST
    valueFrom:
      configMapKeyRef:
        name: order-config
        key: DB_HOST

# 方式三：挂载为文件（适合配置文件）
volumeMounts:
  - name: nginx-config-volume
    mountPath: /etc/nginx/conf.d
volumes:
  - name: nginx-config-volume
    configMap:
      name: nginx-config
```

> **代码 8-5**：在 Deployment 中消费 ConfigMap 的三种方式

### 8.6.3 Secret：敏感信息保护

```yaml
# secret-order.yaml
apiVersion: v1
kind: Secret
metadata:
  name: order-secret
type: Opaque
stringData:                        # 开发环境可用 stringData（明文），创建时自动编码
  DB_PASSWORD: "hermes-pass-2024"
  RABBITMQ_PASSWORD: "guest"
  API_KEY: "sk-hermes-delivery-key"
```

> **代码 8-6**：`secret-order.yaml` —— 使用 `stringData` 明文编写，创建时自动转为 Base64

Secret 的消费方式与 ConfigMap 类似：

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: order-secret
        key: DB_PASSWORD
```

### 8.6.4 配置更新的"坑"与 Helix 方案

一个重要事实常被初学者忽略：**以环境变量方式注入的 ConfigMap 或 Secret 更新后，已运行的 Pod 不会自动感知**。环境变量只在容器启动时读取一次。要应用更新后的配置，必须重建 Pod（Deployment 的滚动更新会触发重建）。

而对于挂载为文件的 ConfigMap，kubelet 会定期同步（默认每 60 秒），应用程序可以监听文件变更实现热加载。

Helm Delivery 的最佳实践是：非敏感配置用 ConfigMap 挂载（配合应用的热加载能力），敏感信息用 Secret 以环境变量注入。配合 Helm（见 8.8 节），对 ConfigMap 内容的任何修改都会触发自动的滚动更新。

> **安全提醒**：Kubernetes Secret 默认以 Base64 编码存储——这不是加密！任何有权限读取 Secret 的用户或 Pod 都能轻松解码。生产环境必须配合 RBAC（基于角色的访问控制）、etcd 静态加密、以及外部密钥管理服务（如 HashiCorp Vault、AWS Secrets Manager）使用。我们将在第 12 章深入探讨服务安全。

---

## 8.7 kubectl：你的 K8s 瑞士军刀

### 8.7.1 命令范式

`kubectl` 的命令遵循一致的范式：

```
kubectl <动词> <资源类型> [资源名称] [选项]
```

掌握这个范式后，你可以灵活组合。以下将 Hermes Delivery 中最常用的操作分为"看"（查看）、"改"（变更）、"调"（调试）三类。

### 8.7.2 "看"——查看集群状态

```bash
# 查看所有 Pod（-o wide 显示节点和 IP）
kubectl get pods -o wide

# 持续监视 Pod 状态变化（-w = watch）
kubectl get pods -w

# 查看所有资源：Pod + Service + Deployment + ReplicaSet
kubectl get all

# 查看某类资源的详细信息（事件日志极有价值）
kubectl describe pod order-service-abc123
kubectl describe deployment order-service

# 以 YAML 格式输出资源的完整定义（用于备份或调试）
kubectl get deployment order-service -o yaml

# 查看资源标签
kubectl get pods --show-labels
```

### 8.7.3 "改"——创建与更新

```bash
# 从 YAML 文件创建/更新资源（声明式！apply 比 create 更常用）
kubectl apply -f deployment-order-service.yaml

# 从整个目录批量应用
kubectl apply -f ./k8s/

# 修改 Deployment 的镜像版本
kubectl set image deployment/order-service \
  order-service=hermes-delivery/order-service:2.0

# 扩缩容
kubectl scale deployment order-service --replicas=5

# 手动重启 Deployment 中的所有 Pod（滚动更新方式）
kubectl rollout restart deployment/order-service

# 删除资源（注意：delete 是立即生效的，apply 则有 merge 语义）
kubectl delete pod order-service-abc123       # Deployment 会自动重建
kubectl delete -f deployment-order-service.yaml
```

### 8.7.4 "调"——调试和排查

```bash
# 查看 Pod 日志（最常用的调试手段）
kubectl logs order-service-abc123          # 当前日志
kubectl logs order-service-abc123 -f       # 持续跟踪（Ctrl+C 退出）
kubectl logs order-service-abc123 --tail=50 # 最后 50 行

# 多容器 Pod 指定容器名
kubectl logs order-service-abc123 -c order-service

# 进入 Pod 内部执行命令（相当于 docker exec -it）
kubectl exec -it order-service-abc123 -- /bin/sh

# 端口转发：将本地 8080 映射到 Pod 的 8080
kubectl port-forward pod/order-service-abc123 8080:8080
# 现在可以用浏览器访问 http://localhost:8080 调试

# 查看 Service 的端点（确认是否正确关联了 Pod）
kubectl get endpoints order-service

# 查看滚动更新状态
kubectl rollout status deployment/order-service

# 查看更新历史（用于回滚决策）
kubectl rollout history deployment/order-service
```

### 8.7.5 实用技巧

- **`kubectl explain`**：忘了某个资源的字段结构？`kubectl explain deployment.spec.strategy.rollingUpdate` 会在终端显示完整文档。
- **别名**：在 `~/.bashrc` 中设置 `alias k=kubectl` 能节省大量打字时间。
- **上下文管理**：`kubectl config get-contexts` 和 `kubectl config use-context` 在多集群间切换。

---

## 8.8 Helm：Kubernetes 的应用商店

### 8.8.1 当你开始复制粘贴 YAML

在 8.9 节之前，我们已经为 `order-service` 写了 Deployment、Service、ConfigMap、Secret 四个 YAML 文件。Hermes Delivery 有四个微服务，再加上 PostgreSQL 和 RabbitMQ，总共大约 20 个 YAML 文件。这些文件中大量内容重复——每个 Deployment 的 `spec.template` 结构几乎一模一样，只是镜像名、端口号、副本数不同。

更糟的是，开发环境用 1 个副本、测试环境用 2 个副本、生产环境用 3 个副本——你是否要维护三套几乎相同的 YAML？

Helm 是 Kubernetes 的**包管理器**（类比 Ubuntu 的 `apt`、Python 的 `pip`），它通过**模板引擎**将"变量部分"（副本数、镜像版本、资源限制）从"结构部分"（Deployment 的 API 版本和固定字段）中分离出来，用一种叫 **Chart** 的格式打包。

### 8.8.2 Chart 的目录结构

```
hermes-delivery/
├── Chart.yaml              # Chart 元信息（名称、版本、描述）
├── values.yaml             # 默认配置值（"缺省的正确答案"）
├── values-dev.yaml         # 开发环境覆盖值
├── values-prod.yaml        # 生产环境覆盖值
├── templates/
│   ├── _helpers.tpl        # 可复用的模板函数
│   ├── deployment.yaml     # Deployment 模板
│   ├── service.yaml        # Service 模板
│   ├── configmap.yaml      # ConfigMap 模板
│   └── secret.yaml         # Secret 模板
└── charts/                 # 子 Chart 依赖
```

**图 8-7 Helm Chart 的标准目录结构**

### 8.8.3 模板语法示例

模板文件将 YAML 中的可变部分替换为 `{{ .Values.xxx }}` 占位符：

```yaml
# templates/deployment.yaml（片段）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-{{ .Chart.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          resources:
            requests:
              memory: {{ .Values.resources.requests.memory }}
              cpu: {{ .Values.resources.requests.cpu }}
            limits:
              memory: {{ .Values.resources.limits.memory }}
              cpu: {{ .Values.resources.limits.cpu }}
```

> **代码 8-7**：Helm 模板示例 —— 双花括号内的变量来自 `values.yaml`

对应的 `values.yaml` 提供默认值：

```yaml
# values.yaml
replicaCount: 3
image:
  repository: hermes-delivery/order-service
  tag: "1.0"
resources:
  requests:
    memory: "128Mi"
    cpu: "250m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

### 8.8.4 一条命令，多环境

有了 Helm Chart，部署到不同环境就是换一个值文件的事情：

```bash
# 开发环境
helm install hermes-dev ./hermes-delivery -f values-dev.yaml

# 生产环境
helm install hermes-prod ./hermes-delivery -f values-prod.yaml
```

升级与回滚也同样简洁：

```bash
# 修改 values.yaml 或模板后升级
helm upgrade hermes-dev ./hermes-delivery -f values-dev.yaml

# 查看发布历史
helm history hermes-dev

# 回滚到上一个版本
helm rollback hermes-dev
```

### 8.8.5 公共 Chart 仓库

不需要从零编写基础设施的 Chart。Helm 拥有活跃的社区仓库，一条命令即可安装生产级数据库：

```bash
# 添加 Bitnami 仓库（维护了大量生产就绪的 Chart）
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 安装 PostgreSQL
helm install postgres bitnami/postgresql \
  --set auth.password=hermes-pass-2024 \
  --set primary.persistence.size=10Gi

# 安装 RabbitMQ
helm install rabbitmq bitnami/rabbitmq
```

Hermes Delivery 的基础设施层（PostgreSQL + RabbitMQ）全都可以用社区 Helm Chart 一键部署，我们只需专注于编写四个微服务的应用层 Chart。

---

## 8.9 贯穿案例：Hermes Delivery 登上 Kubernetes

### 8.9.1 整体部署架构

```
                          ┌─────────────────────────────────────────────┐
                          │           Kubernetes Cluster                │
                          │                                             │
   ┌─────────┐            │  ┌───────────────────────────────────────┐  │
   │ 用户App  │──── HTTP ──→│  Service: order-api (LoadBalancer)      │  │
   └─────────┘            │  └───────────────┬───────────────────────┘  │
                          │                  │                          │
                          │  ┌───────────────▼───────────────────────┐  │
                          │  │  Deployment: order-service            │  │
                          │  │  replicas: 3                          │  │
                          │  │  ┌─────┐  ┌─────┐  ┌─────┐           │  │
                          │  │  │Pod A│  │Pod B│  │Pod C│           │  │
                          │  │  └──┬──┘  └──┬──┘  └──┬──┘           │  │
                          │  └─────┼────────┼────────┼──────────────┘  │
                          │        │        │        │                 │
                          │  ┌─────▼────────▼────────▼──────────────┐  │
                          │  │  Deployment: dispatch-service         │  │
                          │  │  replicas: 2                          │  │
                          │  └─────┬─────────────────┬──────────────┘  │
                          │        │                 │                 │
                          │  ┌─────▼──────┐  ┌──────▼──────────────┐  │
                          │  │ tracking   │  │ notification        │  │
                          │  │ replicas:2 │  │ replicas:2          │  │
                          │  └────────────┘  └─────────────────────┘  │
                          │                  │  │                      │
                          │       ┌──────────┘  └──────────┐           │
                          │  ┌────▼───────┐         ┌──────▼────────┐  │
                          │  │ PostgreSQL │         │   RabbitMQ    │  │
                          │  │  (Helm)    │         │   (Helm)      │  │
                          │  └────────────┘         └───────────────┘  │
                          │          ConfigMap / Secret                │
                          │   (DB_HOST, DB_PASSWORD, RABBITMQ, ...)    │
                          └────────────────────────────────────────────┘
```

**图 8-8 Hermes Delivery 在 Kubernetes 上的生产部署架构**

### 8.9.2 完整资源清单

以下是 Hermes Delivery 在 Kubernetes 上部署所需的核心资源清单。为了节省篇幅，这里展示 `order-service` 的完整清单，`dispatch-service`、`tracking-service` 和 `notification-service` 的结构完全相同（仅名称、镜像、端口不同）。

**步骤 1：创建命名空间**

```yaml
# 00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hermes
```

**步骤 2：创建 ConfigMap 和 Secret**

```yaml
# 01-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hermes-config
  namespace: hermes
data:
  DB_HOST: "postgres-postgresql.hermes.svc.cluster.local"
  DB_PORT: "5432"
  RABBITMQ_HOST: "rabbitmq.hermes.svc.cluster.local"
  RABBITMQ_PORT: "5672"
  LOG_LEVEL: "info"
  ORDER_SERVICE_URL: "http://order-service.hermes.svc.cluster.local:8080"
---
# 02-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: hermes-secret
  namespace: hermes
type: Opaque
stringData:
  DB_PASSWORD: "hermes-pass-2024"
  RABBITMQ_PASSWORD: "guest"
```

**步骤 3：部署四微服务**

```yaml
# 03-order-service.yaml (其余三个服务同理)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: hermes
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:
        - name: order-service
          image: hermes-delivery/order-service:1.0
          ports:
            - containerPort: 8080
          envFrom:
            - configMapRef:
                name: hermes-config
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: hermes-secret
                  key: DB_PASSWORD
          resources:
            requests:
              memory: "128Mi"
              cpu: "250m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: hermes
spec:
  selector:
    app: order-service
  ports:
    - port: 8080
      targetPort: 8080
  type: ClusterIP
```

> **代码 8-8**：Hermes Delivery 在 Kubernetes 上的完整部署清单

### 8.9.3 一键部署流程

```bash
# 1. 创建命名空间
kubectl create namespace hermes

# 2. 安装基础设施（使用 Helm）
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --namespace hermes \
  --set auth.password=hermes-pass-2024
helm install rabbitmq bitnami/rabbitmq \
  --namespace hermes

# 3. 部署应用层
kubectl apply -f ./k8s/ -n hermes

# 4. 验证部署状态
kubectl get all -n hermes

# 期望输出类似：
# NAME                              READY   STATUS    RESTARTS   AGE
# pod/order-service-abc123          1/1     Running   0          30s
# pod/order-service-def456          1/1     Running   0          30s
# pod/order-service-ghi789          1/1     Running   0          30s
# pod/dispatch-service-xxx          1/1     Running   0          30s
# pod/dispatch-service-yyy          1/1     Running   0          30s
# ...

# 5. 测试服务连通性
kubectl exec -n hermes deploy/dispatch-service -- \
  curl -s http://order-service:8080/health
# 预期返回 HTTP 200
```

### 8.9.4 从 Docker Compose 到 Kubernetes 的对比

| 维度 | Docker Compose | Kubernetes |
|------|---------------|------------|
| 调度范围 | 单台机器 | 集群（多台机器） |
| 自愈能力 | 无（需手动重启） | 自动（调谐循环） |
| 滚动更新 | 不支持 | 原生支持 |
| 服务发现 | 通过 Compose 网络 DNS | 原生 Service + CoreDNS |
| 配置管理 | 环境变量 / .env 文件 | ConfigMap + Secret |
| 扩缩容 | 手动修改 + 重启 | `kubectl scale` 或 HPA |
| 适用场景 | 开发、本地测试 | 生产、多环境 |

---

## 8.10 常见误区

### 误区 1："Pod 就是容器"

这是一个普遍存在的误解，尤其对于刚学完 Docker 的读者。**Pod 是 Kubernetes 的抽象层**，容器是运行在 Pod 内部的进程。Kubernetes 不直接管理容器——它管理 Pod，kubelet 再通过容器运行时管理容器。在大多数情况下，一个 Pod 确实只有一个容器，但这不意味着二者等同。当你需要写 `kubectl logs` 查看日志而 Pod 内有多个容器时，你很快就体会到二者差异了。

### 误区 2："Service 是 HTTP 反向代理"

Service 工作在网络第四层（传输层），基于 IP 和端口转发流量。它不解析 HTTP 头部，不能根据 URL 路径（如 `/api/orders` 和 `/api/users`）将请求路由到不同后端。如果你需要七层路由能力，需要使用 **Ingress** 资源配合 Ingress Controller（如 Nginx Ingress Controller、Traefik）。

### 误区 3："ConfigMap 改了，Pod 自动感知"

这只对了一半。如果你以**文件挂载**方式使用 ConfigMap，kubelet 会定期同步文件内容到 Pod 的挂载点（默认 60 秒），应用程序如果支持热加载就能生效。但如果你以**环境变量**方式注入，已运行的 Pod 完全不知情——环境变量仅在容器启动时设置一次。生产环境中，通常让 Deployment 的滚动更新来触发 Pod 重建。

### 误区 4："Secret 是安全的，可以提交到 Git"

Kubernetes Secret 默认仅以 Base64 编码——相当于把密码写在纸上但用铅笔。知道 `base64 -d` 命令的人都能解码。生产环境有三个必须：必须启用 etcd 静态加密、必须配置 RBAC 最小权限、必须将 Secret 排除在 Git 仓库之外（使用 `.gitignore` 或外部密钥管理服务）。

### 误区 5："kubectl apply 和 kubectl create 是一回事"

这两个命令虽然都能从 YAML 文件创建资源，但语义不同。`kubectl create` 是命令式的——如果资源已存在会报错。`kubectl apply` 是声明式的——如果资源存在则合并更新，不存在则创建。在 Kubernetes 的世界里应优先使用 `apply`，它与声明式管理哲学一脉相承：你只管声明期望状态，Kubernetes 负责达成它。

---

## 8.11 本章小结

本章从 Hermes Delivery 在 Docker Compose 阶段遇到的三个真实痛点出发，引入了 Kubernetes 集群编排。核心内容回顾如下：

```
Kubernetes 入门
│
├── 为什么需要 K8s ── 跨机器调度、自愈、滚动更新、配置外部化
│
├── 核心架构
│   ├── Control Plane：API Server / etcd / Scheduler / Controller Manager
│   └── Worker Node：kubelet / kube-proxy / Container Runtime
│
├── 五大核心资源
│   ├── Pod — 原子调度单元，共享网络和存储
│   ├── Deployment — 声明式副本管理 + 滚动更新 + 自愈
│   ├── Service — 稳定网络入口 + L4 负载均衡 + DNS 服务发现
│   ├── ConfigMap / Secret — 配置与代码分离
│   └── Helm Chart — 模板化打包 + 多环境管理 + 社区生态
│
├── 贯穿案例：Hermes Delivery 从 Docker Compose 迁移到 K8s
│   ├── 基础设施层：PostgreSQL + RabbitMQ（Helm 一键安装）
│   └── 应用层：order / dispatch / tracking / notification（kubectl apply）
│
└── 核心哲学
    ├── 声明式管理："说你要什么，而非怎么做"
    └── 调谐循环：Kubernetes 永不停止地修正现实以匹配声明
```

**关键术语表**：

| 术语 | 英文 | 释义 |
|------|------|------|
| 调谐循环 | Reconciliation Loop | Controller 持续比较期望状态与实际状态并自动修正的循环机制 |
| 声明式管理 | Declarative Management | 描述期望状态而非操作步骤的管理范式 |
| 边车模式 | Sidecar Pattern | 在同一 Pod 中运行辅助容器以增强主容器功能的设计模式 |
| 滚动更新 | Rolling Update | 逐步替换 Pod 实例的零停机部署策略 |
| 就绪探针 | Readiness Probe | 判断容器是否准备好接收流量的健康检查 |
| 存活探针 | Liveness Probe | 判断容器是否需要被重启的健康检查 |
| 标签选择器 | Label Selector | 通过键值对标签筛选 Kubernetes 资源的机制 |

---

## 8.12 练习

### 基础题（每题 5 分，共 25 分）

1. **调谐循环**：用自己的话解释图 8-2 中的调谐循环。如果 Hermes Delivery 的 `order-service` Deployment 声明 `replicas: 3`，但某个 Pod 所在的 Node 突然宕机，Kubernetes 内部会发生什么？

2. **三层关系**：Deployment、ReplicaSet、Pod 三者之间是什么关系？滚动更新时，Deployment 如何利用 ReplicaSet 来实现回滚？

3. **ConfigMap vs Secret**：两者都在管理配置，在 Hermes Delivery 中你会把数据库连接地址（DB_HOST）和数据库密码（DB_PASSWORD）分别放在哪里？为什么不能互换？

4. **kubectl 命令**：写出以下操作的完整 `kubectl` 命令——(a) 将 `dispatch-service` Deployment 扩容到 5 个副本；(b) 查看某个 Pod 的最近 30 行日志；(c) 进入 Pod 内部执行 `curl` 命令测试连通性。

5. **Helm 的价值**：比直接手写 20 个 YAML 文件，使用 Helm Chart 的核心优势是什么？`values-dev.yaml` 和 `values-prod.yaml` 解决的是什么问题？

### 综合题（每题 10 分，共 30 分）

6. **配置管理方案设计**：Hermes Delivery 需要支持三个环境——开发（dev）、测试（staging）、生产（prod）。每个环境的数据库地址、日志级别、副本数都不同。请设计一套 ConfigMap + Secret + Deployment 的配置管理方案，使得**同一个镜像**可以部署到三个环境而不做任何修改。画出资源之间的引用关系图。

7. **故障演练**：运维同事在测试环境故意 `kubectl delete pod` 删除了 `order-service` 的一个 Pod，不到 10 秒一个新的 Pod 就出现了，但 IP 已经不同。请详细解释这个过程中涉及了哪些 Kubernetes 组件，每步分别做了什么。

8. **滚动更新回滚**：Hermes Delivery 的 `order-service` 从 1.0 升级到 2.0 后，5 分钟内 readinessProbe 持续失败。请写出完整的诊断和回滚流程（含具体 `kubectl` 命令），并解释 `maxSurge` 和 `maxUnavailable` 参数如何保证了升级期间的可用性。

### 拓展题（每题 10 分，共 20 分）

9. **Pod 共址设计**：`order-service` 需要在每次请求结束后将结构化日志写入文件 `/var/log/order/access.log`，而公司要求所有服务的日志必须统一发送到中心的 Elasticsearch。技术架构规定不允许修改 `order-service` 的代码。你会如何利用 Pod 的多容器特性实现这个需求？画出 Pod 内部结构并解释 Sidecar 容器的工作流程。

10. **跨命名空间 DNS**：Hermes Delivery 部署在 `hermes` 命名空间，而公司的监控系统（Prometheus）部署在 `monitoring` 命名空间。Prometheus 需要定期访问 `order-service` 的 `/metrics` 端点采集指标。请写出 Prometheus 应该如何配置 `order-service` 的目标地址（利用 K8s DNS 的完整限定名），并说明命名空间在网络隔离中的作用。

---

> **编写说明**：
> - 本章假设读者已掌握第 7 章 Docker 基础，聚焦编排层而非容器原理
> - Hermes Delivery 贯穿案例延续第 7 章，在 8.9 节完成 Docker Compose → Kubernetes 的完整迁移
> - 架构图（图 8-1、图 8-8）当前为 ASCII 艺术版本，后续阶段将替换为 SVG 矢量图以提升出版质量
> - Helm 控制于"简介与基本使用"层面，深入应用（如自定义 Hook、Library Chart）留给第 13 章 CI/CD
> - 练习遵循基础→综合→拓展三层递进，综合题第 7、8 题可直接转化为课堂实验环节
> - 本章与第 7 章（Docker）构成"容器化→编排"的完整技术栈链条，为第 9 章服务网格做好基础设施准备
