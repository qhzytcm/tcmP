# 第10章 可观测性

> **学习目标**
>
> - **知识**：理解可观测性三大支柱（日志、指标、链路追踪）的核心概念及相互关系；了解 ELK、Prometheus、Jaeger 在可观测性体系中的角色
> - **能力**：能使用结构化日志库为 Go 服务添加日志；能用 Prometheus client 暴露业务指标并用 Grafana 可视化；能用 OpenTelemetry 为跨服务调用注入链路追踪
> - **素养**：建立"先观测、后优化"的运维思维，养成在编写业务代码时同步埋入观测数据的工作习惯

---

## 10.1 情境导入：Hermes Delivery 的"失明"时刻

凌晨两点，张工被手机震动吵醒。运维群里几十条消息——十几位用户在投诉："快递查不到位置了""App 一直转圈"。张工打开电脑，SSH 连上服务器，面对十几个微服务进程，脑子里只有一个问题：

**"到底哪个服务出了问题？"**

他看着终端上的系统负载和进程列表，这些信息只能告诉他 CPU 和内存没打满，但不能回答最关键的问题：

- 是订单服务挂了，还是调度服务卡住了？
- 哪个 API 接口的错误率飙升？
- 请求到底卡在哪一步？

这就是一个**"失明"的分布式系统**——服务在运行，但你完全看不见它内部在发生什么。

如果 Hermes Delivery 在每个服务中都埋入了结构化日志、关键指标和分布式追踪，张工只需要打开 Grafana 看一眼仪表盘，就能立刻定位到调度服务的 P99 延迟从 200ms 飙到了 30s，再用 Jaeger 点开一条慢请求的追踪链，发现是调用第三方地图 API 时超时了。

**可观测性不是锦上添花，而是分布式系统的"视力"。**

---

## 10.2 什么是可观测性

### 10.2.1 监控 ≠ 可观测性

我们先厘清两个容易混淆的概念：

| | **监控（Monitoring）** | **可观测性（Observability）** |
|---|---|---|
| 核心问题 | "系统是否正常？" | "系统为什么这样？" |
| 依赖条件 | 已知的故障模式 | 未知的故障模式 |
| 信息特征 | 预定义指标和告警规则 | 丰富的上下文数据 |
| 典型工具 | Nagios, Zabbix | ELK, Prometheus, Jaeger |

> 简单类比：监控就像汽车仪表盘（油量、水温、速度），它能告诉你车是否在正常范围。可观测性则像一架飞机的"黑匣子"，出事之后你能通过飞行数据**反推**出事故原因。

在微服务架构中，一个用户请求可能触发十几个服务间的调用链。你不可能预先知道所有可能的故障模式——因此你需要的是**足够的观测数据，让未知问题也能被追溯**。

### 10.2.2 三大支柱：Logs / Metrics / Traces

现代可观测性体系围绕三种信号类型构建：

```
┌─────────────────────────────────────────────────────────┐
│                    可观测性三大支柱                         │
├───────────────┬───────────────────┬─────────────────────┤
│   日志(Logs)   │   指标(Metrics)    │  链路追踪(Tracing)   │
├───────────────┼───────────────────┼─────────────────────┤
│ 发生了什么？    │ 量有多大？多久？   │ 在哪一步？为什么？    │
│ 离散事件记录    │ 连续时间序列聚合   │ 请求级因果链         │
│ "订单#2301      │ "P99延迟=320ms"   │ "order→dispatch→    │
│  支付超时"     │                  │  map→payment"       │
├───────────────┼───────────────────┼─────────────────────┤
│ 存储: ES/Loki  │ 存储: Prometheus  │ 存储: Jaeger/Tempo  │
│ 体积: 大       │ 体积: 中          │ 体积: 较小(采样后)   │
│ 查询: 关键词    │ 查询: PromQL      │ 查询: TraceID精确   │
└───────────────┴───────────────────┴─────────────────────┘
```

这三者不是竞争关系，而是**互补关系**。实战中的排查路径通常是：

> **指标告警 → 追踪定位 → 日志确认**

即：Grafana 仪表盘发现延迟飙升 → Jaeger 找到具体哪条 Trace 慢 → Kibana 查看该请求的详细日志上下文。

### 10.2.3 MELT 模型

业界有时用 **MELT** 这个缩写来概括可观测性的四个维度：

- **M**etrics（指标）
- **E**vents（事件日志）
- **L**ogs（日志）
- **T**races（追踪）

其中 Events 是日志的特殊形式（如部署事件、配置变更），实践中通常并入 Logs 讨论。本书沿用"三大支柱"的主流分类。

---

## 10.3 日志（Logging）：系统行为的"日记本"

### 10.3.1 结构化日志

传统日志是人读的：

```
2024-03-15 02:14:23 ERROR order-service: order creation failed for user=10023
```

结构化日志是**机器优先可读**的：

```json
{
  "timestamp": "2024-03-15T02:14:23.456Z",
  "level": "error",
  "service": "order-service",
  "message": "order creation failed",
  "user_id": 10023,
  "order_id": "ORD-2301",
  "error": "payment gateway timeout",
  "latency_ms": 3200
}
```

结构化日志的核心优势是**可查询**。当你把所有服务的日志集中到 Elasticsearch 中，就可以用类似 SQL 的查询语言做这样的操作：

```
level:error AND service:order-service AND latency_ms:>3000
```

### 10.3.2 Go 实战：使用 zap 输出结构化日志

zap 是 Uber 开源的高性能 Go 结构化日志库，是 Go 微服务的事实标准之一。下面展示在 Hermes Delivery 的订单服务中如何使用它：

```go
// order-service/internal/logging/logger.go
package logging

import (
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

// NewLogger 创建一个生产环境可用的结构化日志器
func NewLogger(serviceName string) (*zap.Logger, error) {
    config := zap.NewProductionConfig()
    config.EncoderConfig.TimeKey = "timestamp"
    config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
    config.InitialFields = map[string]interface{}{
        "service": serviceName,
    }
    return config.Build()
}
```

```go
// 在业务代码中使用
func (s *OrderService) CreateOrder(ctx context.Context, req *CreateOrderReq) (*Order, error) {
    logger := zap.L().With(
        zap.String("user_id", req.UserID),
        zap.String("trace_id", traceIDFromContext(ctx)), // 与链路追踪关联的关键
    )

    logger.Info("creating order",
        zap.String("pickup", req.PickupAddr),
        zap.String("delivery", req.DeliveryAddr),
    )

    order, err := s.repo.Insert(ctx, req)
    if err != nil {
        logger.Error("order creation failed",
            zap.Error(err),
            zap.Duration("elapsed", time.Since(start)),
        )
        return nil, err
    }

    logger.Info("order created",
        zap.String("order_id", order.ID),
        zap.Duration("elapsed", time.Since(start)),
    )
    return order, nil
}
```

> **要点**：注意 `trace_id` 字段。将 Trace ID 注入每条日志是连接 Logs 和 Traces 的**关键桥梁**——你能从 Jaeger 中的一条 Trace 直接跳转到 Kibana 的相关日志。

### 10.3.3 ELK Stack 概览

ELK 是 Elasticsearch、Logstash、Kibana 三者的缩写，是日志收集、存储、查询的经典方案：

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  微服务容器    │──→  │  Filebeat     │──→  │  Logstash    │──→  │Elasticsearch │
│  (日志文件/stdout)│  │(轻量级采集器)  │     │(日志处理管道)  │     │  (存储+索引)  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                      │
                                                                      ▼
                                                               ┌──────────────┐
                                                               │   Kibana     │
                                                               │(可视化+查询)   │
                                                               └──────────────┘
```

**各组件职责**：

- **Filebeat**：部署在每个节点上，轻量级日志采集器，读取容器 stdout 或日志文件，转发给 Logstash
- **Logstash**：日志处理管道，负责解析、过滤、转换日志格式
- **Elasticsearch**：分布式搜索和分析引擎，存储索引后的日志数据
- **Kibana**：Web 可视化界面，提供搜索、仪表盘、告警功能

对于中小规模项目，也可以用更轻量的 **Grafana Loki** 替代 ELK。Loki 的设计哲学是"像 Prometheus 一样便宜，像 Kibana 一样可搜"，不需要维护庞大的 ES 集群。

---

## 10.4 指标（Metrics）：系统健康的"体温计"

### 10.4.1 指标类型

Prometheus 定义了四种核心指标类型，覆盖了大多数监控场景：

| 类型 | 含义 | 示例 | 特点 |
|------|------|------|------|
| **Counter** | 只增不减的计数 | HTTP 请求总数、订单创建总数 | 重启归零，用 `rate()` 看变化速率 |
| **Gauge** | 可增可减的瞬时值 | 当前内存使用、活跃连接数 | 适合状态快照 |
| **Histogram** | 分桶统计分布 | 请求延迟分布（0-10ms, 10-50ms, 50-100ms...） | 可算百分位数（P50/P90/P99） |
| **Summary** | 客户端计算分位数 | 请求延迟的 P50/P99 | 比 Histogram 精确但不可聚合 |

### 10.4.2 Prometheus 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Prometheus 生态                           │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │order-svc │  │dispatch  │  │notify    │  ← 被监控服务暴露       │
│  │:8080     │  │:8081     │  │:8082     │    /metrics 端点      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │             │             │                              │
│       │    pull (每15s采集一次)     │                              │
│       ▼             ▼             ▼                              │
│  ┌─────────────────────────────────────┐                        │
│  │          Prometheus Server          │  ← 时序数据库 + 告警引擎 │
│  │   (抓取 → 存储 → 规则评估 → 告警)    │                        │
│  └──────────┬──────────────────────────┘                        │
│             │                                                     │
│             │  PromQL 查询                                        │
│             ▼                                                     │
│  ┌──────────────────┐   ┌──────────────────┐                    │
│  │    Grafana       │   │  AlertManager     │                    │
│  │  (仪表盘可视化)    │   │ (告警去重/分组/路由) │                    │
│  └──────────────────┘   └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

Prometheus 的核心理念是 **Pull 模型**：它主动向每个服务拉取指标数据，而不是等服务推送。这带来了一个优势——如果某个服务的 `/metrics` 端点挂了，Prometheus 能立刻发现。

### 10.4.3 Go 实战：为 Hermes Delivery 添加业务指标

```go
// order-service/internal/metrics/metrics.go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // Counter: 订单创建总数（按状态分组）
    OrdersCreated = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "hermes_orders_created_total",
            Help: "Total number of orders created.",
        },
        []string{"status"}, // 标签: success / failed
    )

    // Histogram: 订单创建延迟分布
    OrderCreationDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "hermes_order_creation_duration_seconds",
            Help:    "Duration of order creation in seconds.",
            Buckets: prometheus.DefBuckets, // 默认: .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10
        },
        []string{"method"}, // 标签: api / mq
    )

    // Gauge: 当前待处理的订单数
    PendingOrders = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "hermes_pending_orders",
            Help: "Current number of pending orders.",
        },
    )
)
```

```go
// 在业务代码中埋点
func (s *OrderService) CreateOrder(ctx context.Context, req *CreateOrderReq) (*Order, error) {
    timer := prometheus.NewTimer(prometheus.ObserverFunc(func(f float64) {
        metrics.OrderCreationDuration.WithLabelValues("api").Observe(f)
    }))
    defer timer.ObserveDuration()

    order, err := s.repo.Insert(ctx, req)
    if err != nil {
        metrics.OrdersCreated.WithLabelValues("failed").Inc()
        return nil, err
    }

    metrics.OrdersCreated.WithLabelValues("success").Inc()
    metrics.PendingOrders.Inc()
    return order, nil
}
```

> **Grafana 查询示例**：在 Grafana 面板中输入 PromQL：
> ```
> rate(hermes_orders_created_total{status="failed"}[5m])  # 过去5分钟每秒失败订单数
> histogram_quantile(0.99, rate(hermes_order_creation_duration_seconds_bucket[5m]))  # P99延迟
> ```

### 10.4.4 RED 与 USE 方法

面对几十个微服务，你不可能给每个服务建一百个仪表盘。业界推荐用两种方法论来聚焦关键指标：

- **RED 方法**（面向请求驱动型服务）：
  - **R**ate（请求速率）：每秒接收多少请求？
  - **E**rrors（错误率）：多少比例的请求失败了？
  - **D**uration（延迟）：P99 请求处理时间是多少？

- **USE 方法**（面向资源型组件，如数据库、缓存）：
  - **U**tilization（利用率）：资源使用百分比
  - **S**aturation（饱和度）：等待队列的长度
  - **E**rrors（错误数）：操作失败次数

Hermes Delivery 中的订单服务（请求驱动型）用 RED，MySQL 数据库（资源型）用 USE，各取所需。

---

## 10.5 链路追踪（Tracing）：跨服务调用的"行车记录仪"

### 10.5.1 为什么需要分布式追踪

考虑 Hermes Delivery 的"用户下单"流程：

```
用户点击下单 → API网关 → 订单服务 → 调度服务 → 地图服务 → 通知服务
                                     ↳ 支付服务
```

一个请求跨越 6 个服务。如果整个流程耗时 3 秒，你怎么知道是哪个环节慢了？是订单服务的数据库写入，还是地图服务的 API 调用，还是支付服务的网络延迟？

**分布式追踪**就是在请求入口处生成一个全局唯一的 `TraceID`，并让它在每次跨服务调用时像接力棒一样传递下去。每个服务处理阶段记录为一个 **Span**，所有 Span 组成一条完整的 **Trace**。

### 10.5.2 核心概念

```
 Trace: ┌────────────────────────────────────────────────────────────────┐
        │                                                                │
        │  Span A (API Gateway)  [0ms ──────────────────────── 3200ms]  │
        │    │                                                           │
        │    ├── Span B (Order Service)  [15ms ────── 2800ms]           │
        │    │     │                                                     │
        │    │     ├── Span C (MySQL INSERT)  [30ms ── 120ms]           │
        │    │     │                                                     │
        │    │     └── Span D (Dispatch Service)  [150ms ── 2700ms]     │
        │    │           │                                               │
        │    │           └── Span E (Map API HTTP GET)  [200ms ─ 2600ms]│
        │    │                                                           │
        │    └── Span F (Notification)  [2850ms ── 3150ms]              │
        │                                                                │
        └────────────────────────────────────────────────────────────────┘
```

- **Trace**：一条完整的请求链路，由 TraceID 唯一标识
- **Span**：链路中的一个操作单元，拥有 SpanID、操作名、起止时间戳、标签（Tags）和日志事件（Events）
- **SpanContext**：在进程间传递的上下文信息，包含 TraceID 和当前 SpanID
- **传播（Propagation）**：将 SpanContext 注入 HTTP Header / gRPC Metadata，让下游服务接收到

### 10.5.3 Jaeger 架构

Jaeger 是 Uber 开源的分布式追踪系统，2017 年捐赠给 CNCF 并毕业。其架构如下：

```
┌───────────────────────────────────────────────┐
│                Jaeger 架构                     │
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │order-svc │  │dispatch  │  │notify    │    │
│  │(Jaeger   │  │client)   │  │          │    │
│  │ client)  │  │          │  │          │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │          │
│       │  Span数据    │             │          │
│       ▼             ▼             ▼          │
│  ┌──────────────────────────────────────┐    │
│  │         Jaeger Collector            │    │
│  │   (接收 → 验证 → 入队 → 写入存储)    │    │
│  └──────────────┬───────────────────────┘    │
│                 │                             │
│                 ▼                             │
│  ┌──────────────────────────┐                │
│  │   Storage Backend        │                │
│  │ (Elasticsearch/Cassandra)│                │
│  └──────────┬───────────────┘                │
│             │                                 │
│             ▼                                 │
│  ┌──────────────────────────┐                │
│  │    Jaeger Query + UI     │                │
│  │    (搜索/可视化/依赖图)    │                │
│  └──────────────────────────┘                │
└───────────────────────────────────────────────┘
```

### 10.5.4 Go 实战：使用 OpenTelemetry 统一追踪

OpenTelemetry（简称 OTel）是 CNCF 的标准化可观测性框架，将 Metrics、Logs、Traces 统一到一个 SDK 中。在 Go 微服务中使用 OTel + Jaeger 的典型模式如下：

```go
// 初始化 TracerProvider（通常在 main.go 中）
package main

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

func initTracer(serviceName string) (*sdktrace.TracerProvider, error) {
    // 通过 OTLP 协议将 Span 发送到 Jaeger Collector（gRPC 端口 4317）
    exporter, err := otlptracegrpc.New(context.Background(),
        otlptracegrpc.WithEndpoint("jaeger-collector:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceName(serviceName),
        )),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}
```

```go
// 在 HTTP Handler 中使用
func (h *OrderHandler) CreateOrder(w http.ResponseWriter, r *http.Request) {
    // 从请求头提取 Trace Context（W3C TraceContext 标准）
    ctx := otel.GetTextMapPropagator().Extract(r.Context(),
        propagation.HeaderCarrier(r.Header),
    )

    tracer := otel.Tracer("order-service")
    ctx, span := tracer.Start(ctx, "OrderHandler.CreateOrder")
    defer span.End()

    // 添加 Span 属性，便于在 Jaeger 中搜索
    span.SetAttributes(
        attribute.String("user.id", userIDFromRequest(r)),
        attribute.String("order.type", "express"),
    )

    // 业务逻辑，ctx 中携带了 SpanContext
    order, err := h.service.CreateOrder(ctx, req)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        http.Error(w, err.Error(), 500)
        return
    }
    span.SetStatus(codes.Ok, "order created")
    json.NewEncoder(w).Encode(order)
}
```

### 10.5.5 采样策略

全量追踪在流量高峰期非常昂贵（可能消耗数 GB/s 的存储写入）。生产环境通常采用**采样**：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **头部采样** (Head-based) | 在 Trace 开始时决定是否采样 | 简单，但可能丢失有意义的慢请求 |
| **尾部采样** (Tail-based) | 缓存一段时间，根据完整结果决定 | 保留所有错误/慢请求，准确但复杂 |
| **自适应采样** | 根据流量动态调整采样率 | 生产环境推荐（Jaeger 的 Adaptive Sampling） |

> **实战建议**：在 Jaeger Collector 中启用尾部采样，配置规则为"错误 Trace 全保留、耗时 > 1s 全保留、正常请求 10% 采样"。

---

## 10.6 Hermes Delivery 可观测性方案

### 10.6.1 整体架构

将前三节的内容整合起来，Hermes Delivery 的可观测性架构如下：

```
┌────────────────────────────────────────────────────────────────────────┐
│                  Hermes Delivery 可观测性全景架构                        │
│                                                                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐          │
│  │API Gateway│  │Order Svc  │  │Dispatch   │  │Notify Svc │          │
│  │           │  │           │  │Svc        │  │           │          │
│  │ ┌───────┐ │  │ ┌───────┐ │  │ ┌───────┐ │  │ ┌───────┐ │          │
│  │ │ zap   │ │  │ │ zap   │ │  │ │ zap   │ │  │ │ zap   │ │          │
│  │ │ OTel  │ │  │ │ OTel  │ │  │ │ OTel  │ │  │ │ OTel  │ │          │
│  │ │Prom cl│ │  │ │Prom cl│ │  │ │Prom cl│ │  │ │Prom cl│ │          │
│  │ └──┬──┬─┘ │  │ └──┬──┬─┘ │  │ └──┬──┬─┘ │  │ └──┬──┬─┘ │          │
│  └────┼──┼───┘  └────┼──┼───┘  └────┼──┼───┘  └────┼──┼───┘          │
│       │  │           │  │           │  │           │  │              │
│  ─────┼──┼───────────┼──┼───────────┼──┼───────────┼──┼── 数据流     │
│       │  │           │  │           │  │           │  │              │
│       ▼  │           ▼  │           ▼  │           ▼  │              │
│  ┌───────┴┐      ┌───────┴┐      ┌───────┴┐      ┌───────┴┐         │
│  │Filebeat│      │Filebeat│      │Filebeat│      │Filebeat│         │
│  └───┬────┘      └───┬────┘      └───┬────┘      └───┬────┘         │
│      │               │               │               │              │
│      ▼               ▼               ▼               ▼              │
│  ┌──────────────────────────────────────────────────────┐           │
│  │              Elasticsearch (日志存储)                  │           │
│  └──────┬───────────────────────────────────────────────┘           │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────┐                                                        │
│  │ Kibana   │  ← 日志查询与分析                                       │
│  └──────────┘                                                        │
│                                                                      │
│       │ (Prometheus /metrics 端点采集)                                │
│       ▼                                                              │
│  ┌──────────────┐   ┌──────────────┐                                 │
│  │ Prometheus   │──→│ AlertManager │  ← 告警通知（企业微信/邮件）       │
│  └──────┬───────┘   └──────────────┘                                 │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────┐                                                        │
│  │ Grafana  │  ← 仪表盘（RED 仪表盘 + 业务大盘）                       │
│  └──────────┘                                                        │
│                                                                      │
│       │ (OTel gRPC 推送 Span)                                        │
│       ▼                                                              │
│  ┌───────────────┐                                                   │
│  │Jaeger Collector│                                                  │
│  └───────┬───────┘                                                   │
│          │                                                           │
│          ▼                                                           │
│  ┌──────────────┐                                                    │
│  │Jaeger UI     │  ← 链路查询 + 服务依赖拓扑图                         │
│  └──────────────┘                                                    │
└────────────────────────────────────────────────────────────────────────┘
```

### 10.6.2 关键业务指标设计

Hermes Delivery 作为一个快递调度系统，除了通用的 RED 指标外，还需要定义业务专有的观测维度：

```go
// 调度服务的关键业务指标
var (
    // 调度成功率：成功匹配骑手的订单比例
    DispatchSuccessRate = promauto.NewGauge(prometheus.GaugeOpts{
        Name: "hermes_dispatch_success_rate",
        Help: "Percentage of orders successfully dispatched to a rider.",
    })

    // 骑手在线数：实时反映运力
    RidersOnline = promauto.NewGauge(prometheus.GaugeOpts{
        Name: "hermes_riders_online",
        Help: "Current number of riders online and accepting orders.",
    })

    // 订单堆积深度：调度队列中等待处理的订单数
    DispatchQueueDepth = promauto.NewGauge(prometheus.GaugeOpts{
        Name: "hermes_dispatch_queue_depth",
        Help: "Number of orders waiting in the dispatch queue.",
    })
)
```

> **设计原则**：业务指标应该直接回答运营团队真正关心的问题——"现在有多少单待分配？""骑手够不够？""有多少订单分配失败了？"

### 10.6.3 Docker Compose 一键部署（实验环境）

对于教学和开发环境，可以用 Docker Compose 一键拉起整个可观测性栈：

```yaml
# observability/docker-compose.yml
version: '3.8'
services:
  # 日志: Elasticsearch + Kibana
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"

  # 指标: Prometheus
  prometheus:
    image: prom/prometheus:v2.50.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.3.0
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"

  # 追踪: Jaeger
  jaeger-collector:
    image: jaegertracing/jaeger-collector:1.53
    environment:
      - SPAN_STORAGE_TYPE=badger
      - BADGER_EPHEMERAL=false
      - BADGER_DIRECTORY_VALUE=/badger/data
      - BADGER_DIRECTORY_KEY=/badger/key
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "14250:14250"

  jaeger-query:
    image: jaegertracing/jaeger-query:1.53
    environment:
      - SPAN_STORAGE_TYPE=badger
      - BADGER_EPHEMERAL=false
      - BADGER_DIRECTORY_VALUE=/badger/data
      - BADGER_DIRECTORY_KEY=/badger/key
    ports:
      - "16686:16686"  # Jaeger UI
```

---

## 10.7 常见误区

### 误区一："日志打多了影响性能，所以尽量少打"

**纠正**：结构化日志的性能开销主要来自 I/O，现代日志库（zap、zerolog）都采用异步写入 + 缓冲批处理，写入开销通常是亚毫秒级。**真正拖慢系统的是在日志中做同步的字符串拼接**。正确的做法是：

- 使用延迟求值的字段（zap 的 `zap.Duration("elapsed", time.Since(start))` 比 `fmt.Sprintf` 先构造字符串再传入高效得多）
- 当日志量巨大时，使用采样（如 zap 的 `SamplingConfig`，每 N 条相同的日志只记录一条 + 计数）
- 异步写入 + 按大小/时间滚动切割

### 误区二："Prometheus 的 Histogram 和 Summary 选哪个都行"

**纠正**：这是一个经典陷阱。核心区别在于**分位数计算的时机和地点**：

- **Histogram**：原始桶计数存储在 Prometheus 服务端，`histogram_quantile()` 在查询时聚合多个实例的桶数据后再计算分位数。这让你可以跨实例计算全局 P99，**适合水平扩展的微服务**。
- **Summary**：分位数在客户端本地计算，Prometheus 只拿到最终结果。这意味着你无法跨实例聚合——两个实例各自 P99=200ms，不代表全局 P99=200ms。**适合单实例或不需要跨实例聚合的场景**。

> 结论：绝大多数微服务场景用 **Histogram**。

### 误区三："有了 ELK + Prometheus + Jaeger，可观测性就完成了"

**纠正**：工具只是手段，不是终点。真正的可观测性需要：

1. **统一的上下文传播**：日志、指标、追踪之间必须通过 TraceID 关联，才能形成排查闭环
2. **告警分级与值班制度**：告警无休止地轰炸 = 没人看告警。需要设置明确的 P0/P1/P2 分级和 on-call 轮值
3. **事后复盘文化**：每次线上事故后必须回答——"这个问题的信号是否在出事前就已存在于我们的观测数据中？如果没有，该补什么指标/日志？"

### 误区四："OpenTelemetry 自动埋点就够了，不需要手动 Span"

**纠正**：自动埋点（Auto-instrumentation）能覆盖 HTTP/gRPC/数据库的入口和出口调用，但**不知道你的业务逻辑边界**。例如：

```go
func (s *DispatchService) AssignRider(orderID string) error {
    // ← OTel 不知道这段逻辑是一个"有意义的操作单元"
    riders := s.filterByLocation(orderID)
    best := s.selectBestRider(riders)
    if err := s.notifyRider(best, orderID); err != nil {
        return err
    }
    return nil
}
```

如果没有手动创建 `AssignRider` 这个 Span，Jaeger 中你只能看到一堆底层 RPC 调用，而看不到"订单调度"这个业务操作耗时多少。**自动埋点告诉你骨架，手动埋点才赋予血肉。**

---

## 10.8 本章小结

本章从 Hermes Delivery 线上故障排查的真实场景出发，系统地讲解了可观测性的三大支柱：

```
                    可观测性三大支柱
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      日志(Logs)      指标(Metrics)   链路追踪(Traces)
     "发生了什么"    "量有多大/多快"   "在哪一步/为什么"
          │               │               │
          ▼               ▼               ▼
      ELK Stack      Prometheus        Jaeger
    (ES+Logstash    + Grafana       (OTel SDK +
    +Kibana)        +AlertManager)    Collector)
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
              统一关联: TraceID 贯穿日志+追踪
              排查闭环: 指标告警 → 追踪定位 → 日志确认
```

### 关键术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 可观测性 | Observability | 通过系统输出的外部数据推断其内部状态的能力 |
| 结构化日志 | Structured Logging | 以 JSON 等键值对格式输出日志，便于机器解析和搜索 |
| 指标 | Metrics | 时间序列化的数值数据，描述系统在某维度的度量 |
| 链路追踪 | Distributed Tracing | 追踪一个请求在多个服务间的完整调用路径 |
| TraceID | Trace ID | 全链路唯一的标识符，贯穿所有 Span |
| Span | Span | 链路中的一个操作单元，记录起止时间和元数据 |
| OpenTelemetry | OTel | CNCF 可观测性标准框架，统一 SDK 覆盖三类信号 |
| PromQL | Prometheus Query Language | Prometheus 的查询语言，用于计算聚合指标 |
| RED 方法 | RED Method | 面向服务的监控方法：Rate / Errors / Duration |
| USE 方法 | USE Method | 面向资源的监控方法：Utilization / Saturation / Errors |
| ELK | Elasticsearch, Logstash, Kibana | 经典的集中式日志方案 |
| OTLP | OpenTelemetry Protocol | OTel 定义的数据传输协议 |

---

## 练习

### 基础题

1. **概念辨析**：简述日志（Logs）、指标（Metrics）、链路追踪（Traces）三者的核心区别，并说明在实际排错中三者的协作关系。

2. **工具匹配**：以下场景分别最适合使用哪种可观测性工具？请连线并说明理由。
   - (a) 想知道过去 1 小时订单服务的 P99 延迟变化趋势
   - (b) 用户投诉某订单状态异常，需要查看该订单完整的服务调用链
   - (c) 需要在凌晨 2:00 到 2:05 之间搜索所有包含 "timeout" 关键字的错误日志
   - 可选工具：Prometheus + Grafana / Jaeger / ELK (Kibana)

3. **代码填空**：补全以下 Prometheus Counter 的定义代码，使其能按 `status` 标签分别统计成功和失败的订单数。

```go
OrdersTotal = promauto.NewCounterVec(
    prometheus.CounterOpts{
        Name: "hermes_orders_total",
        Help: "________________",
    },
    []string{"______"},
)
```

4. **指标类型选择**：在 Hermes Delivery 中，以下场景分别该用哪种 Prometheus 指标类型（Counter / Gauge / Histogram）？
   - (a) 当前在线的骑手数量
   - (b) 订单创建的总次数
   - (c) 订单处理耗时的分布

5. **架构判断**：判断正误并说明理由——"Prometheus 采用 Push 模型采集指标数据，各服务主动推送指标到 Prometheus Server。"

### 综合题

6. **方案设计**：假设 Hermes Delivery 新增了一个"运费计算服务"，请为其设计一套完整的可观测性方案，包括：
   - 至少 3 个业务指标的定义
   - 关键 Span 的设计
   - 日志中应记录的字段

7. **故障模拟**：在本地 Docker Compose 环境中（10.6.3 节配置），模拟以下故障并写出排查步骤：
   - 场景：订单服务调用调度服务超时
   - 要求：说明如何从 Grafana → Jaeger → Kibana 逐步缩小问题范围

8. **代码实现**：为 10.4.3 节中的订单服务编写一个 Gin/标准库 HTTP 中间件，自动为每个请求记录以下指标：
   - 请求总数（按 HTTP 方法和路径分组）
   - 请求延迟分布（Histogram）
   - 在响应状态码为 5xx 时增加错误计数

### 拓展题

9. **技术调研**：OpenTelemetry 作为 CNCF 的标准化框架，正在逐步统一日志、指标、追踪的 SDK。请调研 OTel 的日志信号（Logs Signal）现状，撰写一份 500 字的技术简报，说明其与 ELK 方案的差异和互补关系。

10. **架构演进**：Hermes Delivery 当前的可观测性架构中，日志存储使用 Elasticsearch。随着业务增长，ES 集群的存储和查询成本显著上升。请调研 Grafana Loki 作为替代方案的可行性，从成本、查询能力、与 Prometheus 的协同三个维度进行分析，撰写不超过 800 字的技术评估报告。
