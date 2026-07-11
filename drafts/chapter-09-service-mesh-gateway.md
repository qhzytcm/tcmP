# 第9章 服务网格与网关

> **一句话总结**：服务网格（Service Mesh）将流量管理、安全通信和可观测性从应用代码下沉到基础设施层，而 API 网关（API Gateway）则作为服务网格的"大门"，统一管理进出集群的所有流量。

---

## 9.1 学习目标

| 维度 | 目标 |
|------|------|
| **知识目标** | 理解服务网格的核心思想（Sidecar 模式与控制面/数据面分离）；掌握 Istio 的流量管理能力（路由、金丝雀发布、熔断）；理解 API 网关的职责与南北向流量模型 |
| **能力目标** | 能够编写 Istio VirtualService 和 DestinationRule 实现金丝雀发布与熔断；能够独立完成 Kong 或 APISIX 网关的基本配置；能够根据业务场景进行 Kong 与 APISIX 的选型分析 |
| **素养目标** | 建立"将非功能需求下沉到基础设施"的工程思维；理解云原生生态中"关注点分离"的设计哲学 |

---

## 9.2 情境导入：Hermes Delivery 的流量治理困境

经过前面几章的学习，小德的团队已经将 *Hermes Delivery* 的微服务成功部署到了 Kubernetes 集群上。系统运行得不错，但新的问题接踵而至——

**场景一：发布焦虑。** 每次上线新版本，工程师们都要熬到凌晨，祈祷别出问题。因为新旧版本是"一刀切"切换——要嘛 100% 用户用新版本，要嘛 100% 用旧版本。一旦新版本有 bug，所有用户同时受影响，只能紧急回滚。

**场景二：连锁雪崩。** 某个周五下午，`order-service` 因为数据库连接池耗尽开始响应变慢。按道理这不该影响其他服务——但 `user-service` 调用 `order-service` 时没有设置超时重试限制，大量请求堆积，很快 `user-service` 的线程池也被耗尽。接着调用 `user-service` 的 `gateway-service` 也崩溃了……短短三分钟，整个快递调度系统全线瘫痪。

**场景三：流量迷宫。** 系统里现在有 12 个微服务，服务间的调用关系错综复杂。运维团队想知道："一次快递下单请求到底经过了哪些服务？每个服务花了多少时间？"——没人能准确回答。

**这些问题的共性是什么？** 它们都涉及**服务间的通信治理**——而这些逻辑不应该由业务代码来操心。

> 本章将介绍两种关键基础设施：**服务网格（Service Mesh）** 将流量治理能力透明地注入服务间通信；**API 网关（API Gateway）** 则统一管理外部请求的入口。二者配合，构建起微服务体系的"交通控制系统"。

---

## 9.3 服务网格概述

### 9.3.1 微服务治理的演进：从"侵入式"到"零侵入"

让我们先回顾一下历史。在微服务架构早期，开发者在每个服务中引入"微服务框架库"（如 Spring Cloud、Dubbo、Netflix OSS）来获得服务发现、负载均衡、熔断等能力。

```
┌─────────────────────────────────────┐
│       早期模式：SDK 库模式           │
│                                     │
│  ┌──────────┐   ┌──────────┐       │
│  │  order-  │   │  user-   │       │
│  │  service │   │  service │       │
│  │ ┌──────┐ │   │ ┌──────┐ │       │
│  │ │业务   │ │   │ │业务   │ │       │
│  │ │逻辑   │ │   │ │逻辑   │ │       │
│  │ ├──────┤ │   │ ├──────┤ │       │
│  │ │Hystrix│ │   │ │Hystrix│ │  ← 治理逻辑嵌入每个服务
│  │ │Ribbon │ │   │ │Ribbon │ │
│  │ │Eureka │ │   │ │Eureka │ │
│  │ └──────┘ │   │ └──────┘ │       │
│  └──────────┘   └──────────┘       │
└─────────────────────────────────────┘
```

这种方式被称为**侵入式治理**——治理能力与业务代码混合在一起。它有几个致命缺陷：

1. **语言绑定**：Spring Cloud 只支持 Java，你的 Go 或 Python 服务享受不到同等能力
2. **升级噩梦**：升级框架版本需要重新编译和部署所有服务
3. **职责混淆**：业务开发者被迫关心熔断阈值、重试策略这些基础设施细节

**服务网格**的解法很优雅：把这些治理逻辑从应用进程中"拖出来"，放进一个独立的**代理进程**（称为 Sidecar）。这个 Sidecar 与应用容器部署在同一个 Pod 中，透明地拦截所有进出流量。

```
┌───────────────────────────────────────────────┐
│              服务网格：Sidecar 模式             │
│                                               │
│  ┌──────────────┐      ┌──────────────┐      │
│  │  Pod         │      │  Pod         │      │
│  │ ┌──────────┐ │      │ ┌──────────┐ │      │
│  │ │ order-   │ │      │ │ user-    │ │      │
│  │ │ service  │ │      │ │ service  │ │      │
│  │ │ (业务)    │ │      │ │ (业务)    │ │      │
│  │ └────┬─────┘ │      │ └────┬─────┘ │      │
│  │      │       │      │      │       │      │
│  │ ┌────┴─────┐ │      │ ┌────┴─────┐ │      │
│  │ │ Sidecar  │←┼──────┼→│ Sidecar  │ │      │
│  │ │ (Envoy)  │ │ mTLS │ │ (Envoy)  │ │      │
│  │ └──────────┘ │      │ └──────────┘ │      │
│  └──────────────┘      └──────────────┘      │
│           ↑                    ↑              │
│           └────────────────────┘              │
│              控制面 (Istiod) 下发配置          │
└───────────────────────────────────────────────┘
```

> **核心理念**：让应用只管业务逻辑，基础设施层来操心"服务怎么通信"。

### 9.3.2 Sidecar 与 Envoy：数据面的秘密

**Sidecar** 这个概念来源于摩托车侧面的挎斗——它不是摩托车本身，但紧紧附着在摩托车旁边，提供额外的运载能力。

在服务网格中，Sidecar 代理就是"挎斗"：
- 应用容器是"摩托车"——它不需要知道 Sidecar 的存在
- Sidecar 容器是"挎斗"——它透明地劫持所有进出流量

**Envoy** 是目前最流行的 Sidecar 代理实现（由 Lyft 开源，后捐赠给 CNCF）。它作为 Istio 默认的数据面代理，负责执行所有流量策略：路由、负载均衡、熔断、重试、限流——全部由 Envoy 完成。

Envoy 的关键能力：

| 能力 | 说明 |
|------|------|
| **透明劫持** | 通过 iptables 将 Pod 的进出流量重定向到 Envoy，应用无感知 |
| **动态发现** | 通过 xDS API 从控制面动态获取服务列表和路由规则 |
| **L7 路由** | 支持基于 HTTP Header、Path、Method 的精细路由 |
| **自动重试与超时** | 配置重试次数、超时时间、重试条件 |
| **mTLS** | 自动执行双向 TLS，加密服务间通信 |
| **丰富的遥测** | 自动采集请求数、延迟、错误率等指标 |

### 9.3.3 Istio 架构：控制面与数据面

**Istio** 是服务网格领域的事实标准（由 Google、IBM、Lyft 联合发起）。它的架构采用经典的控制面-数据面分离设计：

```
┌────────────────────────────────────────────────────┐
│                  Istio 架构                         │
│                                                    │
│  ┌─────────────────────┐                           │
│  │   控制面 (Istiod)    │                           │
│  │                     │                           │
│  │  ┌───────────────┐  │   xDS API ──────────┐    │
│  │  │ Pilot         │  │←─────────────────┐  │    │
│  │  │ (服务发现+路由)│  │                  │  │    │
│  │  ├───────────────┤  │    ┌─────────┐   │  │    │
│  │  │ Citadel       │  │    │         │   │  │    │
│  │  │ (证书管理)     │  │────│ Envoy   │───│──│──→ │
│  │  ├───────────────┤  │    │ (数据面) │   │  │    │
│  │  │ Galley        │  │    │         │   │  │    │
│  │  │ (配置校验)     │  │    └─────────┘   │  │    │
│  │  └───────────────┘  │    ┌─────────┐   │  │    │
│  └─────────────────────┘    │ Envoy   │───│──┘    │
│                              └─────────┘          │
│                              ┌─────────┐          │
│                              │ Envoy   │──────────┘
│                              └─────────┘
└────────────────────────────────────────────────────┘
```

| 组件 | 职责 | 类比 |
|------|------|------|
| **数据面** (Data Plane) | 由每个 Pod 旁的 Envoy Sidecar 组成，负责实际处理流量——转发、加密、记录 | 快递员：真正搬货、签收、拍照 |
| **控制面** (Control Plane) | Istiod（Istio 1.5+ 将 Pilot/Citadel/Galley 合并），负责配置管理、服务发现、证书签发 | 快递调度中心：分配路线、下发规则 |

这个分离设计的精妙之处在于：**控制面修改规则不需要重启数据面**。当你通过 Istio CRD 修改路由策略时，Istiod 通过 xDS 协议实时推送给所有 Envoy Sidecar，Envoy 热加载新配置，整个过程不影响正在处理中的请求。

> **术语解释**：xDS 是 Envoy 的发现服务（Discovery Service）协议族，包括 LDS（Listener）、RDS（Route）、CDS（Cluster）、EDS（Endpoint）等子协议。每个子协议负责发现一种配置维度。

---

## 9.4 流量管理

流量管理是服务网格最核心的能力。在 Istio 中，有两个关键的自定义资源（CRD）来定义流量规则：

- **VirtualService**：定义"流量去哪儿"——路由规则
- **DestinationRule**：定义"到了之后怎么做"——策略（负载均衡方式、熔断阈值、TLS 模式）

### 9.4.1 流量路由与负载均衡

最基础的流量路由：将请求按路径转发到不同服务版本。

```yaml
# VirtualService: 定义路由规则
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service-vs
  namespace: hermes-delivery
spec:
  hosts:
  - order-service  # 这个 VirtualService 作用于哪个服务
  http:
  - match:
    - uri:
        prefix: /api/v1/orders  # 匹配请求路径
    route:
    - destination:
        host: order-service  # 目标服务
        subset: v1           # 目标子集（在 DestinationRule 中定义）
        port:
          number: 8080
      weight: 100            # 权重 = 100%（全部流量到此子集）
```

```yaml
# DestinationRule: 定义子集和策略
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: order-service-dr
  namespace: hermes-delivery
spec:
  host: order-service
  subsets:
  - name: v1
    labels:
      version: v1.0.0     # 子集 v1 = 带有 label version=v1.0.0 的 Pod
  - name: v2
    labels:
      version: v2.0.0
  trafficPolicy:
    loadBalancer:
      simple: ROUND_ROBIN  # 负载均衡算法：轮询
```

### 9.4.2 金丝雀发布（Canary Release）

想象金丝雀在煤矿中的角色——矿工用它来检测瓦斯。如果金丝雀死了，矿工就赶紧撤离。

**金丝雀发布**同理：先让一小部分用户（例如 5%）尝试新版本，如果一切正常，逐渐增加比例，直到 100%。

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service-canary
  namespace: hermes-delivery
spec:
  hosts:
  - order-service
  http:
  - match:
    - headers:
        user-type:
          exact: beta          # Beta 用户走新版本
    route:
    - destination:
        host: order-service
        subset: v2
        port:
          number: 8080
  - route:                     # 默认规则：逐步金丝雀
    - destination:
        host: order-service
        subset: v1
        port:
          number: 8080
      weight: 90               # 90% 流量到旧版本
    - destination:
        host: order-service
        subset: v2
        port:
          number: 8080
      weight: 10               # 10% 流量到新版本
```

> **Hermes Delivery 实践**：小德的团队在发布 `order-service v2.0.0` 时，先用 5% 的流量测试 30 分钟。通过 Prometheus + Grafana 监控错误率和延迟——如果错误率上升超过 0.5%，自动回滚到 v1。

**金丝雀发布的步骤**（在 Istio 中）：

1. 部署新版本 Pod（不打生产流量标签）
2. 创建 DestinationRule，定义 v1/v2 子集
3. 创建 VirtualService，设置 `weight: 95`（v1）和 `weight: 5`（v2）
4. 观察指标 30 分钟
5. 逐步调整权重：5% → 20% → 50% → 100%
6. 完成全量切换后，下线老旧版本

### 9.4.3 熔断（Circuit Breaker）

还记得 **9.2 节的场景二** 吗？`order-service` 的数据库连接池耗尽，连锁拖垮了整个系统。**熔断器**就是为了阻止这种雪崩效应。

熔断器有三种状态，就像家里的电路保险丝：

```
      ┌──────────┐
      │  CLOSED  │ ← 正常状态：请求正常通过
      └────┬─────┘
           │ 错误率超过阈值
           ▼
      ┌──────────┐
      │   OPEN   │ ← 熔断状态：快速失败，拒绝请求
      └────┬─────┘
           │ 冷却时间过后
           ▼
      ┌──────────┐
      │ HALF_OPEN│ ← 半开状态：允许少量请求试探
      └────┬─────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 成功→CLOSED   失败→OPEN
```

在 Istio 中，熔断配置通过 DestinationRule 的 `connectionPool` 和 `outlierDetection` 来定义：

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: order-service-dr
  namespace: hermes-delivery
spec:
  host: order-service
  trafficPolicy:
    connectionPool:           # 连接池限制
      tcp:
        maxConnections: 100   # 最多 100 个并发 TCP 连接
      http:
        http1MaxPendingRequests: 50   # HTTP/1.1 最多 50 个等待请求
        http2MaxRequests: 100         # HTTP/2 最多 100 个并发请求
        maxRequestsPerConnection: 10  # 每个连接最多 10 个请求
    outlierDetection:          # 异常检测（触发熔断的条件）
      consecutive5xxErrors: 5        # 连续 5 次 5xx 错误 → 触发熔断
      interval: 30s                  # 每 30 秒评估一次
      baseEjectionTime: 60s          # 熔断后至少隔离 60 秒
      maxEjectionPercent: 50         # 最多隔离 50% 的实例
```

> **关键参数解释**：
> - `consecutive5xxErrors: 5`：连续 5 次返回 5xx 状态码，Envoy 将该实例标记为"不健康"，暂时移出负载均衡池
> - `baseEjectionTime: 60s`：被熔断的实例至少等待 60 秒才会被重新纳入负载均衡池
> - `maxEjectionPercent: 50`：防止过度熔断——最多隔离一半实例

### 9.4.4 故障注入与超时重试

**故障注入**是服务网格的一项独特能力——它可以**人为制造故障**来测试系统的韧性，而不需要修改任何业务代码。

```yaml
# 人为注入 3 秒延迟 + HTTP 500 错误，测试下游的容错能力
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service-fault
  namespace: hermes-delivery
spec:
  hosts:
  - order-service
  http:
  - fault:
      delay:
        percentage:
          value: 10        # 10% 的请求注入延迟
        fixedDelay: 3s     # 延迟 3 秒
      abort:
        percentage:
          value: 5         # 5% 的请求直接返回错误
        httpStatus: 500
    route:
    - destination:
        host: order-service
        subset: v1
```

**超时与重试**配置同样简洁：

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service-timeout
  namespace: hermes-delivery
spec:
  hosts:
  - order-service
  http:
  - timeout: 5s              # 请求超时 = 5 秒
    retries:
      attempts: 3            # 最多重试 3 次
      perTryTimeout: 2s      # 每次重试的超时
      retryOn: 5xx,reset    # 在 5xx 错误或连接重置时重试
    route:
    - destination:
        host: order-service
        subset: v1
```

> **在 Hermes Delivery 中的应用**：快递下单接口配置 `timeout: 5s` + 重试 3 次。如果 `order-service` 在 5 秒内未响应，Envoy 自动重试（最多 3 次）。如果三次重试都失败，Envoy 返回 503 给调用方，同时该实例被熔断器标记。

---

## 9.5 API 网关

### 9.5.1 网关的职责与流量方向

在讨论网关之前，我们需要理解两个流量方向：

| 方向 | 含义 | 示例 |
|------|------|------|
| **东西向流量** | 服务之间的内部调用 | `user-service` → `order-service` |
| **南北向流量** | 外部客户端到集群内服务的调用 | 手机 App → API → 集群内服务 |

```
              互联网
                │
    ┌───────────┴───────────┐
    │      API 网关          │  ← 南北向流量入口
    │   (Kong / APISIX)     │
    └───────────┬───────────┘
                │
   ┌────────────┼────────────┐
   │            │            │
   ▼            ▼            ▼
┌──────┐   ┌──────┐    ┌──────┐
│ 服务A │ ←→ │ 服务B│ ←→ │ 服务C│  ← 东西向流量（服务网格）
└──────┘   └──────┘    └──────┘
```

**服务网格主要负责东西向流量；API 网关主要负责南北向流量。** 二者职责互补，而非替代。

API 网关的核心能力：
- **认证与授权**：验证 API Key、JWT Token、OAuth2
- **限流与配额**：按用户/按 API 设置调用频率上限
- **请求转换**：改写 Header、路径重写、请求体转换
- **协议转换**：HTTP ↔ gRPC，REST ↔ GraphQL
- **路由与负载均衡**：将请求转发到正确的后端服务
- **可观测性**：集中记录所有 API 调用的日志和指标

### 9.5.2 Kong 核心概念

**Kong** 是由 Kong Inc. 开发的开源 API 网关（基于 OpenResty + LuaJIT，新版本也支持 Go 插件）。它的核心理念是**插件化**——任何功能都可以通过插件实现。

Kong 的核心概念层次结构：

```
Workspace（工作空间）
 └── Service（后端服务）── Route（路由规则）── Consumer（消费者）
      │                     │
      ├── 插件              ├── 插件
      │  (认证/限流/日志)   │  (认证/限流/日志)
```

| 概念 | 说明 | Hermes Delivery 对应 |
|------|------|---------------------|
| **Service** | 后端 API 服务的抽象（名称 + URL） | `order-service` → `http://order-service.hermes-delivery.svc.cluster.local:8080` |
| **Route** | 如何匹配请求并将其转发到 Service | `GET /api/v1/orders` → `order-service` |
| **Consumer** | API 的使用者（用户/应用） | 配送员 App、商家管理后台、用户小程序 |
| **Plugin** | 可插拔的功能模块 | JWT 认证、速率限制、日志记录 |

**Kong 网关配置示例**（使用 Kong Ingress Controller on Kubernetes）：

```yaml
# Hermes Delivery - 为快递下单 API 配置 Kong 限流与认证
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: rate-limiting
  namespace: hermes-delivery
config:
  minute: 100          # 每分钟最多 100 次请求
  policy: local
plugin: rate-limiting
---
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: jwt-auth
  namespace: hermes-delivery
plugin: jwt
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: order-api-ingress
  namespace: hermes-delivery
  annotations:
    konghq.com/plugins: jwt-auth,rate-limiting  # 绑定多个插件
spec:
  ingressClassName: kong
  rules:
  - host: api.hermes-delivery.com
    http:
      paths:
      - path: /api/v1/orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 8080
```

### 9.5.3 APISIX 核心概念

**Apache APISIX** 是另一款主流开源 API 网关（由中国公司 API7.ai 捐赠给 Apache 基金会）。与 Kong 类似，它也采用插件化架构，但有一个关键差异：

| 特性 | Kong | APISIX |
|------|------|--------|
| **数据存储** | PostgreSQL（必须） | etcd（灵活，可选 PostgreSQL） |
| **路由匹配** | 单一维度（path/host） | 多条件组合（支持表达式匹配） |
| **热加载** | 需要 reload Nginx | 完全热加载，零中断 |
| **性能** | ~20K QPS/核 | ~30K QPS/核（压测数据参考） |
| **插件生态** | 200+ 插件（商业化生态更成熟） | 100+ 插件（增长迅速） |
| **管理 API** | REST Admin API | REST Admin API + Dashboard |
| **多协议** | HTTP/gRPC/WebSocket/TCP | HTTP/gRPC/WebSocket/Dubbo/MQTT |

APISIX 的路由配置示例：

```yaml
# APISIX 路由配置（通过 APISIX Ingress Controller）
apiVersion: apisix.apache.org/v2
kind: ApisixRoute
metadata:
  name: order-route
  namespace: hermes-delivery
spec:
  http:
  - name: order-api
    match:
      hosts:
      - api.hermes-delivery.com
      paths:
      - /api/v1/orders
    backends:
    - serviceName: order-service
      servicePort: 8080
    plugins:
    - name: jwt-auth
      enable: true
    - name: limit-req
      enable: true
      config:
        rate: 100
        burst: 20
        key: remote_addr
```

### 9.5.4 Kong vs APISIX 选型分析

**选择 Kong 的场景**：
- 团队已有 PostgreSQL 运维经验（Kong 强依赖 PostgreSQL）
- 需要成熟的商业化生态（Kong Konnect、Kong Mesh）
- 企业在北美/欧洲市场（Kong 在这些地区社区更大）
- 需要大量现成插件（Kong 的插件市场更丰富）

**选择 APISIX 的场景**：
- 追求极致性能和完全热加载（配置变更不影响运行中请求）
- 使用 etcd 作为统一存储（与 Kubernetes 一致的基础设施）
- 多协议场景（特别是 Dubbo、MQTT 等非 HTTP 协议）
- 需要丰富的路由匹配表达式（不只是 path/host）

> **Hermes Delivery 的选型决策**：基于以下考量，小德的团队选择了 **APISIX**：
> 1. 团队在 Kubernetes 上已有 etcd 集群，不需要额外引入 PostgreSQL
> 2. 快递业务有波峰波谷（双十一、618），需要网关配置热加载来动态调整限流策略
> 3. 未来计划接入 IoT 传感器数据（MQTT 协议），APISIX 原生支持

---

## 9.6 实战：为 Hermes Delivery 配置 Istio 流量管理

### 场景说明

Hermes Delivery 的 `order-service` 即将发布 v2.0.0，带来了全新的"智能路线规划"功能。小德的团队需要：

1. 部署 v2.0.0 到集群
2. 对 Beta 用户直接路由到 v2
3. 对普通用户做 10% 金丝雀
4. 配置熔断防止雪崩
5. 观察 Golden Signals（延迟、流量、错误、饱和度）

### 步骤 1：部署 v2 版本

```bash
# 在 Kubernetes 中部署 v2.0.0（不打 service label，避免自动接流量）
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-v2
  namespace: hermes-delivery
  labels:
    app: order-service
    version: v2.0.0          # ← 关键：通过 version label 区分版本
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
      version: v2.0.0
  template:
    metadata:
      labels:
        app: order-service
        version: v2.0.0
    spec:
      containers:
      - name: order-service
        image: hermes-delivery/order-service:v2.0.0
        ports:
        - containerPort: 8080
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: order-config
              key: db_host
EOF
```

### 步骤 2：配置 DestinationRule 和 VirtualService

```yaml
# 01-destination-rule.yaml — 定义两个版本子集
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: order-service
  namespace: hermes-delivery
spec:
  host: order-service
  subsets:
  - name: v1
    labels:
      version: v1.0.0
  - name: v2
    labels:
      version: v2.0.0
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 60s
      maxEjectionPercent: 50
---
# 02-virtual-service.yaml — 流量分配策略
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service
  namespace: hermes-delivery
spec:
  hosts:
  - order-service
  http:
  - match:
    - headers:
        x-beta-user:
          exact: "true"              # Beta 用户标记
    route:
    - destination:
        host: order-service
        subset: v2
  - route:                          # 默认：金丝雀 10%
    - destination:
        host: order-service
        subset: v1
      weight: 90
    - destination:
        host: order-service
        subset: v2
      weight: 10
```

### 步骤 3：部署并验证

```bash
# 应用配置
kubectl apply -f 01-destination-rule.yaml
kubectl apply -f 02-virtual-service.yaml

# 验证 Istio 配置是否生效
istioctl proxy-status                              # 检查所有 Sidecar 同步状态
istioctl analyze -n hermes-delivery                # 配置有效性分析

# 发送测试流量
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://order-service.hermes-delivery:8080/api/v1/orders/health
done | sort | uniq -c

# 查看 Envoy 的实时统计
istioctl dashboard envoy order-service-v1-xxx-xxx  # 打开 Envoy 管理面板
```

### 步骤 4：监控金丝雀效果

```yaml
# Prometheus 查询示例（通过 Grafana Dashboard 展示）
# 查看 v1 vs v2 的请求分布
sum(rate(istio_requests_total{
  destination_service="order-service.hermes-delivery.svc.cluster.local",
  destination_version=~"v1.0.0|v2.0.0"
}[1m])) by (destination_version)

# 查看 v2 的错误率
sum(rate(istio_requests_total{
  destination_service="order-service.hermes-delivery.svc.cluster.local",
  destination_version="v2.0.0",
  response_code=~"5.*"
}[1m])) /
sum(rate(istio_requests_total{
  destination_service="order-service.hermes-delivery.svc.cluster.local",
  destination_version="v2.0.0"
}[1m]))
```

---

## 9.7 常见误区

> **误区 1："有了服务网格就不需要 API 网关了"**

这是最常见的误解。服务网格和 API 网关解决的是不同方向的问题：

| 对比维度 | 服务网格 | API 网关 |
|----------|---------|---------|
| 流量方向 | 东西向（服务间） | 南北向（外部↔内部） |
| 关注点 | 服务间通信治理 | API 生命周期管理 |
| 典型功能 | 熔断、重试、mTLS | 认证、限流、请求转换 |

**正确理解**：二者是互补关系。在实际架构中，外部请求经由 API 网关进入集群，集群内部的服务间通信由服务网格管理。

> **误区 2："Istio 这么强大，应该在所有项目中使用"**

Istio 确实功能强大，但它引入了明显的复杂性：
- 每个 Pod 多跑一个 Envoy Sidecar，增加 CPU 和内存开销（约增加 10-20% 资源消耗）
- 几十个 CRD 概念（VirtualService、DestinationRule、Gateway、Sidecar、PeerAuthentication……）学习曲线陡峭
- 调试困难：请求经过了两次代理（Sidecar → Sidecar），出问题时排查链路更长

**判断标准**：如果团队少于 5 人、服务少于 10 个、没有灰度发布需求——先别急着上 Istio，Kubernetes Service + Ingress 可能就够用了。等团队规模和服务数量增长后再引入也不迟。

> **误区 3："熔断器配置一次就不用改了"**

熔断阈值不是银弹。不同的服务有不同的容忍度：
- 支付服务：可能 `consecutive5xxErrors: 3`（高度敏感，快速熔断）
- 日志服务：可能 `consecutive5xxErrors: 20`（可容忍较多失败，因为不是核心路径）
- 推荐服务：熔断后可以采用静态推荐作为降级（对可用性要求不那么苛刻）

**正确做法**：根据服务的 SLA（Service Level Agreement）和业务关键程度，为每个服务单独调优熔断参数。同时定期回顾——流量模式变了，阈值也需要跟着调整。

> **误区 4："API 网关选 Kong 还是 APISIX，看性能测试谁 QPS 高就够了"**

性能只是选型的一个维度。更重要的是：
- **团队技能栈**：有 PostgreSQL DBA 吗？（Kong 强依赖）还是更熟悉 etcd？（APISIX 默认）
- **运维能力**：能否自己维护 etcd 集群？还是希望用已有的 RDS PostgreSQL？
- **协议需求**：需要 Dubbo/MQTT 支持吗？
- **社区与商业支持**：在中国市场有技术支持需求吗？

---

## 9.8 本章小结

### 思维导图

```
服务网格与网关
├── 服务网格（Service Mesh）
│   ├── 核心思想：治理逻辑下沉到基础设施
│   ├── Sidecar 模式（Envoy）
│   │   ├── 透明流量劫持
│   │   ├── L7 路由、mTLS、遥测
│   │   └── xDS 动态配置发现
│   ├── Istio 架构
│   │   ├── 数据面（Envoy 集群）
│   │   └── 控制面（Istiod）
│   └── 流量管理
│       ├── VirtualService：路由规则
│       ├── DestinationRule：负载均衡 + 熔断 + 子集
│       ├── 金丝雀发布：weight 渐进式切流
│       ├── 熔断：outlierDetection 自动隔离故障实例
│       └── 故障注入：人为制造故障测试韧性
├── API 网关
│   ├── 职责：南北向流量、认证、限流、转换
│   ├── Kong：PostgreSQL + LuaJIT，插件生态成熟
│   └── APISIX：etcd + 热加载，多协议支持
└── 二者关系：互补，网格管东西向，网关管南北向
```

### 关键术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 服务网格 | Service Mesh | 将服务间通信治理下沉到基础设施层（Sidecar 代理层）的架构模式 |
| Sidecar | Sidecar Proxy | 与应用容器部署在同一 Pod 中的代理容器，透明拦截所有进出流量 |
| Envoy | Envoy Proxy | 由 Lyft 开源的 L7 代理，Istio 的默认数据面实现 |
| Istio | Istio | CNCF 毕业项目，最流行的服务网格实现 |
| 控制面 | Control Plane | 负责配置管理、服务发现、证书签发的中心组件（Istiod） |
| 数据面 | Data Plane | 由 Envoy Sidecar 组成的代理集群，执行流量策略 |
| VirtualService | VirtualService | Istio CRD，定义路由规则（流量去哪儿） |
| DestinationRule | DestinationRule | Istio CRD，定义目标策略（负载均衡、熔断、TLS） |
| 金丝雀发布 | Canary Release | 渐进式将流量从旧版本切换到新版本的部署策略 |
| 熔断器 | Circuit Breaker | 自动检测故障服务并暂时隔离，防止雪崩效应的模式 |
| xDS | xDS API | Envoy 的动态发现服务协议族 |
| API 网关 | API Gateway | 统一管理外部流量进入微服务集群的入口组件 |
| 南北向流量 | North-South Traffic | 外部客户端与集群内服务之间的流量 |
| 东西向流量 | East-West Traffic | 集群内部服务之间的流量 |

---

## 9.9 练习

### 基础题（5 题）

**题 1** 请用自己的话解释：服务网格的 Sidecar 模式与传统的 SDK 库模式（如 Spring Cloud）相比，有哪些核心优势？（提示：从语言绑定、升级维护、职责分离三个角度回答）

**题 2** 阅读以下 VirtualService 配置，回答问题：
```yaml
http:
- match:
  - headers:
      x-canary:
        exact: "enabled"
  route:
  - destination:
      host: payment-service
      subset: v2
- route:
  - destination:
      host: payment-service
      subset: v1
    weight: 80
  - destination:
      host: payment-service
      subset: v2
    weight: 20
```
（1）如果一个请求不带 `x-canary` Header，它会被路由到哪个版本？
（2）如果一个请求带有 `x-canary: enabled` Header，它会被路由到哪个版本？

**题 3** 在 Istio 的熔断配置中，`consecutive5xxErrors`、`baseEjectionTime`、`maxEjectionPercent` 三个参数分别控制什么行为？如果 `maxEjectionPercent` 设置为 100 会有什么风险？

**题 4** API 网关和服务网格的职责有什么不同？为什么说二者是互补而非替代关系？

**题 5** 请列举至少三个你需要 API 网关（而不是直接用 Kubernetes Ingress）的场景。

### 综合题（3 题）

**题 6** Hermes Delivery 的 `tracking-service`（快递轨迹服务）即将发布 v3.0.0。新版本对数据库查询做了重构，团队担心可能有性能退化。请设计一套完整的金丝雀发布方案，包括：
- DestinationRule 和 VirtualService 配置
- 监控指标选择（至少三个）
- 回滚触发条件和自动化策略

**题 7** 某电商系统在促销期间发生了以下故障链：`inventory-service` 响应变慢（从 50ms 到 5s）→ `order-service` 线程池耗尽 → `cart-service` 级联崩溃。请设计一套 Istio 配置方案来防止此类雪崩，并说明每种配置的作用。

**题 8** 某团队正在 Kong 和 APISIX 之间做技术选型。他们的场景如下：
- 10 人团队，有 MySQL DBA，没有 etcd 运维经验
- 业务主要是 REST API，计划半年后接入 MQTT 协议的 IoT 设备
- 双十一期间流量是平时的 10 倍，需要动态调整限流策略
- 总部在中国，社区支持和中文文档很重要

请基于以上信息撰写一份选型建议（300 字以内），给出推荐方案及理由。

### 拓展题（2 题）

**题 9** （研究型）Envoy 的 xDS 协议分为 LDS、RDS、CDS、EDS、SDS 等多个子协议。请查阅 Envoy 官方文档，绘制一张图描述这些子协议之间的关系，并说明当一个新的服务实例上线时，xDS 如何在控制面和数据面之间传播这一变更。

**题 10** （项目型）在 Hermes Delivery 项目中，当前 API 网关的限流策略对所有用户一视同仁。但实际上，高级会员（Premium）应该有更高的调用配额。请设计一套方案，利用 Kong 或 APISIX 的 Consumer + Plugin 机制实现分层限流：
- 普通用户：每分钟 60 次
- 高级会员：每分钟 300 次
- 管理员：不限制
并给出关键配置代码。

---

## 9.10 实验：Istio 流量管理动手实践

> **实验环境要求**：Kubernetes ≥ 1.28、Istio ≥ 1.20、kubectl 已配置、Minikube 或 Kind 本地集群

### 实验目标
在本地 Kubernetes 集群中部署一个简单微服务，配置 Istio 实现金丝雀发布、熔断和故障注入。

### 实验步骤

**1. 部署示例应用（BookInfo 或自定义应用）**
```bash
# 为命名空间启用 Istio 自动注入
kubectl create namespace istio-lab
kubectl label namespace istio-lab istio-injection=enabled

# 部署一个简单的 HTTP 服务（v1 和 v2 两个版本用不同颜色和大小的响应区分）
kubectl apply -f https://raw.githubusercontent.com/istio/istio/master/samples/httpbin/httpbin.yaml -n istio-lab
```

**2. 配置金丝雀发布**
```bash
# 创建 DestinationRule 和 VirtualService，设置 v1:90% / v2:10% 的权重
# 然后用 curl 循环发送 100 次请求，统计 v1 和 v2 的响应比例
```

**3. 配置熔断并测试**
```bash
# 使用 fortio（负载测试工具）向服务发送大量请求
# 观察当 consecutive5xxErrors 达到阈值时，Envoy 是否自动隔离故障实例
kubectl apply -f samples/httpbin/sample-client/fortio-deploy.yaml -n istio-lab
FORTIO_POD=$(kubectl get pods -n istio-lab -l app=fortio -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $FORTIO_POD -n istio-lab -c fortio -- fortio load -c 50 -t 60s http://httpbin:8000/get
```

**4. 故障注入测试韧性**
```bash
# 配置 VirtualService 注入 5 秒延迟，观察调用方是否触发超时重试
# 然后注入 HTTP 503 错误，观察熔断器行为
```

**5. 使用 Kiali 可视化服务拓扑**
```bash
# 启动 Kiali Dashboard，查看流量分布和请求延迟
istioctl dashboard kiali
```

### 实验报告要求
提交一份 Markdown 格式的实验报告，包含：
1. 实验环境的版本信息（kubectl version、istioctl version）
2. 金丝雀发布测试的请求分布截图
3. 熔断触发前后的 Envoy 日志片段
4. Kiali 服务拓扑截图
5. 实验心得（200 字以内）

---

> **本章完成。** 下一章我们将探讨微服务体系的"神经系统"——可观测性（日志、指标、链路追踪），让你真正拥有对分布式系统的"全局视野"。
