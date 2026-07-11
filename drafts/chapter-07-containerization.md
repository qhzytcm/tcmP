# 第7章 容器化基础

---

## 学习目标

| 维度 | 目标 |
|------|------|
| **知识目标** | 理解 Docker 镜像、容器、仓库的核心概念及其关系；掌握 Dockerfile 的常用指令与多阶段构建原理；理解 Docker Compose 的服务编排模型 |
| **能力目标** | 能独立编写 Dockerfile 将 Go 服务打包为轻量镜像；能使用 docker-compose 编排多服务应用并管理网络/数据卷 |
| **素养目标** | 建立"基础设施即代码"的工程意识；理解容器化如何消除"在我机器上能跑"的经典困境 |

---

## 7.1 情境导入：Hermes Delivery 的部署困境

李明的团队正在开发 *Hermes Delivery* 快递调度系统。第一个里程碑到来时，系统由四个 Go 服务组成：订单服务（order-service）、调度服务（dispatch-service）、骑手服务（courier-service）和 API 网关（api-gateway）。每个服务依赖不同的运行时配置——订单服务需要连接 PostgreSQL，调度服务依赖 Redis 做实时位置缓存，API 网关需要配置 Nginx 反向代理。

当李明把代码交给运维同事王磊部署时，问题接踵而至：

> "dispatch-service 在我机器上跑得好好的，怎么到测试服务器上就报 `GLIBC_2.32 not found`？"
>
> "你本地 Go 是 1.22，服务器装的是 1.21，`range over func` 语法不支持！"
>
> "PostgreSQL 版本不一致，订单服务的迁移脚本跑了一半就失败了……"

这些问题有一个共同的名字：**环境不一致**。传统部署模式下，开发环境、测试环境、生产环境的差异会导致大量"在我机器上能跑"式的无效排查。更麻烦的是，四个服务散落在不同的机器上，启动顺序、端口冲突、日志收集——每个环节都可能成为部署的"拦路虎"。

这一章，我们将引入 **Docker 容器化技术**，从根本上解决 Hermes Delivery 面临的部署困境。学完本章后，你将能用一条命令在任意机器上拉起整个快递调度系统。

---

## 7.2 Docker 核心概念

Docker 是一个开源的应用容器引擎，它将应用程序及其依赖打包到一个可移植的容器中，然后发布到任何支持 Docker 的 Linux/Windows/macOS 机器上运行。理解 Docker 的核心，需要首先搞清三个关键概念：**镜像**、**容器**和**仓库**。

### 7.2.1 镜像（Image）：应用的"蓝图"

**镜像**是一个只读的模板，包含了运行应用程序所需的完整文件系统——代码、运行时、系统工具、系统库和配置。可以把它类比为面向对象编程中的"类"：类定义了对象的结构，但类本身不能直接使用；镜像定义了容器的内容，但镜像本身只是一个静态的打包文件。

```text
┌─────────────────────────────────────┐
│            容器镜像（Image）          │
│  ┌─────────────────────────────┐    │
│  │         应用代码层            │    │  ← 你的 Go 二进制 + 配置
│  ├─────────────────────────────┤    │
│  │         运行时依赖层          │    │  ← CA 证书、时区数据、静态文件
│  ├─────────────────────────────┤    │
│  │         系统依赖层            │    │  ← libc、OpenSSL 等系统库
│  ├─────────────────────────────┤    │
│  │         基础系统层            │    │  ← alpine/ubuntu 最小化发行版
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

图 7-1 容器镜像的分层结构

Docker 镜像采用**联合文件系统（UnionFS）** 技术，由多个只读层叠加组成。每一层代表 Dockerfile 中的一条指令。这种分层设计的优势在于：

- **复用**：多个镜像可以共享相同的基础层，节省磁盘空间。
- **增量构建**：修改一条指令后重新构建时，只重建变更的层及以上的层。
- **分发效率**：拉取镜像时，已存在的层可以直接从本地缓存读取。

**动手验证 7-1：感受镜像分层**

```bash
# 查看镜像的分层历史
docker image history golang:1.22-alpine

# 输出示例（每行是一条指令创建的一层）：
# IMAGE          CREATED BY                                      SIZE
# <missing>      /bin/sh -c #(nop)  CMD ["/bin/sh"]              0B
# <missing>      /bin/sh -c #(nop) ADD file:xxx in /             7.05MB
# ...
```

### 7.2.2 容器（Container）：镜像的运行实例

**容器**是镜像的一个可运行实例。如果把镜像比作类，容器就是 `new` 出来的对象——你可以从一个镜像创建多个相互隔离的容器。Docker 利用 Linux 内核的 **Namespace**（命名空间）和 **Cgroups**（控制组）技术实现容器的隔离与资源限制：

| 机制 | 作用 | 类比 |
|------|------|------|
| **PID Namespace** | 容器内进程拥有独立的进程树，PID=1 是自己的 init 进程 | 每个容器有自己的"进程世界" |
| **Network Namespace** | 容器拥有独立的网络栈（IP、端口、路由） | 每个容器有自己的网卡和 IP |
| **Mount Namespace** | 容器拥有独立的文件系统挂载视图 | 容器"看到"的文件系统是隔离的 |
| **Cgroups** | 限制容器的 CPU、内存、磁盘 I/O 使用量 | 给每个容器设置"资源上限" |

> **注意**：容器不是轻量级虚拟机。虚拟机虚拟整个硬件层，每个 VM 运行独立的内核；而容器共享宿主机的操作系统内核，只隔离用户空间。这使得容器启动只需毫秒级，内存开销极小。

**动手验证 7-2：运行你的第一个容器**

```bash
# 从 alpine 镜像启动一个容器，执行 echo 后自动退出
docker run --rm alpine:3.19 echo "Hello, Hermes Delivery!"
# 输出：Hello, Hermes Delivery!

# 启动一个交互式容器，在容器内查看进程
docker run --rm -it alpine:3.19 sh
/ # ps aux
PID   USER     TIME  COMMAND
    1 root      0:00 sh        # ← 容器内的 PID 1 是 sh，不是宿主机的 init
    7 root      0:00 ps aux
/ # exit
```

### 7.2.3 仓库（Registry）：镜像的分发中心

**仓库**是存储和分发 Docker 镜像的服务。类比 GitHub 是代码的托管平台，**Docker Hub** 就是镜像的托管平台。仓库中的镜像通过**标签（Tag）** 来标识版本：

```
# 镜像引用完整格式
docker.io/library/golang:1.22-alpine
│        │       │      │     │
│        │       │      │     └── 标签（通常是版本号）
│        │       │      └── 镜像名称
│        │       └── 命名空间（用户/组织名，官方镜像用 library）
│        └── 仓库地址（registry hostname）
└── 默认 scheme（HTTPS）
```

**常用操作速查**：

```bash
docker pull nginx:1.25-alpine    # 从 Docker Hub 拉取镜像
docker tag nginx:1.25-alpine myrepo/nginx:v1   # 为镜像打标签
docker push myrepo/nginx:v1      # 推送到私有/公有仓库
docker image ls                  # 列出本地镜像
docker rmi nginx:1.25-alpine     # 删除本地镜像
```

### 7.2.4 Docker 架构总览

```text
┌──────────────┐      REST API       ┌──────────────────┐
│ Docker Client │ ◄─────────────────► │  Docker Daemon    │
│   (docker     │                     │  (dockerd)        │
│    CLI 命令)   │                     │                   │
└──────────────┘                     │  ┌─────────────┐  │
                                     │  │ Container 1  │  │
┌──────────────┐                     │  ├─────────────┤  │
│   Registry    │ ◄──── pull/push ───►  │ Container 2  │  │
│  (Docker Hub) │                     │  ├─────────────┤  │
└──────────────┘                     │  │ Container N  │  │
                                     │  └─────────────┘  │
                                     └──────────────────┘
```

图 7-2 Docker 核心架构（Docker Client / Daemon / Registry）

## 7.3 Dockerfile 编写

Dockerfile 是一个文本文件，包含了一系列构建 Docker 镜像的指令。每条指令创建一个新的镜像层。将 Dockerfile 掌握好比"能运行容器"重要得多——它是"基础设施即代码"思想在构建环节的具体体现。

### 7.3.1 Dockerfile 核心指令

| 指令 | 用途 | 示例 |
|------|------|------|
| `FROM` | 指定基础镜像（必须是第一条指令） | `FROM golang:1.22-alpine` |
| `WORKDIR` | 设置工作目录（后续指令的默认路径） | `WORKDIR /app` |
| `COPY` | 从构建上下文复制文件到镜像 | `COPY . /app` |
| `ADD` | 类似 COPY，但支持 URL 下载和 tar 自动解压 | `ADD https://example.com/file.tar.gz /tmp/` |
| `RUN` | 在构建阶段执行命令（创建新层） | `RUN go build -o /app/server ./cmd/server` |
| `CMD` | 容器启动时默认执行的命令（可被 docker run 参数覆盖） | `CMD ["./server"]` |
| `ENTRYPOINT` | 容器启动时的入口命令（不可被覆盖，但可追加参数） | `ENTRYPOINT ["./server"]` |
| `ENV` | 设置环境变量 | `ENV APP_ENV=production` |
| `EXPOSE` | 声明容器运行时监听的端口（仅文档作用，不实际发布端口） | `EXPOSE 8080` |
| `USER` | 指定运行用户（安全最佳实践：不使用 root） | `USER 1000:1000` |

### 7.3.2 编写 Hermes Delivery 服务的 Dockerfile

回到 Hermes Delivery，我们以订单服务（order-service）为例编写 Dockerfile。order-service 是一个 Go 编写的 HTTP 服务，监听 8080 端口，依赖 PostgreSQL 数据库。

**第一版：直接构建（概念演示）**

```dockerfile
# Dockerfile — 版本 1（简单构建，镜像较大）
FROM golang:1.22-alpine

WORKDIR /app

# 先复制依赖文件，利用 Docker 层缓存加速构建
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码并构建
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/order-service ./cmd/order

# 暴露端口（仅文档作用）
EXPOSE 8080

# 启动服务
CMD ["/app/order-service"]
```

```bash
# 构建镜像
docker build -t hermes/order-service:v1 -f Dockerfile .

# 查看镜像大小
docker image ls hermes/order-service:v1
# REPOSITORY            TAG    IMAGE ID       SIZE
# hermes/order-service  v1     a1b2c3d4e5f6   452MB   ← 注意这个大小！
```

452 MB 对于一个简单的 Go 服务来说太大了。问题在于 `golang:1.22-alpine` 镜像包含了完整的 Go 编译工具链，但运行时我们只需要编译好的二进制文件。这就是**多阶段构建**要解决的问题。

### 7.3.3 多阶段构建（Multi-stage Build）

多阶段构建允许在一个 Dockerfile 中使用多个 `FROM` 语句，每个阶段可以使用不同的基础镜像。前一阶段产生的文件可以被复制到后一阶段，而编译工具链等中间产物则被"丢弃"，最终镜像只包含运行时所需的文件。

```dockerfile
# Dockerfile — 版本 2（多阶段构建，镜像较小）
# ==================== 阶段 1：构建阶段 ====================
FROM golang:1.22-alpine AS builder

WORKDIR /app

# 利用层缓存：先下载依赖
COPY go.mod go.sum ./
RUN go mod download

# 复制源码并编译为静态链接的二进制
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/order-service ./cmd/order

# ==================== 阶段 2：运行阶段 ====================
FROM alpine:3.19

# 安装运行时依赖：CA 证书（HTTPS 请求需要）和时区数据
RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

# 从构建阶段复制编译好的二进制
COPY --from=builder /app/order-service .

# 创建非 root 用户运行服务
RUN adduser -D -u 1000 hermes
USER hermes

EXPOSE 8080

CMD ["./order-service"]
```

```bash
# 重新构建
docker build -t hermes/order-service:v2 -f Dockerfile .

# 对比镜像大小
docker image ls hermes/order-service
# REPOSITORY            TAG    IMAGE ID       SIZE
# hermes/order-service  v1     a1b2c3d4e5f6   452MB
# hermes/order-service  v2     1f2e3d4c5b6a   14.8MB   ← 缩小了 30 倍！
```

**多阶段构建的核心要点**：

| 要点 | 说明 |
|------|------|
| `AS <name>` | 为构建阶段命名，后续可用 `--from=<name>` 引用 |
| `-ldflags="-s -w"` | 去掉调试信息和符号表，减小二进制体积（Go 编译优化） |
| `CGO_ENABLED=0` | 禁用 CGO，编译纯静态链接的二进制（无需 libc） |
| `alpine:3.19` 运行时 | 最小化基础镜像，仅 7 MB，包含 musl libc 和 apk 包管理器 |
| 非 root 用户 | 安全最佳实践，即使容器被攻破，攻击者的权限也受限 |

### 7.3.4 编写最佳实践

以下是教材编写团队根据实际工程经验总结的 Dockerfile 编写实践清单：

**1. 利用层缓存优化构建速度**

```dockerfile
# ✅ 好的写法：不常变的依赖文件先复制
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o /app/server ./cmd/server

# ❌ 坏的写法：每次代码变更都重新下载依赖
COPY . .
RUN go mod download && go build -o /app/server ./cmd/server
```

**2. 合理使用 .dockerignore**

像 `.gitignore` 一样，`.dockerignore` 排除不需要复制到构建上下文的文件，减小构建上下文体积、加速构建。

```text
# .dockerignore — 排除不必要文件
.git
.gitignore
*.md
Dockerfile
docker-compose*.yml
.env
bin/
vendor/     # 如果使用 Go modules，不需要 vendor
```

**3. 减少镜像层数**

将多个 `RUN` 指令合并，减少镜像层数（但不牺牲可读性）：

```dockerfile
# ✅ 好：合并相关操作
RUN apk --no-cache add ca-certificates tzdata \
    && adduser -D -u 1000 hermes \
    && mkdir -p /app/data && chown hermes:hermes /app/data

# ❌ 差：每个命令一层，层数过多
RUN apk --no-cache add ca-certificates
RUN apk --no-cache add tzdata
RUN adduser -D -u 1000 hermes
RUN mkdir -p /app/data
RUN chown hermes:hermes /app/data
```

**4. 使用特定版本的标签**

永远不要在生产中使用 `latest` 标签——它会随着上游推送而变化，导致不可重现的构建：

```dockerfile
# ✅ 好
FROM golang:1.22-alpine
FROM alpine:3.19

# ❌ 差
FROM golang:latest
FROM alpine
```

---

## 7.4 Docker Compose 编排

单个服务的容器化只是第一步。实际项目中，多个服务需要协同工作：order-service 依赖 PostgreSQL，dispatch-service 依赖 Redis，API 网关需要连接所有后端服务。**Docker Compose** 是一个用于定义和运行多容器 Docker 应用的工具——你用一个 YAML 文件描述所有服务的配置，然后一条命令启动整个应用栈。

### 7.4.1 Compose 文件结构

Docker Compose 使用 `docker-compose.yml`（或 `compose.yaml`）文件定义服务。核心概念对应关系：

```text
docker-compose.yml  ←──→  docker run 参数
─────────────────────────────────────────
services:                   docker run
  image:              ←──→  --image
  build:              ←──→  docker build 上下文
  ports:              ←──→  -p
  volumes:            ←──→  -v
  environment:        ←──→  -e
  networks:           ←──→  --network
  depends_on:         ←──→  控制启动顺序
```

### 7.4.2 Hermes Delivery 的 Compose 配置

现在将 Hermes Delivery 的四个服务加上它们依赖的中间件，编写为一个完整的 `docker-compose.yml`。

```yaml
# docker-compose.yml — Hermes Delivery v1
version: "3.9"

services:
  # ────────────────── 基础设施 ──────────────────
  postgres:
    image: postgres:16-alpine
    container_name: hermes-postgres
    environment:
      POSTGRES_DB: hermes
      POSTGRES_USER: hermes
      POSTGRES_PASSWORD: secret123
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hermes -d hermes"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: hermes-redis
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ────────────────── 业务服务 ──────────────────
  order-service:
    build:
      context: ./services/order
      dockerfile: Dockerfile
    container_name: hermes-order
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_USER: hermes
      DB_PASSWORD: secret123
      DB_NAME: hermes
      REDIS_HOST: redis
      REDIS_PORT: "6379"
      APP_PORT: "8080"
    ports:
      - "8081:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  dispatch-service:
    build:
      context: ./services/dispatch
      dockerfile: Dockerfile
    container_name: hermes-dispatch
    environment:
      REDIS_HOST: redis
      REDIS_PORT: "6379"
      APP_PORT: "8080"
    ports:
      - "8082:8080"
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

  courier-service:
    build:
      context: ./services/courier
      dockerfile: Dockerfile
    container_name: hermes-courier
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_USER: hermes
      DB_PASSWORD: secret123
      DB_NAME: hermes
      APP_PORT: "8080"
    ports:
      - "8083:8080"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  api-gateway:
    image: nginx:1.25-alpine
    container_name: hermes-gateway
    ports:
      - "80:80"
    volumes:
      - ./gateway/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - order-service
      - dispatch-service
      - courier-service
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
```

**关键设计说明**：

| 设计决策 | 原因 |
|----------|------|
| `healthcheck` 条件 | `depends_on` 只保证容器启动顺序，`condition: service_healthy` 保证依赖服务**真正就绪**后才启动 |
| 数据卷 `pgdata` / `redisdata` | 数据持久化，容器删除后数据不丢失 |
| 环境变量注入配置 | 代码与配置分离，同一镜像可在不同环境复现 |
| `restart: unless-stopped` | 异常退出自动重启，人工停止不重启 |
| 端口映射差异化 | 宿主机端口 8081-8083 映射到各服务容器内统一的 8080 |

### 7.4.3 网络与数据卷

**网络模型**：Docker Compose 自动为每个项目创建一个独立的网络。以上面的配置为例，所有容器在 `hermes-delivery_default` 网络中可以通过**服务名**互相通信——`order-service` 连接 PostgreSQL 只需要用主机名 `postgres`，无需知道 IP 地址。

```bash
# 启动所有服务
docker compose up -d

# 查看网络
docker network ls | grep hermes
# NETWORK ID     NAME                       DRIVER    SCOPE
# a1b2c3d4e5f6   hermes-delivery_default    bridge    local

# 在容器内通过服务名访问
docker compose exec order-service ping -c 2 postgres
# PING postgres (172.18.0.3): 56 data bytes
# 64 bytes from 172.18.0.3: seq=0 ttl=64 time=0.130 ms

# 查看数据卷
docker volume ls | grep hermes
# DRIVER    VOLUME NAME
# local     hermes-delivery_pgdata
# local     hermes-delivery_redisdata
```

**数据卷 vs 绑定挂载**：

```text
数据卷（volumes:）：         绑定挂载（bind mount: ./dir:/container/dir）
├── Docker 管理               ├── 宿主机路径直接暴露
├── 独立于容器生命周期         ├── 开发时热重载的常用方式
├── 跨平台兼容性好             ├── 路径必须是绝对路径
└── 生产环境推荐              └── 本地开发推荐
```

### 7.4.4 服务依赖管理

`depends_on` 解决了启动顺序，但**不保证服务内部的业务逻辑就绪**。PostgreSQL 容器启动不等于 PostgreSQL 进程已准备好接受连接——这就是我们添加 `healthcheck` 并使用 `condition: service_healthy` 的原因。

> **常见误区**：`depends_on` 只控制 Docker 层面的启动顺序，不检查应用是否就绪。真正的服务间依赖应当结合 **重试机制**（在应用代码中）与 **健康检查**（在 Compose 中）共同保障。

一个更健壮的启动策略是在应用代码中实现数据库重连逻辑：

```go
// internal/database/postgres.go — 带重试的数据库连接
package database

import (
    "database/sql"
    "fmt"
    "log"
    "time"

    _ "github.com/lib/pq"
)

func ConnectWithRetry(dsn string, maxRetries int, backoff time.Duration) (*sql.DB, error) {
    var db *sql.DB
    var err error

    for i := 0; i < maxRetries; i++ {
        db, err = sql.Open("postgres", dsn)
        if err == nil {
            err = db.Ping()
        }
        if err == nil {
            log.Printf("数据库连接成功（尝试 %d/%d）", i+1, maxRetries)
            return db, nil
        }
        log.Printf("数据库连接失败（尝试 %d/%d）: %v，%v 后重试...", i+1, maxRetries, err, backoff)
        time.Sleep(backoff)
    }
    return nil, fmt.Errorf("数据库连接失败，已重试 %d 次: %w", maxRetries, err)
}
```

---

## 7.5 实验：Hermes Delivery 实验环境搭建

本节我们动手将 Hermes Delivery 的实验环境搭建起来。

### 实验目标

在本地使用 Docker Compose 一键启动 Hermes Delivery 全部服务（order-service、dispatch-service、courier-service、api-gateway + PostgreSQL + Redis），并通过 API 网关访问订单服务。

### 实验环境

| 组件 | 版本要求 |
|------|----------|
| Docker Engine | ≥ 24.0 |
| Docker Compose | ≥ v2.20（`docker compose` 子命令） |
| Go（编译服务） | ≥ 1.21（本地可选，Compose 内已包含） |
| 操作系统 | Linux / macOS / Windows (WSL2) |

### 实验步骤

**步骤 1：克隆项目代码**

```bash
git clone https://github.com/nsee-lab/hermes-delivery-lab.git
cd hermes-delivery-lab
git checkout chapter-07
```

**步骤 2：查看项目结构**

```bash
tree -L 3 -I 'vendor|.git'
# .
# ├── docker-compose.yml
# ├── db
# │   └── init.sql              # PostgreSQL 初始化脚本
# ├── gateway
# │   └── nginx.conf            # API 网关配置
# └── services
#     ├── order
#     │   ├── Dockerfile
#     │   ├── cmd/order/main.go
#     │   └── internal/...
#     ├── dispatch
#     │   ├── Dockerfile
#     │   ├── cmd/dispatch/main.go
#     │   └── internal/...
#     └── courier
#         ├── Dockerfile
#         ├── cmd/courier/main.go
#         └── internal/...
```

**步骤 3：一键启动**

```bash
# -d 表示后台运行
docker compose up -d

# 预期输出
# [+] Running 8/8
#  ✔ Network hermes-delivery_default    Created
#  ✔ Volume "hermes-delivery_pgdata"    Created
#  ✔ Volume "hermes-delivery_redisdata" Created
#  ✔ Container hermes-postgres          Healthy
#  ✔ Container hermes-redis             Healthy
#  ✔ Container hermes-order             Started
#  ✔ Container hermes-dispatch          Started
#  ✔ Container hermes-courier           Started
#  ✔ Container hermes-gateway           Started
```

**步骤 4：验证服务**

```bash
# 查看所有容器状态
docker compose ps

# 预期输出
# NAME               IMAGE                  STATUS                    PORTS
# hermes-postgres    postgres:16-alpine     Up (healthy)             0.0.0.0:5432->5432/tcp
# hermes-redis       redis:7-alpine         Up (healthy)             0.0.0.0:6379->6379/tcp
# hermes-order       hermes-order:latest    Up                       0.0.0.0:8081->8080/tcp
# hermes-dispatch    hermes-dispatch:latest Up                       0.0.0.0:8082->8080/tcp
# hermes-courier     hermes-courier:latest  Up                       0.0.0.0:8083->8080/tcp
# hermes-gateway     nginx:1.25-alpine      Up                       0.0.0.0:80->80/tcp

# 通过 API 网关访问订单服务
curl http://localhost/api/v1/orders/health
# {"status":"ok","service":"order-service","version":"1.0.0"}

# 查看日志
docker compose logs -f order-service
```

**步骤 5：查看网络拓扑**

```bash
# Docker Compose 创建的独立网络
docker network inspect hermes-delivery_default
# 可以看到所有容器的 IP 地址和 DNS 别名

# 在容器内验证服务间通信
docker compose exec dispatch-service ping -c 1 order-service
# PING order-service (172.18.0.4): 56 data bytes — 成功！
```

### 实验小结

通过这个实验，你完成了：

1. 将多服务应用定义为一个 `docker-compose.yml` 文件
2. 用一条 `docker compose up -d` 命令启动整个应用栈
3. 验证了容器间可以通过服务名互相通信
4. 通过 API 网关成功访问了后端服务

这些操作在任何安装了 Docker 的机器上都能复现——李明和王磊的环境不一致问题，就此解决。

---

## 本章小结

### 思维导图

```text
容器化基础
├── Docker 核心概念
│   ├── 镜像（Image）— 只读模板，分层存储
│   ├── 容器（Container）— 镜像运行实例，Namespace + Cgroups 隔离
│   └── 仓库（Registry）— 镜像分发中心（Docker Hub）
├── Dockerfile 编写
│   ├── 核心指令：FROM / WORKDIR / COPY / RUN / CMD / ENTRYPOINT / ENV / EXPOSE / USER
│   ├── 多阶段构建：分离编译环境和运行环境，镜像体积缩小 30 倍
│   └── 最佳实践：层缓存 / .dockerignore / 固定版本 / 非 root 用户
├── Docker Compose 编排
│   ├── 单文件定义多服务：docker-compose.yml
│   ├── 自动创建网络：服务名 = DNS 域名
│   ├── 数据卷持久化：volumes / bind mount
│   └── 启动顺序控制：depends_on + healthcheck
└── 实验环境
    └── Hermes Delivery：4 个 Go 服务 + PostgreSQL + Redis + Nginx，一键启动
```

### 关键术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 镜像 | Image | 包含应用及依赖的只读模板，由多层叠加而成 |
| 容器 | Container | 镜像的运行实例，拥有独立的命名空间和资源限制 |
| 仓库 | Registry | 存储和分发 Docker 镜像的服务（如 Docker Hub） |
| 标签 | Tag | 镜像的版本标识符，如 `golang:1.22-alpine` |
| 联合文件系统 | UnionFS | 将多个文件系统层叠加为统一视图的技术 |
| 命名空间 | Namespace | Linux 内核特性，实现进程/网络/文件系统隔离 |
| 控制组 | Cgroups | Linux 内核特性，限制进程组的资源使用 |
| 多阶段构建 | Multi-stage Build | 在一个 Dockerfile 中使用多个 FROM 实现编译与运行分离 |
| 数据卷 | Volume | Docker 管理的持久化存储，独立于容器生命周期 |
| 健康检查 | Healthcheck | 定期检测容器内服务是否就绪的机制 |

---

## 练习

### 基础题（5 题）

**7-1** 以下关于 Docker 镜像的描述，正确的是（ ）

A. 镜像是一个可执行的虚拟磁盘文件，包含完整的操作系统内核
B. 镜像采用分层存储，多个镜像可以共享相同的基础层
C. 镜像一旦构建完成，里面的文件可以被修改
D. Docker 镜像只能从 Docker Hub 拉取

**7-2** Docker 容器通过哪两种 Linux 内核机制实现隔离和资源限制？

**7-3** 请解释 `CMD` 和 `ENTRYPOINT` 的区别，并给出适合使用 `ENTRYPOINT` 的场景。

**7-4** 在 Docker Compose 中，`depends_on` 的作用是什么？它有什么局限性？应该如何弥补？

**7-5** 什么是多阶段构建？使用它构建 Go 服务时，镜像体积能大幅缩小的根本原因是什么？

### 综合题（3 题）

**7-6** 为 Hermes Delivery 的通知服务（notification-service）编写 Dockerfile。该服务是一个 Go 编写的 gRPC 服务，监听 50051 端口，使用多阶段构建并确保运行时使用非 root 用户。写出完整 Dockerfile 并标注每条指令的作用。

**7-7** 某团队在 CI 流水线中频繁构建镜像，每次构建都需 5 分钟以上。检查 Dockerfile 后发现问题：

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci --only=production
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

请指出该 Dockerfile 存在的缓存利用问题，并改写为能有效利用层缓存的版本（假设 `package.json` 和 `package-lock.json` 不常变更，而 `src/` 下的代码频繁变更）。

**7-8** 参考本章的 docker-compose.yml，为 notification-service 添加 Compose 配置。该服务需要连接 Redis（获取推送队列）和 PostgreSQL（存储推送记录），健康检查端点为 `/healthz`，对外暴露端口 50051。

### 拓展题（2 题）

**7-9** 假设 Hermes Delivery 需要在离线环境（无法访问 Docker Hub）部署。请设计一套方案，使镜像分发能在离线环境下完成。需要考虑：(1) 镜像的导出格式；(2) 私有 Registry 的搭建；(3) 基础镜像的预缓存。

**7-10** 当 Hermes Delivery 中的 dispatch-service 需要利用多核 CPU 并行处理大量骑手位置更新时，容器的 Cgroups 资源限制应该如何配置？请结合 `docker run` 的 `--cpus`、`--memory` 参数和 `docker-compose.yml` 中的 `deploy.resources` 说明配置方案，并讨论资源过载时的降级策略。

---

## 常见误区

| 序号 | 错误认知 | 正确理解 |
|:---:|----------|----------|
| 1 | "Docker 就是轻量级虚拟机" | 容器共享宿主机内核，不虚拟化硬件——启动毫秒级，内存开销极小，不能运行不同内核的操作系统 |
| 2 | "`EXPOSE` 指令会发布端口" | `EXPOSE` 仅作为文档标注，不实际映射端口到宿主机；真正发布端口需要 `-p` 参数或 Compose 中的 `ports:` |
| 3 | "`depends_on` 保证数据库已就绪" | `depends_on` 只控制容器启动顺序，不等数据库进程 ready。应使用 `healthcheck` + `condition: service_healthy` |
| 4 | "`latest` 标签很方便，生产环境也用" | 使用 `latest` 意味着每次拉取可能得到不同版本，构建不可复现；生产环境必须使用固定版本标签 |
| 5 | "容器退出后数据就丢失了" | 只有容器读写层的数据丢失；挂载到数据卷（Volumes）或绑定目录的数据在容器删除后仍然保留 |
| 6 | "Dockerfile 中 `RUN` 指令越多越清晰" | 每条 `RUN` 创建一个新镜像层；相关命令应合并以减少层数，但不牺牲可读性 |

---

> **下一章预告**：有了容器化的基础，第 8 章将进入 Kubernetes 的世界——当 Hermes Delivery 需要多副本运行、滚动更新、自动扩缩容时，Docker Compose 已力不从心，Kubernetes 将接过编排的接力棒。
