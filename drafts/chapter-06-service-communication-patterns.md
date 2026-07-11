# 第6章 服务通信模式综合

> **所属篇章**：第二篇 · 服务间通信  
> **前置章节**：第4章（同步通信：REST 与 gRPC）、第5章（异步通信：消息与事件）  
> **建议学时**：3 学时（理论 2 + 讨论/实操 1）  
> **贯穿案例**：Hermes Delivery 快递调度系统

---

## 6.0 学习目标

| 层次 | 目标 |
|------|------|
| **知识目标** | 理解编配（Choreography）与编排（Orchestration）两种服务协调模式的核心区别；掌握 Saga 分布式事务的两类实现方式；理解最终一致性的工程含义 |
| **能力目标** | 能根据业务场景选择合适的服务协调模式；能设计基于事件的 Saga 补偿流程；能用 Go 语言实现一个简化的 Saga 编排器 |
| **素养目标** | 建立"分布式系统没有免费的一致性"的工程直觉；培养在一致性、可用性与复杂度之间做权衡的决策能力 |

---

## 6.1 情境导入：一笔快递订单的旅程

> **Hermes Delivery 场景**  
> 用户小张在 Hermes Delivery 平台下单寄送一个包裹。系统需要完成以下步骤：
> 1. 创建订单（Order Service）
> 2. 冻结用户余额（Payment Service）  
> 3. 分配快递员（Dispatch Service）
> 4. 通知用户和快递员（Notification Service）
>
> 四个步骤涉及四个独立的微服务。问题来了：**谁来协调这些步骤的执行顺序？如果第3步分配快递员失败了，如何回滚前两步？**

这正是本章要解决的核心问题。在第4章和第5章中，我们分别学习了同步通信（REST/gRPC）和异步通信（消息队列/事件）。但在真实业务中，一个业务流程往往跨越多个服务——此时仅靠"发一个请求"或"发一条消息"是不够的，我们还需要**协调逻辑**。

---

## 6.2 服务协调的两种哲学：编配与编排

当一个业务流程跨越多个服务时，有两种根本不同的协调思路。Chris Richardson 在 *Microservices Patterns* 中将它们命名为 **Choreography（编配）** 和 **Orchestration（编排）**。

### 6.2.1 编配（Choreography）：去中心化的舞蹈

想象一场即兴舞蹈：没有指挥，每位舞者根据音乐和前一位舞者的动作做出反应。在微服务世界中，编配模式就是这样工作的——

**核心思想**：每个服务在完成自己的任务后，发布一个事件。其他关心这个事件的服务自行响应。没有一个"中央指挥官"。

```
┌──────────┐   OrderCreated    ┌──────────┐
│  Order   │ ────事件────→     │ Payment  │
│ Service  │                   │ Service  │
└──────────┘                   └────┬─────┘
                                    │ PaymentAuthorized
                                    ▼
                              ┌──────────┐
                              │ Dispatch │
                              │ Service  │
                              └────┬─────┘
                                   │ CourierAssigned
                                   ▼
                              ┌──────────────┐
                              │ Notification │
                              │   Service    │
                              └──────────────┘
```

**Go 代码示意（编配模式下的 Order Service）**：

```go
// order/service.go
// 演示版本：Go 1.21+, 使用 Watermill 消息库 (github.com/ThreeDotsLabs/watermill)

package order

import (
    "encoding/json"
    "github.com/ThreeDotsLabs/watermill/message"
)

type OrderCreatedEvent struct {
    OrderID   string  `json:"order_id"`
    UserID    string  `json:"user_id"`
    Amount    float64 `json:"amount"`
    FromAddr  string  `json:"from_address"`
    ToAddr    string  `json:"to_address"`
}

// CreateOrder 创建订单并发布领域事件
func (s *Service) CreateOrder(req CreateOrderRequest) (*Order, error) {
    // 1. 持久化订单
    order, err := s.repo.Save(Order{
        Status: "PENDING",
        UserID: req.UserID,
        // ...
    })
    if err != nil {
        return nil, err
    }

    // 2. 发布领域事件 —— 这就是编配模式的精髓
    //    不直接调用 Payment Service，而是说"订单已创建"
    event := OrderCreatedEvent{
        OrderID: order.ID,
        UserID:  req.UserID,
        Amount:  req.Amount,
    }
    payload, _ := json.Marshal(event)
    s.publisher.Publish("order.created", message.NewMessage(
        order.ID, // 使用订单ID作为消息key，保证同一订单事件有序
        payload,
    ))
    // ⬆ 注意：Order Service 不知道谁会消费这个事件
    //    它只是"广播"了一个事实，各服务自行决定是否响应

    return order, nil
}
```

**编配模式的优点**：
- **松耦合**：服务之间不直接依赖对方的 API，只依赖事件格式
- **易扩展**：新增一个"数据分析服务"只需订阅已有事件，不影响现有服务

**编配模式的缺点**：
- **流程不可见**：没有一个地方能看到"订单创建→付款→派单→通知"这个完整流程
- **循环依赖风险**：如果不小心设计，可能出现 A→B→C→A 的事件循环

### 6.2.2 编排（Orchestration）：中央指挥的乐团

换一个思路：想象一支交响乐团，每位乐手只负责演奏自己的乐器，**指挥**负责协调整个演奏的节奏与顺序。

在编排模式中，我们引入一个 **Saga 编排器（Orchestrator）** 来集中管理业务流程。

```
                  ┌─────────────────┐
                  │     Saga        │
                  │  Orchestrator   │  ← 中央指挥官
                  └───┬───┬───┬─────┘
              命令↓   │   │   │  ↑回复
          ┌──────────┴┐ ┌┴───┴──────┐ ┌┴──────────────┐
          │  Order    │ │ Payment   │ │  Notification │
          │  Service  │ │ Service   │ │   Service     │
          └───────────┘ └───────────┘ └───────────────┘
```

**Go 代码示意（编排模式下的 Saga Orchestrator）**：

```go
// saga/orchestrator.go
package saga

import (
    "context"
    "fmt"
)

// Step 定义 Saga 中的一个步骤
type Step struct {
    Name     string
    Execute  func(ctx context.Context) error  // 正向操作
    Compensate func(ctx context.Context) error // 补偿（回滚）操作
}

// Saga 编排器
type Orchestrator struct {
    steps       []Step
    executed    []int  // 已成功执行的步骤索引
}

// Run 按顺序执行所有步骤，任一步骤失败则触发补偿
func (o *Orchestrator) Run(ctx context.Context) error {
    for i, step := range o.steps {
        fmt.Printf("[Saga] 执行步骤 %d: %s\n", i+1, step.Name)

        if err := step.Execute(ctx); err != nil {
            fmt.Printf("[Saga] 步骤 %s 失败: %v, 开始补偿...\n", step.Name, err)
            o.compensate(ctx) // 反向执行补偿
            return fmt.Errorf("saga 在步骤 %s 失败: %w", step.Name, err)
        }
        o.executed = append(o.executed, i)
    }
    fmt.Println("[Saga] 所有步骤执行成功 ✅")
    return nil
}

// compensate 反向执行已成功步骤的补偿操作
func (o *Orchestrator) compensate(ctx context.Context) {
    // 逆序补偿：最后成功的先回滚
    for i := len(o.executed) - 1; i >= 0; i-- {
        stepIdx := o.executed[i]
        step := o.steps[stepIdx]
        fmt.Printf("[Saga] 补偿步骤 %s...\n", step.Name)
        _ = step.Compensate(ctx) // 补偿失败只记录日志，不中断后续补偿
    }
}
```

```go
// saga/hermes_delivery_saga.go
// Hermes Delivery 下单 Saga 的具体编排

func NewHermesOrderSaga(
    orderSvc    *order.Service,
    paymentSvc  *payment.Service,
    dispatchSvc *dispatch.Service,
    notifySvc   *notification.Service,
) *Orchestrator {
    return &Orchestrator{
        steps: []Step{
            {
                Name: "创建订单",
                Execute: func(ctx context.Context) error {
                    return orderSvc.Create(ctx, orderData)
                },
                Compensate: func(ctx context.Context) error {
                    return orderSvc.Cancel(ctx, orderData.ID)
                },
            },
            {
                Name: "冻结余额",
                Execute: func(ctx context.Context) error {
                    return paymentSvc.Hold(ctx, userID, amount)
                },
                Compensate: func(ctx context.Context) error {
                    return paymentSvc.Release(ctx, userID, amount)
                },
            },
            {
                Name: "分配快递员",
                Execute: func(ctx context.Context) error {
                    return dispatchSvc.AssignCourier(ctx, orderID)
                },
                Compensate: func(ctx context.Context) error {
                    return dispatchSvc.ReleaseCourier(ctx, orderID)
                },
            },
            {
                Name: "发送通知",
                Execute: func(ctx context.Context) error {
                    return notifySvc.Send(ctx, userID, "订单已创建")
                },
                Compensate: func(ctx context.Context) error {
                    return notifySvc.Send(ctx, userID, "订单已取消")
                },
            },
        },
    }
}
```

### 6.2.3 编配 vs 编排：如何选择？

| 维度 | 编配 (Choreography) | 编排 (Orchestration) |
|------|---------------------|----------------------|
| **流程可见性** | 分散在各服务中，难以看到全局 | 编排器中集中可见 |
| **耦合度** | 松耦合（仅依赖事件） | 编排器强依赖各服务 API |
| **单点故障** | 无单点 | 编排器本身可能成为单点 |
| **调试难度** | 需跨服务追踪事件链 | 在编排器中可集中调试 |
| **扩展灵活性** | 极易扩展新消费者 | 需修改编排器 |
| **适用场景** | 简单流程、无回滚需求 | 复杂多步骤事务、需要补偿 |

> **选型建议**：对于 Hermes Delivery 这样的系统，**订单创建流程推荐使用编排模式**——因为它需要精确的补偿逻辑（扣款失败要取消订单）。而**状态变更通知（如"包裹已签收"）推荐编配模式**——因为多个服务可能需要独立响应这一事件，且不需要回滚。

---

## 6.3 Saga：分布式事务的工程解法

### 6.3.1 为什么需要 Saga？

在单体应用中，我们习惯用数据库的 ACID 事务：

```sql
BEGIN TRANSACTION;
  INSERT INTO orders ...;
  UPDATE accounts SET balance = balance - 50 ...;
  INSERT INTO dispatch_tasks ...;
COMMIT; -- 要么全成功，要么全失败
```

但在微服务架构中，每个服务有自己的数据库。**不存在跨数据库的 ACID 事务**。这就是 Saga 模式要解决的问题。

### 6.3.2 Saga 的本质

**Saga 是一系列本地事务的序列**，每个本地事务更新本服务的数据并发布消息/事件，触发下一个本地事务。如果某个事务失败，Saga 执行**补偿事务（Compensating Transaction）** 来撤销前面已成功的操作。

```
正向流程:  T1 ──成功──→ T2 ──成功──→ T3 ──成功──→ 完成
                            │
                            └──失败──→ C2 ──补偿──→ C1 ──补偿──→ 已回滚
```

### 6.3.3 两种 Saga 实现

**（1）编配式 Saga（Choreography-based Saga）**

与 6.2.1 节的思想一致：用事件链驱动流程。

```
Order       Payment      Dispatch
  │            │            │
  ├─订单创建──→│            │
  │            ├─扣款成功──→│
  │            │            ├─派单失败──→│
  │  ←────扣款失败───────┤            │
  ├─取消订单──→│            │
```

**缺点**：随着步骤增多，事件数量呈指数增长，流程理解困难。

**（2）编排式 Saga（Orchestration-based Saga）**

与 6.2.2 节一致：用一个编排器指挥所有步骤。本章6.2.2节的代码示例正是编排式 Saga 的实现。

### 6.3.4 补偿：不是"回滚"的"回滚"

在分布式世界中，**不存在真正的回滚**。补偿事务是一个**语义上的逆操作**：

| 正向操作 | 补偿操作（≠回滾） |
|----------|-------------------|
| 扣减余额 50 元 | 增加余额 50 元 |
| 分配快递员张三 | 释放快递员张三（注意：此时张三可能已接其他单） |
| 发送"订单成功"通知 | 发送"订单已取消"通知 |
| 预留库存 1 件 | 释放库存 1 件 |

> **关键认知**：补偿操作是"从业务语义上撤销效果"，而非"数据库层面的时间回溯"。例如取消订单后，订单记录仍然存在，只是状态变为 CANCELLED——这是**审计要求**所必需的。

---

## 6.4 最终一致性：接受"不一致的时刻"

### 6.4.1 ACID 与 BASE 的分野

| 属性 | ACID（传统事务） | BASE（分布式系统） |
|------|-----------------|-------------------|
| 一致性 | 强一致性（写入后立即可见） | 最终一致性（经过一段时间后收敛） |
| 核心机制 | 锁、MVCC、WAL | 事件驱动、补偿、重试 |
| 失败处理 | 回滚 | 补偿 + 重试 |
| 适用场景 | 单数据库、银行业核心 | 微服务、电商、物流 |

### 6.4.2 最终一致性的实践原则

**原则一：幂等性（Idempotency）**

在分布式环境中，**消息可能被投递多次**。每个服务操作必须设计为幂等的——重复执行不会产生副作用。

```go
// payment/service.go
// 幂等的扣款操作

func (s *Service) Hold(ctx context.Context, userID string, amount float64, idempotencyKey string) error {
    // 1. 先检查该幂等键是否已处理过
    processed, err := s.repo.IdempotencyExists(ctx, idempotencyKey)
    if err != nil {
        return err
    }
    if processed {
        return nil // 已处理过，直接返回成功
    }

    // 2. 执行扣款
    if err := s.repo.HoldBalance(ctx, userID, amount); err != nil {
        return err
    }

    // 3. 记录幂等键
    return s.repo.SaveIdempotency(ctx, idempotencyKey)
}
```

**原则二：重试与死信队列（Dead Letter Queue, DLQ）**

失败是常态。合理的重试策略 + 死信队列是最终一致性的保障：

```
消息 → [处理] → 失败？
                  ├─ 瞬态错误 → 重试队列 → 延迟 N 秒 → [处理]
                  └─ 持久错误 → 死信队列 → 人工介入
```

**原则三：状态机驱动**

不要用布尔标志（`paid = true/false`），用状态机：

```
订单状态机:
  PENDING → CONFIRMED → PAID → DISPATCHED → IN_TRANSIT → DELIVERED
     │          │         │         │
     └──────────┴─────────┴── CANCELLED
```

每个状态转换由明确的事件触发，状态机保证不会出现非法状态。

**原则四：读己之写（Read-Your-Writes）**

在最终一致的系统里，用户执行操作后立即查询，可能看到旧数据。解决方案：
- 关键路径使用强一致读（如从主库读）
- 非关键路径在前端展示 "处理中" 状态，优雅降级

---

## 6.5 Hermes Delivery 完整通信方案设计

现在让我们将本章和前两章的知识融会贯通，设计 Hermes Delivery 的完整服务通信方案。

### 6.5.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Hermes Delivery                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  同步(gRPC)   ┌─────────┐   事件(Kafka)       │
│  │  API    │ ←──────────→ │  Order  │ ──────────────┐      │
│  │ Gateway │              │ Service │                │      │
│  └─────────┘              └────┬────┘                │      │
│                                │ gRPC                 │      │
│              ┌─────────────────┼───────────────┐     │      │
│              ▼                 ▼               ▼     │      │
│        ┌──────────┐    ┌──────────┐    ┌──────────┐  │      │
│        │ Payment  │    │ Dispatch │    │  Order   │  │      │
│        │ Service  │    │ Service  │    │  Saga    │  │      │
│        └──────────┘    └──────────┘    └──────────┘  │      │
│              │                 │               │      │      │
│              └────────┬────────┘               │      │      │
│                       │ 事件(Kafka)            │      │      │
│                       ▼                        │      │      │
│                ┌──────────────┐                │      │      │
│                │ Notification │ ←──────────────┘      │      │
│                │   Service    │  事件订阅              │      │
│                └──────────────┘                       │      │
│                       │                               │      │
│                       ▼                               │      │
│                ┌──────────────┐                       │      │
│                │  用户/快递员  │                       │      │
│                │  (Push/短信)  │                       │      │
│                └──────────────┘                       │      │
└─────────────────────────────────────────────────────────────┘
```

### 6.5.2 通信方案决策矩阵

| 交互场景 | 通信方式 | 协调模式 | 理由 |
|----------|----------|----------|------|
| 用户创建订单 → 系统 | 同步 REST（API Gateway） | — | 用户需要即时反馈 |
| 订单创建 → 扣款 → 派单 | gRPC + 编排式 Saga | 编排 (Orchestration) | 需要精确的补偿逻辑 |
| 订单状态变更 → 通知用户 | 事件驱动 (Kafka) | 编配 (Choreography) | 多消费者（Push/短信/邮件），无回滚需求 |
| 快递员位置上报 | gRPC 双向流 | — | 实时双向数据流 |
| 日终对账 | 异步消息 (Kafka) | 编配 | 非实时，批处理场景 |
| 内部服务健康检查 | gRPC Health Check | — | 标准协议 |

### 6.5.3 下单 Saga 的完整流程

```
时间轴 ──────────────────────────────────────────────→

1. API Gateway 接收用户下单请求（REST）
   │
   ▼
2. Order Saga Orchestrator 启动 Saga
   │
   ├─[Step 1]─→ Order Service: 创建订单(PENDING)
   │              │ 失败？→ 直接返回错误给用户
   │              │
   ├─[Step 2]─→ Payment Service: 冻结余额
   │              │ 失败？→ 补偿 Step 1：CancelOrder
   │              │
   ├─[Step 3]─→ Dispatch Service: 分配快递员
   │              │ 失败？→ 补偿 Step 2：ReleaseBalance
   │              │         补偿 Step 1：CancelOrder
   │              │
   ├─[Step 4]─→ Order Service: 确认订单(CONFIRMED)
   │              │ 失败？→ 补偿 Step 3：ReleaseCourier
   │              │         补偿 Step 2：ReleaseBalance
   │              │         补偿 Step 1：CancelOrder
   │              │
   ▼
3. Order Service 发布 OrderConfirmed 事件（Kafka）
   │
   ├─→ Notification Service 消费：发送Push通知
   ├─→ Analytics Service 消费：更新实时看板
   └─→ Tracking Service 消费：初始化物流轨迹
```

### 6.5.4 关键设计决策

**为什么下单用编排而非编配？**

下单 Saga 包含 4 个步骤，其中 3 个需要补偿（订单可取消、余额可释放、快递员可释放）。如果用编配模式，事件流如下：

```
OrderCreated → PaymentService.Hold() → PaymentAuthorized → DispatchService.Assign()
    ↓ (分配失败)
PaymentFailed ← PaymentService.Release() ← DispatchFailed
    ↓
OrderCancelled
```

这里 Payment Service 需要同时消费 `OrderCreated` 和 `DispatchFailed` 事件——这意味着 Payment Service 需要**了解下单的完整流程**，违背了单一职责原则。编排模式下，流程知识集中在 Saga Orchestrator 中，各服务只需提供 `Do()` 和 `Undo()` 接口。

---

## 6.6 常见误区

### 误区一："Saga 保证了 ACID"

**错误认知**：使用了 Saga 模式，我的跨服务操作就和数据库事务一样安全了。

**实际真相**：Saga 提供的是 **ACD（Atomicity, Consistency, Durability）**，但**不提供 Isolation（隔离性）**。在 Saga 执行过程中，其他请求可能读到中间状态的数据。

**案例**：用户 A 下单时冻结了余额，此时用户 B 查询余额会看到"钱少了但订单还没确认"。这就是隔离性的缺失——在 ACID 事务中，其他事务看不到未提交的修改。

**补救措施**：
- 语义锁（Semantic Lock）：在订单表中设置 `PENDING` 状态，余额查询时对 PENDING 状态的冻结金额单独展示
- 补偿重试：确保最终收敛

### 误区二："编配一定比编排更解耦"

**错误认知**：编配是事件驱动的，所以一定更松耦合。

**实际真相**：编配模式将流程逻辑从集中式编排器转移到了各服务的事件处理逻辑中。如果流程复杂，每个服务都需要理解部分流程上下文，导致**逻辑耦合**——改一个步骤可能影响多个服务的事件处理逻辑。

**案例**：在下单流程中新增一个"风控检查"步骤。编配模式下，需要修改 Order Service（发布风控检查请求事件）、Payment Service（改为消费风控结果事件而非直接消费 OrderCreated）等多个服务。而编排模式下只需在 Orchestrator 中插入一个步骤。

### 误区三："最终一致性就是'数据过一会儿就对上了'"

**错误认知**：最终一致性很简单，就是异步处理，数据最终会一致。

**实际真相**：最终一致性需要精心设计：
1. **幂等性**：每条消息可能被消费多次
2. **乱序**：消息可能不按发送顺序到达
3. **超时**：长时间未确认的消息需要特殊处理
4. **监控**：需要有手段检测当前的不一致程度和恢复进度

**案例**：Hermes Delivery 中，如果"快递员已取件"事件比"快递员已分配"事件先到达 Tracking Service（网络延迟导致乱序），Tracking Service 必须能处理这种乱序——否则物流轨迹会出现"先取件后分配"的荒谬记录。

---

## 6.7 本章小结

```
                        第6章 服务通信模式综合

     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
     │  编配模式      │    │  编排模式      │    │  Saga 事务    │
     │  Choreography │    │ Orchestration │    │  分布式事务    │
     ├──────────────┤    ├──────────────┤    ├──────────────┤
     │ ·事件驱动      │    │ ·中央协调器    │    │ ·编排式 Saga  │
     │ ·去中心化      │    │ ·命令式调用    │    │ ·编配式 Saga  │
     │ ·松耦合        │    │ ·流程可见      │    │ ·补偿事务     │
     └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │    最终一致性实践       │
                    ├───────────────────────┤
                    │ ·幂等性     ·死信队列   │
                    │ ·状态机     ·读己之写   │
                    └───────────────────────┘
```

### 关键术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 编配 | Choreography | 去中心化的服务协调模式，通过事件链驱动流程 |
| 编排 | Orchestration | 集中式的服务协调模式，通过编排器指挥流程 |
| Saga | Saga | 一系列本地事务的序列，通过补偿机制实现跨服务数据一致性 |
| 补偿事务 | Compensating Transaction | 在 Saga 失败时执行的逆操作，从业务语义上撤销已成功步骤的效果 |
| 最终一致性 | Eventual Consistency | 数据在一段时间后收敛到一致状态的保证，非即时一致 |
| 幂等性 | Idempotency | 同一操作执行多次与执行一次产生相同效果的特性 |
| 死信队列 | Dead Letter Queue (DLQ) | 多次重试失败后的消息暂存队列，等待人工处理 |
| 编排器 | Orchestrator / Saga Coordinator | 编排模式中的中央协调组件 |

---

## 6.8 练习

### 基础题（5题）

**6-1** 请用自己的语言解释编配（Choreography）与编排（Orchestration）的核心区别，并各举一个现实生活中的类比（不能用本章已有的"舞蹈"和"乐团"）。

**6-2** 在 Saga 模式中，为什么补偿事务不能简单等同于数据库的 ROLLBACK？请从"业务语义"角度举例说明。

**6-3** 什么是幂等性？在 Hermes Delivery 中，如果不保证幂等性，可能出现什么问题？请举出至少两个具体场景。

**6-4** 最终一致性与 ACID 的强一致性有何不同？请用"银行转账"和"朋友圈点赞"两个场景分别说明哪种一致性更合适。

**6-5** 在编排式 Saga 中，如果 Orchestrator 本身崩溃了，正在执行的 Saga 会怎样？有哪些常见的恢复策略？

### 综合题（3题）

**6-6** **【设计题】** Hermes Delivery 计划新增一个"智能定价"功能：下单时需要先调用 Pricing Service 获取实时报价（根据距离、天气、时段等动态计算），然后才能继续后续流程。请完成以下任务：
  （a）在下单 Saga 中插入这个新步骤，画出完整的 Saga 流程（包括正向操作和补偿操作）  
  （b）讨论：Pricing Service 的调用放在 Saga 的哪个位置最合理？为什么？

**6-7** **【分析题】** 假设 Hermes Delivery 的订单通知系统使用了编配模式：Order Service 发布 `OrderCreated` 事件，Notification Service 和 Analytics Service 都消费此事件。现在 Analytics Service 的处理逻辑出现 Bug，每次消费事件都会崩溃。
  （a）这个 Bug 是否会影响用户收到通知？为什么？  
  （b）如果 Analytics Service 在处理了 100 条事件后才被发现有问题，如何"补偿"这些错误处理？  
  （c）如果这个场景改用编排模式，会有什么不同的后果？

**6-8** **【编码题】** 参考本章 6.2.2 节的 Saga Orchestrator 代码，为 Hermes Delivery 实现一个新的 Saga：**"快递员取消接单"流程**。该流程需要：
  - 取消调度分配（Dispatch Service）
  - 释放快递员状态为"空闲"
  - 将订单重新放回待分配池
  - 通知用户"快递员已变更"

  要求：用 Go 语言写出 `NewCancelAssignmentSaga()` 函数，定义每个步骤的正向操作和补偿操作。

### 拓展题（2题）

**6-9** **【调研题】** 查阅资料，了解 Netflix Conductor、Uber Cadence、Temporal 等开源 Saga/工作流引擎的设计。选择一个引擎，分析它是如何解决以下两个问题的：
  （a）编排器自身的容错（不丢失 Saga 状态）  
  （b）长时间运行 Saga 的状态管理（一个 Saga 可能持续数天）

**6-10** **【辩论题】** 一个常见的工程争论是："微服务架构下，应该尽量减少分布式事务。如果一个操作涉及超过 3 个服务，就应该考虑重新设计服务边界，而不是用 Saga 来补救。" 你同意这个观点吗？请从以下角度组织你的论点：
  （a）服务粒度与事务复杂度的关系
  （b）过度拆分 vs 过度补偿
  （c）结合 Hermes Delivery 的具体场景

---

> **下一章预告**：第7章「容器化基础」将进入第三篇，学习如何用 Docker 将 Hermes Delivery 的各个微服务打包为容器镜像，实现一致的构建和交付。
