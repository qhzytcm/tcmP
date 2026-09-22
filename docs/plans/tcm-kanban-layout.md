# Kanban 看板 · 四层分层布局设计

> **看板名称：** `tcm-knowledge-tree`  
> **分层逻辑：** 每个 Agent 层级有独立的看板视图，层级间通过任务流转实现串联。  
> **物理载体：** Hermes Kanban（SQLite）+ 八领域各自独立 Board。

---

## 一、总体布局：四层 × 六阶段 矩阵

```
                       阶段一      阶段二      阶段三      阶段四      阶段五      阶段六
                       (需求)      (设计)      (编写)      (审核)      (应用)      (修订)
                      
┌─────────────┐    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ L1 行业主编  │    │ 签批总纲  │ 签发规范  │ 跨域仲裁  │ 终审签批  │ 审阅全局  │ 签发修订令│
│ (Board: L1) │    │          │          │(例外介入)│          │ 反馈报告  │          │
├─────────────┤    ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ L2 领域主编  │    │ 岗位调研  │ 域架构图  │ 跨科协调  │ 域一致性  │ 收集域   │ 域修订    │
│ (8 Boards)  │    │ 能力矩阵  │ 术语规范  │          │ 岗位匹配  │ 反馈     │ 计划      │
├─────────────┤    ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ L3 学科主编  │    │ 知识点清单│ 章节结构  │ 实时指导  │ 科学性审  │ 汇总学科  │ 分配      │
│ (~120 Boards)│   │ 依赖图    │ 目标矩阵  │          │ 教学审    │ 反馈     │ 修改任务  │
├─────────────┤    ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ L4 章节作者  │    │ 读者调研  │ 教学详案  │ 执笔写草稿│ 自审自查  │ 接收反馈  │ 执笔      │
│ (N Cards)   │    │ 素材采风  │          │ 提交审核  │          │          │ 执行修改  │
└─────────────┘    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## 二、九宫格看板（每个 Agent 层级的标准视图）

每个 Agent 层级看板使用统一九宫格布局：

```
┌──────────────┬──────────────┬──────────────┐
│              │              │              │
│   Backlog    │   Ready      │  In Progress │
│   (待办池)   │   (就绪)     │   (进行中)   │
│              │              │              │
├──────────────┼──────────────┼──────────────┤
│              │              │              │
│   Review     │   Blocked    │   Revision   │
│   (审核中)   │   (阻塞)     │   (修订中)   │
│              │              │              │
├──────────────┼──────────────┼──────────────┤
│              │              │              │
│   Done       │   Archived   │   Escalated  │
│   (已完成)   │   (归档)     │   (已升级)   │
│              │              │              │
└──────────────┴──────────────┴──────────────┘
```

### 列定义

| 列 | 含义 | 谁放入 | 谁拉取 |
|------|------|:--:|:--:|
| **Backlog** | 待办池，任务尚未分配 | L3/L2/L1 | L4/L3/L2 |
| **Ready** | 任务已分配，就绪待执行 | 上层Agent | 下层Agent |
| **In Progress** | 正在执行中 | 下层Agent | — |
| **Review** | 提交审核，等待上级审阅 | 下层Agent | 上层Agent |
| **Blocked** | 因依赖未满足而阻塞 | 任何Agent | 上层Agent |
| **Revision** | 审核不通过，需修改 | 上层Agent | 下层Agent |
| **Done** | 审核通过，完成 | 上层Agent | — |
| **Archived** | 已归档的历史任务 | 系统自动 | — |
| **Escalated** | 多次驳回，已升级到更高层 | 当前层Agent | 更高层Agent |

---

## 三、层级间任务流转协议

### 3.1 L4 → L3 流转（章节作者 ↔ 学科主编）

```
L4 编写完成
    │
    ▼
L4 自审 → 通过 → 卡片从 In Progress 移到 Review
    │
    ▼
L3 学科审 → 通过 → 卡片从 Review 移到 Done
    │
    ├── 不通过(第1次) → 卡片移到 Revision，附修改意见
    │       │
    │       └── L4 修改 → 重新提交 → 卡片移回 Review
    │
    ├── 不通过(第2次) → 卡片移回 Revision，附详细修改清单
    │       │
    │       └── L4 修改 → 重新提交 → 卡片移回 Review
    │
    └── 不通过(第3次) → 卡片移到 Escalated
            │
            └── 自动通知 L2 领域主编介入裁定
```

### 3.2 L3 → L2 流转（学科主编 ↔ 领域主编）

```
L3 学科审通过
    │
    ▼
学科全部章节 Done → L3 汇总 → 创建"XX学科-域审"卡片在 L2 Board
    │
    ▼
L2 领域审 → 检查跨学科一致性 + 岗位匹配度
    │
    ├── 通过 → Done
    ├── 不通过 → Revision（退回 L3 协调修改）
    └── 不通过(第3次) → Escalated → L1 介入
```

### 3.3 L2 → L1 流转（领域主编 ↔ 行业主编）

```
L2 领域内部全部学科 Done → L2 汇总 → 创建"XX域-终审"卡片在 L1 Board
    │
    ▼
L1 终审 → 全局合规 + 四层级衔接
    │
    ├── 通过 → Done → 进入阶段五(教学应用)
    ├── 有条件通过 → Revision → 退回 L2 督办
    └── 驳回 → 记录为全局判例
```

---

## 四、八领域独立看板设计

每个领域拥有独立的 Kanban Board，由对应的 L2 领域主编管理：

```
┌─────────────────────────────────────────────────────────┐
│ Board: branch-02-herb (枝2·中药域)                       │
│ Owner: L2-领域主编-中药                                   │
│                                                         │
│  ┌──────────┬──────────┬──────────┐                     │
│  │ Backlog  │ Ready    │ In Prog  │  ← 当前阶段列       │
│  ├──────────┼──────────┼──────────┤                     │
│  │ Review   │ Blocked  │ Revision │  ← 审核流转列       │
│  ├──────────┼──────────┼──────────┤                     │
│  │ Done     │ Archived │ Escalate │  ← 终态列           │
│  └──────────┴──────────┴──────────┘                     │
│                                                         │
│  Cards:                                                  │
│  ├── [中药学] L3-学科主编 → 27个章节卡片                  │
│  ├── [中药炮制学] L3-学科主编 → 12个章节卡片              │
│  ├── [中药药理学] L3-学科主编 → 15个章节卡片              │
│  ├── ...（共14个L3学科）                                  │
│  └── [域审] L2审核卡片（域内跨学科一致性）                │
└─────────────────────────────────────────────────────────┘
```

### 八领域 Board 清单

| Board Slug | 枝编号 | 领域 | L2 Owner | 含 L3 子任务数 |
|------|:--:|------|------|:--:|
| `branch-01-basic` | 枝1 | 基础医学院 | L2-领域主编-基础 | 8 学科 × N章 |
| `branch-02-herb` | 枝2 | 中药学院 | L2-领域主编-中药 | 14 学科 × N章 |
| `branch-03-acupuncture` | 枝3 | 针灸推拿学院 | L2-领域主编-针灸 | 8 学科 × N章 |
| `branch-04-internal` | 枝4 | 第一临床医学院 | L2-领域主编-内科 | 18 学科 × N章 |
| `branch-05-surgery` | 枝5 | 第二临床医学院 | L2-领域主编-外科 | 12 学科 × N章 |
| `branch-06-tcm-ai` | 枝6 | 中医智能学院 | L2-领域主编-智能 | 15 学科 × N章 |
| `branch-07-nursing` | 枝7 | 护理学院 | L2-领域主编-护理 | 8 学科 × N章 |
| `branch-08-management` | 枝8 | 管理人文学院 | L2-领域主编-管理 | 8 学科 × N章 |

### 顶层 L1 Board

| Board Slug | 说明 | Owner |
|------|------|------|
| `tcm-master` | 全局总控板，汇总八域状态 | L1-行业主编 |

---

## 五、卡片（Card）标准化模板

### 5.1 L4 编写卡片

```yaml
title: "编写 第3章·解表药（中药学·枝2）"
assignee: L4-zhongyaoxue-ch03
board: branch-02-herb
status: Ready
backend: local                    # 新增：任务指定后端
backend_fallback: docker          # 新增：后端不可用时的降级
labels: [phase-3, writing, L4, branch-02, subject-009]
body: |
  ## 编写要求
  - 学科：中药学（编号 subject-009）
  - 章节：第3章 解表药
  - 预估篇幅：18,000 字
  - 认知层级：阶段Ⅱ（理解建构）
  
  ## 知识点清单
  1. 解表药概述（分类、功效、适应证）
  2. 麻黄（来源、性味归经、功效、应用、用法用量）
  3. 桂枝
  4. 紫苏
  ... (共25个知识点)
  
  ## 前置依赖
  - 第1章·总论（中药学基本理论）
  - 第2章·中药的性能
```

### 5.2 L3 审核卡片

```yaml
title: "审核 第3章·解表药（L3学科审）"
assignee: L3-zhongyaoxue
board: branch-02-herb
status: Ready
backend: daytona                   # 新增
backend_fallback: ssh              # 新增
labels: [phase-4, review, L3, subject-009]
body: |
  ## 审核材料
  - 草稿路径：content/branch-02-herb/subject-009/drafts/ch03-jiebiao.md
  - 编写说明：本人在编写中着重参考了2025版药典...
  
  ## L3 审核维度（阶段四 Step 2）
  - [ ] 科学性：所有药物信息是否准确
  - [ ] 教学适用性：认知递进是否合理
  - [ ] 章节一致性：与前后的衔接
  - [ ] 习题质量：是否覆盖目标、答案正确
  
  ## 关联
  - 上游卡片：编写-第3章-解表药
  - 参考标准：枝2域术语规范表 v1.0
```

### 5.3 L2 域审卡片

```yaml
title: "域审 中药学（枝2·跨学科一致性）"
assignee: L2-herb
board: branch-02-herb
status: Ready
backend: singularity               # 新增：HPC计算
backend_fallback: ssh              # 新增
labels: [phase-4, review, L2, domain-cross-check]
body: |
  ## 审核范围
  - 中药学全部 27 章（L3 审核已全部通过）
  
  ## L2 审核维度（阶段四 Step 3）
  - [ ] 跨学科一致性：与中药药理学、临床中药学的术语是否统一
  - [ ] 岗位匹配度：内容是否覆盖医院药师岗位核心能力
  - [ ] 层级衔接：本科/硕士知识点递进是否有效
  
  ## 关联
  - 上游卡片：中药学 27 章各章 L3 审核卡片
  - 需对比学科：中药药理学、临床中药学、中药炮制学
```

### 5.4 L1 终审卡片

```yaml
title: "终审 中药域（枝2）"
assignee: L1-chief
board: tcm-master
status: Ready
backend: managed_modal             # 新增：生产级托管
backend_fallback: modal            # 新增
labels: [phase-4, review, L1, final-signoff]
body: |
  ## 终审范围
  - 枝2·中药域下全部 14 种学科（L2 域审已通过）
  
  ## L1 审核维度（阶段四 Step 4）
  - [ ] 全局术语一致性：与其他七域的术语是否统一
  - [ ] 四层级衔接：本/硕/博/博后知识递进完整
  - [ ] 安全合规：民族医药表述、人体图示规范
  - [ ] 思政与价值观：医学伦理、职业精神
  
  ## 关联
  - 上游：枝2 全部 L2 域审卡片
  - 需跨域对比：枝4内科域（中药临床应用部分）
```

---

## 六、任务看板在六阶段的列映射

不同阶段，九宫格的核心使用列不同：

| 阶段 | 核心列（高频流转） | 交互方向 | 典型卡片流动 |
|:--:|------|:--:|------|
| **阶段一<br>需求** | Backlog → Ready → In Progress → Done | ↓ Down | L1 创建总纲卡 → L2 认领岗位调研卡 → L3 认领知识点卡 |
| **阶段二<br>设计** | Backlog → Ready → In Progress → Done | ↓ Down | L1 签发规范卡 → L2 认领架构图卡 → L4 认领详案卡 |
| **阶段三<br>编写** | Ready → In Progress → Review | ↓ Down(指导) | L4 拉取章节卡 → 编写 → 自审 → 移到 Review |
| **阶段四<br>审核** | Review → Revision → Done<br>→ Escalated | ↑ Up | L3审 → 通过→Done / 驳回→Revision / 超限→Escalated |
| **阶段五<br>应用** | Backlog → In Progress → Done | ← 横向 | 使用者反馈卡 → L3/L2 收集 → Done 归档 |
| **阶段六<br>修订** | Ready → In Progress → Review → Done | ↓ Down | L1 修订令 → L2 计划 → L3 分配 → L4 修改 |

---

## 七、看板拓扑关系图

```
                        ┌─────────────┐
                        │  tcm-master │  ← L1 Board (全局)
                        │  1 Board    │
                        └──────┬──────┘
                               │
          ┌────────┬───────┬───┼───┬───────┬────────┬────────┐
          ▼        ▼       ▼   │   ▼       ▼        ▼        ▼
   ┌─────────┐┌─────────┐ ...  │  ... ┌─────────┐┌─────────┐
   │branch-01││branch-02│      │      │branch-07││branch-08│ ← L2 Boards
   │基础域   ││中药域   │      │      │护理域   ││管理域   │    (8个)
   └────┬────┘└────┬────┘      │      └────┬────┘└────┬────┘
        │          │           │           │          │
   ┌────┴────┐┌────┴────┐      │      ┌────┴────┐┌────┴────┐
   │subject  ││subject  │      │      │subject  ││subject  │  ← 学科级任务
   │001-008  ││009-022  │      │      │079-086  ││087-094  │    (14×8=112组)
   │   × N章 ││   × N章 │      │      │   × N章 ││   × N章 │
   └─────────┘└─────────┘      │      └─────────┘└─────────┘
                               │
                     L4 卡片总数 ≈ 102×25 = ~2,550 张
                     卡片自动创建于阶段一结束、阶段二开始之际
```

---

## 八、Kanban 创建命令（Hermes CLI）

```bash
# 1. 创建八领域 Board
hermes kanban boards create branch-01-basic
hermes kanban boards create branch-02-herb
hermes kanban boards create branch-03-acupuncture
hermes kanban boards create branch-04-internal
hermes kanban boards create branch-05-surgery
hermes kanban boards create branch-06-tcm-ai
hermes kanban boards create branch-07-nursing
hermes kanban boards create branch-08-management

# 2. 创建全局 L1 Board
hermes kanban boards create tcm-master

# 3. 切换到枝2 Board 并批量创建章节卡片
hermes kanban boards switch branch-02-herb

for ch in \
  "编写 第1章·总论（中药学）|学科编号009 预估15000字 认知阶段Ⅰ" \
  "编写 第2章·中药的性能|学科编号009 预估12000字 认知阶段Ⅰ" \
  "编写 第3章·解表药|学科编号009 预估18000字 认知阶段Ⅱ" \
  ; do
  title="${ch%%|*}"
  body="${ch#*|}"
  hermes kanban create "$title" \
    --body "$body" \
    --assignee "L4-zhongyaoxue-ch$(echo $title | grep -oP '\d+')"
done

# 4. 设置 Board 默认工作目录
hermes kanban boards set-default-workdir branch-02-herb \
  ~/tcm-project/content/branch-02-herb/
```

---

> **关联文档：**
> - `tcm-requirements-analysis.md` — 项目需求分析
> - `tcm-agent-tree-architecture.html` — 架构图（含四层树状图 + 路由流程图）
> - `tcm-project-directory-structure.md` — 项目目录结构
