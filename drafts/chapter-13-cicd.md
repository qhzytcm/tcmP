# 第13章 CI/CD 流水线

> **摘要**：如果把微服务架构比作一座城市的道路系统，那么 CI/CD 流水线就是这座城市的市政工程队伍——它确保每次道路改造（代码变更）都能安全、高效地交付到市民（用户）手中，而不会导致交通瘫痪（服务中断）。
>
> 本章从「为什么微服务更需要自动化部署」出发，系统讲解 CI/CD 的核心概念、GitHub Actions 多服务流水线设计、蓝绿部署与金丝雀发布两种零停机策略，深入 GitOps 理念，并以 ArgoCD 为工具演示 GitOps 落地的完整流程。全章围绕贯穿案例 *Hermes Delivery* 快递调度系统展开，所有代码示例均可直接运行。

---

## 学习目标

| 层次 | 目标 | 检验方式 |
|------|------|----------|
| **知识** | 理解 CI/CD 的核心概念与价值；掌握 GitHub Actions 的工作流语法；理解蓝绿部署与金丝雀发布的原理及适用场景；掌握 GitOps 的核心原则 | 基础题 1~5 |
| **能力** | 能使用 GitHub Actions 为多服务项目编写构建、测试与部署流水线；能区分不同部署策略的适用场景并做出合理选型；能使用 ArgoCD 搭建基本的 GitOps 部署流程 | 综合题 6~8 |
| **素养** | 建立「一切皆代码」的工程思维；理解自动化不仅是效率工具，更是质量保障的基石 | 拓展题 9~10、课堂讨论 |

> **建议学时**：2 学时（理论 1.5 + 案例分析与演示 0.5）

---

## 情境导入

*Hermes Delivery* 已经完成了微服务拆分，团队也壮大到了 12 人。然而新的问题出现了：

> 「小王提交了一段订单服务的代码，本地测试通过了，但部署到测试环境后把支付接口搞崩了——因为他在本地用的是旧版 SDK。更糟糕的是，我们不知道是谁、在什么时候、改了什么导致的问题。」

这是典型的"手动部署之痛"：环境差异、人为失误、回滚困难、缺乏可追溯性。软件工程中有句名言：

> "如果一件事让你感到痛苦，那就把它自动化。"

本章要解决的问题正是：**如何让代码从开发者的笔记本电脑，安全、一致、可追溯地抵达生产环境？**

---

## 13.1 CI/CD 概述：从手动部署到自动化

### 13.1.1 什么是 CI/CD？

CI/CD 是两个紧密相连但各有侧重的实践：

| 缩写 | 全称 | 中文 | 核心关注点 |
|------|------|------|-----------|
| CI | Continuous Integration | 持续集成 | 代码变更频繁合并到主干，自动构建+测试 |
| CD | Continuous Delivery / Deployment | 持续交付/部署 | 将通过测试的代码自动部署到目标环境 |

**持续集成（CI）** 解决的是"集成地狱"——当多个开发者各自在分支上工作数天甚至数周，合并时往往伴随着大量冲突和回归问题。CI 要求开发者每天至少一次将代码合并到主干，每次合并触发自动化的构建和测试。

**持续交付（CD）** 在 CI 的基础上更进一步：让软件在任何时刻都处于"可发布"状态。而**持续部署**则是交付的最高级形态——每次通过所有测试的变更自动部署到生产环境，无需人工审批。

```
CI/CD 成熟度阶梯：

Level 0: 手动构建，手动部署（FTP 上传时代）
Level 1: 每日构建，手动部署
Level 2: 每次提交自动构建+测试（CI）
Level 3: 自动构建+测试+部署到预发环境（Continuous Delivery）
Level 4: 通过测试即自动上线（Continuous Deployment）
```

### 13.1.2 一条典型 CI/CD 流水线的解剖

一条标准的 CI/CD 流水线通常包含以下阶段：

```
[开发提交代码] → [代码检出] → [依赖安装] → [编译构建]
                                                ↓
[生产部署] ← [审批门禁] ← [预发验证] ← [镜像打包]
```

常见的流水线工具包括：

| 工具 | 类型 | 特点 |
|------|------|------|
| GitHub Actions | SaaS | 与 GitHub 深度集成，社区生态丰富 |
| GitLab CI | SaaS/自托管 | 内置容器注册表，配置灵活 |
| Jenkins | 自托管 | 老牌工具，插件生态最丰富，学习曲线陡峭 |
| Tekton | Kubernetes 原生 | 云原生设计，声明式流水线 |

本书以 **GitHub Actions** 为主讲工具，原因有三：(1) 与课程代码仓库 GitHub 无缝集成；(2) 对开源项目免费；(3) YAML 配置文件直观易学。

### 13.1.3 为什么微服务更需要 CI/CD？

回到 *Hermes Delivery* 的架构——截至目前，系统已拆分为至少 5 个独立服务（订单服务、支付服务、调度服务、用户服务、通知服务）。手动部署一个服务可能只需 5 分钟，但部署 5 个服务：

- 需要逐一确认每个服务的正确版本号
- 需要确保服务间 API 版本兼容
- 部署顺序可能影响系统稳定性
- 一旦出问题，排查范围从 1 个服务扩大到全部交互链路

**CI/CD 流水线的核心价值**就是把这些重复、易错的操作交给机器，让人专注于创造性的开发工作。

---

## 13.2 GitHub Actions 基础

### 13.2.1 核心概念

在开始编写流水线之前，先厘清三个关键概念：

| 概念 | 说明 |
|------|------|
| **Workflow**（工作流） | 定义在 `.github/workflows/` 下的 YAML 文件，描述一条完整的自动化流程 |
| **Job**（作业） | Workflow 中的独立执行单元，默认并行运行，可配置依赖关系 |
| **Step**（步骤） | Job 中的具体操作，可以是运行脚本，也可以是调用社区 Action |

**Action** 是 GitHub Actions 生态的核心——它是可复用的最小执行单元，类似编程中的"函数"。社区提供了数千个现成的 Action，涵盖代码检出、环境准备、镜像构建、部署通知等常见场景。

### 13.2.2 第一个 Workflow：Go 服务构建与测试

以下是一个针对 *Hermes Delivery* 订单服务的简化 CI 流水线：

```yaml
# .github/workflows/order-service-ci.yml
name: Order Service CI

on:
  push:
    branches: [main]
    paths:
      - 'services/order/**'
  pull_request:
    branches: [main]
    paths:
      - 'services/order/**'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout 代码
        uses: actions/checkout@v4

      - name: 安装 Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.21'

      - name: 缓存依赖
        uses: actions/cache@v4
        with:
          path: ~/go/pkg/mod
          key: ${{ runner.os }}-go-${{ hashFiles('services/order/go.sum') }}

      - name: 代码静态检查
        run: |
          go install golang.org/x/lint/golint@latest
          cd services/order
          golint ./...

      - name: 运行单元测试
        run: |
          cd services/order
          go test -v -race -coverprofile=coverage.out ./...

      - name: 上传覆盖率报告
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: services/order/coverage.out
```

> **设计意图解读**
>
> 1. `paths` 过滤器：仅当订单服务代码变更时才触发，避免修改其他服务代码时浪费 CI 资源
> 2. `actions/cache`：缓存 Go 模块依赖，平均可节省 40~60 秒的安装时间
> 3. `-race` 标志：启用 Go 的数据竞争检测器，在 CI 阶段就能发现并发 bug
> 4. `upload-artifact`：将测试覆盖率报告保存为构建产物，便于后续分析

### 13.2.3 Job 间的依赖与并行

当项目包含多个需要独立构建的服务时，可以利用 Job 的依赖关系实现"扇形展开-扇形合并"模式：

```yaml
# .github/workflows/hermes-ci.yml
name: Hermes Delivery 全服务 CI

on:
  push:
    branches: [main]

jobs:
  # 第1阶段：所有服务并行构建
  build-order:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd services/order && go build ./...

  build-payment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd services/payment && go build ./...

  build-dispatch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd services/dispatch && go build ./...

  # 第2阶段：所有服务构建成功后才执行集成测试
  integration-test:
    needs: [build-order, build-payment, build-dispatch]   # ← 依赖声明
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 启动服务并运行集成测试
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 10  # 等待服务就绪
          go test ./integration/...
          docker-compose -f docker-compose.test.yml down
```

这个工作流的核心设计在于 `needs` 声明：integration-test 作业必须等待三个构建作业全部完成才开始执行。这种模式的优势是：**构建阶段各服务并行执行（快），集成测试在最后统一把关（稳）**。

---

## 13.3 多服务流水线设计

### 13.3.1 一个仓库，多个服务——流水线该怎么设计？

*Hermes Delivery* 采用了 **Monorepo**（单一代码仓库）的结构，所有微服务共享一个 Git 仓库。这种组织方式在管理流水线时面临一个核心问题：

> 当用户服务有变更时，是不是该重新构建和部署订单服务？

答案显然是否定的。合理的策略是**按变更范围触发**。下面对比三种主流策略：

| 策略 | 思路 | 优点 | 缺点 |
|------|------|------|------|
| **文件路径过滤** | 用 `paths` 精确指定触发范围 | 简单直接 | 代码共享模块（如 common 包）变更时需要额外处理 |
| **Matrix 策略** | 用一个动态矩阵遍历所有服务 | 统一管理，DRY 原则 | 无法按需触发，浪费 CI 资源 |
| **条件作业** | 编写脚本检测变更，用 `if` 控制作业开关 | 最灵活 | 实现复杂度高 |

在实践中，推荐**文件路径过滤 + 公共模块检测**的组合方案。以下是一个实际可用的配置：

```yaml
# .github/workflows/smart-ci.yml
name: Smart CI — 按变更触发

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # 检测是否有公共代码变更
  detect-common-changes:
    runs-on: ubuntu-latest
    outputs:
      common_changed: ${{ steps.check.outputs.common_changed }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - id: check
        run: |
          if git diff --name-only HEAD~1 HEAD | grep -q '^common/'; then
            echo "common_changed=true" >> $GITHUB_OUTPUT
          else
            echo "common_changed=false" >> $GITHUB_OUTPUT
          fi

  # 订单服务 CI（仅订单或公共代码变更时触发）
  test-order:
    needs: detect-common-changes
    if: |
      needs.detect-common-changes.outputs.common_changed == 'true' ||
      contains(github.event.head_commit.modified, 'services/order/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd services/order && go test ./...
```

这里的关键技巧是 `job.outputs` —— 上一个 Job 的计算结果可以通过 `$GITHUB_OUTPUT` 传递给后续 Job 的 `if` 条件，实现跨 Job 的信息传递。

### 13.3.2 构建 Docker 镜像并推送到容器注册表

CI 产出的是"能否部署"的判断，而 CD 需要的是"可部署的制品"。对于容器化项目，这个制品就是 Docker 镜像。以下是推送镜像到 GitHub Container Registry 的标准步骤：

```yaml
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write     # ← 关键：授予推送镜像的权限
    
    steps:
      - uses: actions/checkout@v4

      - name: 登录 GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: 构建并推送镜像
        uses: docker/build-push-action@v5
        with:
          context: ./services/order
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/order-service:${{ github.sha }}
            ghcr.io/${{ github.repository }}/order-service:latest
```

**镜像标签（Tag）策略**是这里的一项重要工程决策。上述配置使用了双标签策略：

- `${{ github.sha }}`：Git 提交的 SHA 哈希，确保每次构建的镜像可唯一追溯
- `latest`：标记最新版本，方便快速拉取

生产环境中通常还会加上语义版本号（如 `v1.2.3`）和分支名（如 `main` 或 `release-1.x`）。

---

## 13.4 蓝绿部署与金丝雀部署

CI 保证代码"能跑"，CD 负责代码"该怎么上"。对于 *Hermes Delivery* 这样的在线服务，部署策略直接影响用户体验。下面介绍两种核心的零停机部署模式。

### 13.4.1 蓝绿部署（Blue-Green Deployment）

**核心思想**：同时维护两套完全相同的生产环境——蓝色（当前版本）和绿色（新版本）。切换时通过负载均衡器将流量从蓝环境瞬间切换到绿环境。

```
部署前：                 部署后（切换完成）：
┌─────────────┐         ┌─────────────┐
│  用户请求    │         │  用户请求    │
└──────┬──────┘         └──────┬──────┘
       │                       │
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│ 负载均衡器   │         │ 负载均衡器   │
└──┬───────┬──┘         └──┬───────┬──┘
   │       │               │       │
   ▼       ▼               ▼       ▼
┌─────┐ ┌─────┐       ┌─────┐ ┌─────┐
│ 🟦  │ │ 🟩  │       │ 🟦  │ │ 🟩  │
│ v1  │ │ v2  │  →    │空闲 │ │ v2  │ ← 活跃
└─────┘ └─────┘       └─────┘ └─────┘
```

**蓝绿部署的优势与代价**：

| 优势 | 代价 |
|------|------|
| 回滚极快（切回蓝环境即可） | 需要双倍硬件资源 |
| 零停机时间 | 数据库 schema 变更需向后兼容 |
| 可在切流量前进行充分验证 | 长期占用两套环境成本高 |

在 GitHub Actions 中，蓝绿部署通常通过更新 Kubernetes Service 或 Ingress 的目标来实现。简化示例如下：

```yaml
- name: 部署到绿环境
  run: |
    kubectl apply -f k8s/order-service-green.yaml
    kubectl wait --for=condition=ready pod -l app=order,version=green --timeout=120s

- name: 切换流量
  run: |
    kubectl patch service order-service -p '{"spec":{"selector":{"version":"green"}}}'
```

### 13.4.2 金丝雀部署（Canary Deployment）

**核心思想**：先将新版本部署给一小部分用户（如 5%），观察一段时间（通常 10-30 分钟），确认无异常后逐步扩大流量比例，直到 100% 完成切换。

```
金丝雀部署的流量渐进过程：

 100% │                                    ████████████
      │                              ██████
  50% │                        ██████
      │                  ██████
  10% │            ██████
   5% │      ██████
   0% │████████──────────────── v1 ────────────────
      └────────────────────────────────────────────→ 时间
      部署 v2    观察期    扩大      继续扩大    全量切换
      (5%流量)  (10min)  (25%)      (50%)      (100%)
```

金丝雀部署相比蓝绿部署的核心优势在于**风险控制更精细**——即使新版本有问题，也只影响极小比例的用户。但对于非生产流量足够大的系统（如企业内部系统），蓝绿部署可能更简单实用。

> **"金丝雀"这个名字的由来**：煤矿工人下井时会带一只金丝雀——金丝雀对一氧化碳极为敏感，如果金丝雀停止鸣叫，矿工就知道该撤离了。软件工程中借用这个比喻：让一小部分用户来"试毒"，比让所有人都暴露在风险中要安全得多。

### 13.4.3 选型决策：什么时候用哪种？

| 场景 | 推荐策略 | 原因 |
|------|----------|------|
| 关键业务系统，用户量大 | 金丝雀部署 | 渐进验证，风险可控 |
| 内部系统，用户量小 | 蓝绿部署 | 实现简单，管理成本低 |
| 移动端 App（需审核） | 蓝绿部署 | 审核通过后立即切换 |
| API 服务（无状态） | 金丝雀或蓝绿均可 | 取决于团队运维能力 |
| 有状态服务（数据库等） | 需特别设计 | 两种策略都不能直接套用 |

---

## 13.5 GitOps 理念

### 13.5.1 什么是 GitOps？

**GitOps** 是一套以 Git 仓库作为"单一事实来源（Single Source of Truth）"的运维范式。其核心理念可以用一句话概括：

> **Git 里有什么，集群里就有什么。集群的实际状态会持续向 Git 中声明的期望状态收敛。**

传统的 CI/CD 流程中，CI 工具"推（Push）"代码到目标环境；而 GitOps 的设计是**让集群内的 Agent "拉（Pull）"期望状态并自动对齐**。

```
传统 Push 模式：                      GitOps Pull 模式：

开发者 push 代码                       开发者 push 代码+部署清单
      │                                       │
      ▼                                       ▼
  CI 构建镜像                            CI 构建镜像 + 更新 Git
      │                                       │
      ▼                                       ▼
  CD 工具推送部署                     GitOps Agent 拉取并同步
  (kubectl apply)                      (如 ArgoCD / Flux)
      │                                       │
      ▼                                       ▼
  Kubernetes 集群                      Kubernetes 集群
```

### 13.5.2 GitOps 的四大原则

| 原则 | 说明 | 实践方式 |
|------|------|----------|
| **声明式** | 系统配置必须可声明，而非命令式脚本 | Kubernetes YAML / Helm / Kustomize |
| **版本控制** | 所有系统状态存储在 Git 中 | 部署清单文件存放于 Git 仓库 |
| **自动同步** | 系统自动拉取并应用期望状态 | ArgoCD / Flux 定期或 Webhook 触发 |
| **持续调和** | 持续检测偏差并自动修复 | 控制器不断对比期望状态与实际状态 |

### 13.5.3 GitOps 与传统 CI/CD 的对比

| 维度 | 传统 CI/CD（Push） | GitOps（Pull） |
|------|-------------------|-----------------|
| 触发方式 | CI 工具推送部署指令 | 集群 Agent 拉取 Git 状态 |
| 凭证管理 | CI 系统持有生产集群凭证 | 凭证留在集群内，不暴露给 CI |
| 审计追溯 | 依赖 CI 运行历史 | Git 提交历史天然可审计 |
| 回滚 | 执行反向部署操作 | `git revert` + 自动同步 |
| 灾后自愈 | 需要人工介入 | Agent 检测到偏差后自动修复 |

**GitOps 最优雅的特性**是"自动回滚"：如果生产环境出现故障，运维人员只需 `git revert` 上一个提交并推送，GitOps Agent 检测到期望状态变化后会自动将集群恢复到之前的稳定版本。整个过程不需要直接接触集群。

---

## 13.6 ArgoCD 演示

### 13.6.1 ArgoCD 简介

ArgoCD 是 CNCF（云原生计算基金会）的毕业项目，也是最流行的 GitOps 工具。它的核心架构如下：

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Git 仓库    │    │    ArgoCD    │    │  Kubernetes  │
│              │    │              │    │   集群       │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │ 部署清单  │ │◄───│ │ Repo     │ │    │ │ 实际资源  │ │
│ │ (YAML)   │ │    │ │ Server   │ │    │ │ (Pod/Svc) │ │
│ └──────────┘ │    │ └────┬─────┘ │    │ └─────┬────┘ │
│              │    │      │       │    │       │       │
│              │    │      ▼       │    │       │       │
│              │    │ ┌──────────┐ │    │       │       │
│              │    │ │ App      │◄├────┼───────┘       │
│              │    │ │ Controller││    │               │
│              │    │ └──────────┘ │    │               │
└──────────────┘    └──────────────┘    └──────────────┘
```

ArgoCD 的 Application Controller 不断执行以下循环：

1. 从 Git 仓库拉取期望状态（部署清单）
2. 从 Kubernetes 集群获取实际状态
3. 对比两者——如不一致，将实际状态向期望状态同步
4. 通过 Web UI 或 CLI 展示同步状态

### 13.6.2 为 Hermes Delivery 配置 ArgoCD

首先，在 *Hermes Delivery* 的 Git 仓库中创建部署清单目录结构：

```
hermes-delivery/
├── services/          # 源代码
│   ├── order/
│   ├── payment/
│   └── dispatch/
├── deploy/            # 部署清单（GitOps 仓库视角）
│   ├── base/
│   │   ├── order-service.yaml
│   │   ├── payment-service.yaml
│   │   └── dispatch-service.yaml
│   └── overlays/
│       ├── staging/
│       │   └── kustomization.yaml
│       └── production/
│           └── kustomization.yaml
└── .github/workflows/  # CI 流水线
```

一个典型的服务部署配置如下：

```yaml
# deploy/base/order-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  labels:
    app: order-service
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
          image: ghcr.io/hermes-delivery/order-service:v1.2.0
          ports:
            - containerPort: 8080
          env:
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: order-config
                  key: db.host
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
spec:
  selector:
    app: order-service
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

然后通过 ArgoCD CLI 或 Web UI 创建 Application（应用）定义，将 Git 仓库路径与集群中的实际资源关联：

```yaml
# argo-app-order.yaml (安装在 ArgoCD 中)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: order-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/hermes-delivery/hermes-delivery.git
    targetRevision: main
    path: deploy/overlays/staging
  destination:
    server: https://kubernetes.default.svc
    namespace: hermes-staging
  syncPolicy:
    automated:
      prune: true       # 自动删除 Git 中已移除的资源
      selfHeal: true    # 自动修复偏离期望状态的资源
```

关键配置解读：
- `repoURL` / `targetRevision` / `path`：告诉 ArgoCD 去哪里找期望状态
- `syncPolicy.automated.prune: true`：当 Git 中删除了某个资源定义时，集群中对应的资源也会被自动清理
- `syncPolicy.automated.selfHeal: true`：如果有人手工修改了集群中的配置（kubectl edit），ArgoCD 会在 3 分钟内检测到偏离并自动恢复

### 13.6.3 完整工作流：代码提交到自动部署

将 CI（GitHub Actions）与 CD（ArgoCD）串联后，*Hermes Delivery* 的完整交付流程如下：

```
1. 开发者提交代码到 main 分支
       │
2. GitHub Actions 触发：构建、测试、推送镜像
       │
3. GitHub Actions 自动更新部署清单中的镜像 Tag
   （git commit 更新 deploy/overlays/... 中的 image 字段）
       │
4. ArgoCD 检测到 Git 仓库变更
       │
5. ArgoCD 自动同步新版本到 Kubernetes 集群
       │
6. 健康检查通过，部署完成
```

第 3 步是 CI 与 CD 的**衔接点**。在 GitHub Actions 中实现镜像 Tag 自动更新的关键步骤：

```yaml
- name: 更新部署清单中的镜像 Tag
  run: |
    cd deploy/overlays/staging
    
    # 使用 yq 工具更新 YAML 中的镜像版本
    yq -i ".images[0].newTag = \"${{ github.sha }}\"" kustomization.yaml
    
    git config user.name "hermes-bot"
    git config user.email "bot@hermes-delivery.dev"
    git add .
    git commit -m "ci: 更新订单服务镜像至 ${{ github.sha }}"
    git push
```

> **安全性提示**：上述示例中 Git 推送依赖于 CI 环境的认证。在生产实践中，应使用 GitHub Deploy Key 或 Personal Access Token（存储于 GitHub Secrets）进行认证，避免在代码中暴露凭证。

---

## 常见误区

### 误区 1：「CI/CD 太复杂，小团队不需要」

**真相**：团队越小，CI/CD 的收益反而越大。小团队人手紧张，自动化能释放大量重复劳动时间。一个 3 人团队如果每次手工部署需要 20 分钟、每天部署 2 次，一个月就消耗了约 20 小时——超过半个工程师的工作量。GitHub Actions 对公共仓库完全免费，对私有仓库每月提供 2000 分钟免费额度，成本几乎为零。

### 误区 2：「蓝绿部署 = 金丝雀部署，只是叫法不同」

**真相**：两者有本质区别。蓝绿部署是**整体切换**（一次性将 100% 流量切到新版本），金丝雀部署是**渐进切换**（逐步增加新版本流量比例）。蓝绿部署侧重于回滚速度，金丝雀部署侧重于风险控制粒度。

### 误区 3：「GitOps 就是"把部署配置放在 Git 里"」

**真相**：放在 Git 里只是必要条件，不是充分条件。真正的 GitOps 必须包含 **Pull 模式**的自动同步和**持续调和**机制。如果还是用 CI 工具主动推送部署，那只是"用 Git 管理配置的 Push CD"，不是 GitOps。区分的关键在于：**谁在主动——是 CI 工具推送到集群，还是集群内的 Agent 拉取 Git 状态？**

### 误区 4：「有了 CI/CD 就不需要 Code Review 了」

**真相**：CI/CD 自动化验证的是"代码是否正确运行"，而 Code Review 关注的是"设计是否合理、代码是否可维护"。两者解决不同层次的问题，互补而非替代。实际上，成熟的 CI/CD 流水线通常将 Code Review（如 GitHub 的 branch protection + required reviewers）作为部署的前置门禁。

---

## 本章小结

```
                           ┌─────────────────────────┐
                           │     CI/CD 流水线全景     │
                           └────────────┬────────────┘
                                        │
          ┌─────────────────┬───────────┼───────────┬─────────────────┐
          ▼                 ▼           ▼           ▼                 ▼
   ┌────────────┐   ┌────────────┐ ┌─────────┐ ┌──────────┐   ┌──────────┐
   │ CI：持续集成 │   │ 多服务流水线 │ │  部署策略 │ │ GitOps  │   │ ArgoCD   │
   │            │   │            │ │         │ │         │   │          │
   │• 自动构建   │   │• 文件路径过滤 │ │• 蓝绿    │ │• Pull模式│   │• Application│
   │• 自动测试   │   │• Job依赖编排 │ │• 金丝雀  │ │• 声明式  │   │• 自动同步  │
   │• 快速反馈   │   │• 镜像制品化  │ │• 选型决策 │ │• 自愈    │   │• Web UI   │
   └────────────┘   └────────────┘ └─────────┘ └──────────┘   └──────────┘
```

### 关键术语表

| 术语 | 英文 | 简明释义 |
|------|------|----------|
| 持续集成 | Continuous Integration (CI) | 频繁合并代码并自动构建测试 |
| 持续部署 | Continuous Deployment (CD) | 通过测试的变更自动部署到生产 |
| 蓝绿部署 | Blue-Green Deployment | 维护两套环境，切换流量完成部署 |
| 金丝雀部署 | Canary Deployment | 渐进式将新版本暴露给少量用户 |
| GitOps | Git Operations | 以 Git 为单一事实来源的运维范式 |
| ArgoCD | — | CNCF 毕业的 GitOps 工具 |
| Workflow | — | GitHub Actions 中的自动化流程定义 |
| Monorepo | — | 多项目/多服务共享单一代码仓库 |
| 制品 | Artifact | CI 产出的可部署产物（如 Docker 镜像） |
| 持续调和 | Continuous Reconciliation | GitOps Agent 不断对齐实际状态与期望状态 |

---

## 练习

### 基础题（5 题）

1. 简述持续集成（CI）和持续交付/部署（CD）的区别，并说明为什么微服务架构比单体架构更需要 CI/CD。
2. 解释 GitHub Actions 中 Workflow、Job、Step 三者之间的关系，并画出一个包含 2 个并行 Job 的 Workflow 结构图。
3. 什么是蓝绿部署？相比传统的滚动更新，它的核心优势是什么？代价又是什么？
4. 用自己的话解释 GitOps 的"Pull 模式"和传统 CI/CD 的"Push 模式"的区别。
5. 在 ArgoCD 配置中，`syncPolicy.automated.prune` 和 `selfHeal` 分别是什么作用？

### 综合题（3 题）

6. *Hermes Delivery* 目前有 5 个微服务，采用 Monorepo 管理。请设计一套 GitHub Actions 流水线方案，满足以下要求：(a) 仅构建和测试有变更的服务，(b) 公共代码变更时重新测试所有服务，(c) 所有服务测试通过后才构建 Docker 镜像。画出 Workflow 的结构图并说明设计理由。
7. 假设 *Hermes Delivery* 的订单服务正在进行一次重大重构，涉及数据库 schema 变更。请分析这种情况下蓝绿部署和金丝雀部署分别面临什么挑战，你会选择哪种策略？为什么？
8. 某团队声称已经"实施了 GitOps"——他们把所有 Kubernetes YAML 文件放在 Git 仓库里，用 Jenkins 定时执行 `kubectl apply`。请判断这算不算真正的 GitOps，并给出你的理由和改进建议。

### 拓展题（2 题）

9. **研究性学习**：查阅 Argo Rollouts 的官方文档，了解它如何实现比 Kubernetes 原生 Deployment 更精细的金丝雀发布（如基于 Header/Cookie 的流量路由、自动回滚、流量分析等）。写一份不超过 500 字的介绍，与本章介绍的 ArgoCD 进行对比。
10. **动手实践**：为你自己开发过的一个项目（或 *Hermes Delivery* 的任意一个服务）搭建一条完整的 CI/CD 流水线，要求包含：(a) GitHub Actions 自动构建与测试，(b) Docker 镜像推送，(c) 使用 ArgoCD（可通过 Minikube + ArgoCD 本地搭建）实现 GitOps 部署。提交你的 Workflow 配置文件和 ArgoCD Application 定义。

---

> **编写说明**：本章代码示例基于 GitHub Actions、Docker ≥ 24.0、Kubernetes ≥ 1.28、ArgoCD ≥ 2.8 编写。实验所需环境配置见附录。
