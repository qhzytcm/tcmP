# 中医中药教材编写平台 — 四层 Agent 树状路由系统 · 重设计

> **核心变更：** 四层不再是"角色模式切换"，而是四个**独立运行的 Agent 实例**，各自身份不同、工具不同、覆盖范围不同。完整编写链形成「一干八枝」树状知识结构，终端目标为「知识点搜索 → 精准定位描述专家」。

---

## 〇、总览：Agent 即知识节点

```
                          ┌─────────────────┐
                          │   行业主编 (L1)  │  ← 根节点：全系列102种教材
                          │   scope: ALL     │     工具：全局统计、跨域仲裁、安全红线
                          │   1 个实例       │
                          └────────┬────────┘
                                   │
          ┌────────────┬───────────┼───────────┬───────────┬──────────┬──────────┬──────────┐
          ▼            ▼           ▼           ▼           ▼          ▼          ▼          ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │领域主编   │ │领域主编   │ │领域主编   │ │领域主编   │ │领域主编   │ │领域主编   │ │领域主编   │ │领域主编   │
   │枝1:基础  │ │枝2:中药  │ │枝3:方剂  │ │枝4:内科  │ │枝5:针灸  │ │枝6:外科  │ │枝7:妇儿  │ │枝8:经典  │
   │scope:8种 │ │scope:14种│ │scope:6种 │ │scope:18种│ │scope:8种 │ │scope:12种│ │scope:8种 │ │scope:10种│
   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
        │            │            │            │            │            │            │            │
   ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐       ...          ...          ...          ...
   ▼         ▼  ▼         ▼  ▼         ▼  ▼         ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│学科   │ │学科   │ │学科   │ │学科   │ │学科   │ │学科   │ │学科   │ │学科   │
│主编   │ │主编   │ │主编   │ │主编   │ │主编   │ │主编   │ │主编   │ │主编   │
│中基   │ │诊断   │ │中药学 │ │炮制学 │ │方剂学 │ │...    │ │内科   │ │外科   │
│scope: │ │scope: │ │scope: │ │scope: │ │scope: │ │       │ │scope: │ │scope: │
│1种教材│ │1种教材│ │1种教材│ │1种教材│ │1种教材│ │       │ │1种教材│ │1种教材│
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘         └──┬───┘ └──┬───┘
   │        │        │        │        │                │        │
   ▼        ▼        ▼        ▼        ▼                ▼        ▼
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐          ┌──────┐┌──────┐
│章节   ││章节   ││章节   ││章节   ││章节   │   ...    │章节   ││章节   │
│作者   ││作者   ││作者   ││作者   ││作者   │          │作者   ││作者   │
│第1章  ││第2章  ││第1章  ││第2章  ││第1章  │          │第1章  ││第2章  │
│阴阳   ││五行   ││总论   ││解表药 ││总论   │          │总论   ││各论   │
└──────┘└──────┘└──────┘└──────┘└──────┘          └──────┘└──────┘
```

---

## 一、四个 Agent 类型定义（身份 · 工具 · 范围）

### Agent L1：行业主编（Industry Editor-in-Chief）

| 属性 | 定义 |
|------|------|
| **身份 (SOUL)** | 中医药教材系列的**最高学术负责人**，对全部 102 种教材的编写质量负总责。不参与具体内容编写，只做终审裁定。 |
| **工具集** | `web`（检索行业标准）、`file`（读写全局规范）、`terminal`（运行统计脚本）、`kanban`（看板总览）、`session_search`（回溯决策历史）、`delegation`（向 L2 下发仲裁任务） |
| **覆盖范围** | `scope: ALL` — 全部 8 个领域、102 种教材 |
| **典型 Prompt** | "审查《中药学》与《方剂学》之间的术语一致性，输出不一致清单" |
| **不可做** | 不可直接修改章节内容；不可跳过 L2/L3 直接给 L4 下指令 |

### Agent L2：领域主编（Domain Editor-in-Chief）

| 属性 | 定义 |
|------|------|
| **身份 (SOUL)** | 某一**知识域**的学术负责人（如「中药域」共 14 种教材）。精通该领域的学科体系、前沿进展和学术争议。 |
| **工具集** | `file`（读/写领域内文档）、`web`（检索该领域最新文献）、`terminal`（领域内批量校验脚本）、`kanban`（领域任务分派）、`delegation`（向 L3 下发审核任务） |
| **覆盖范围** | `scope: domain-X` — 该领域下全部学科（约 6-18 种教材） |
| **典型 Prompt** | "审查中药域下各学科对'药性'定义的统一性，对比《中药学》《中药药理学》《临床中药学》三书" |
| **不可做** | 不可跨域裁决（如中药域主编不可审批针灸域内容）；不可直接修改学科主编已审定的章节 |

**八个领域（枝）划分：**

| 枝编号 | 领域名 | 覆盖教材数 | 典型学科 |
|:--:|------|:--:|------|
| 枝1 | 中医基础 | 8 | 中基、诊断、内经、各家学说、中医思维… |
| 枝2 | 中药 | 14 | 中药学、炮制学、药理学、鉴定学、药用植物学… |
| 枝3 | 方剂 | 6 | 方剂学、临床方剂学、方剂现代研究… |
| 枝4 | 临床内科 | 18 | 内科、温病、金匮、中西医结合内科… |
| 枝5 | 针灸推拿 | 8 | 针灸学、推拿学、经络学、实验针灸学… |
| 枝6 | 外科骨伤 | 12 | 外科学、骨伤科学、眼科学、耳鼻喉科学… |
| 枝7 | 妇儿 | 8 | 妇科学、儿科学、中医优生学… |
| 枝8 | 经典医籍 | 10 | 伤寒论、金匮要略、温病学、医古文… |

### Agent L3：学科主编（Subject Editor-in-Chief）

| 属性 | 定义 |
|------|------|
| **身份 (SOUL)** | 单一**学科**的负责人（如「方剂学」1 种教材）。对该学科的每一章内容质量负责，是实际内容审核的主力。 |
| **工具集** | `file`（逐章读写）、`terminal`（术语一致性校验）、`web`（检索具体知识点的最新证据）、`kanban`（分配章任务）、`delegation`（向 L4 下发编写/修改任务） |
| **覆盖范围** | `scope: subject-X` — 单一教材的全部章节（约 10-30 章） |
| **典型 Prompt** | "审查《方剂学》第3章解表剂中麻黄汤的君臣佐使分析是否与第1章总论配伍原则一致" |
| **不可做** | 不可跨学科裁决；不可越过领域主编直接修改跨学科的术语定义 |

### Agent L4：章节作者（Chapter Author）

| 属性 | 定义 |
|------|------|
| **身份 (SOUL)** | 具体**章节**的执笔人。深度掌握该章涵盖的知识点，负责从草稿到终稿的全部撰写和修改。 |
| **工具集** | `file`（读写草稿）、`web`（检索知识点最新文献）、`terminal`（运行引用校验）、`kanban`（领取/完成任务） |
| **覆盖范围** | `scope: chapter-X` — 单一章节（约 5000-20000 字） |
| **典型 Prompt** | "编写《方剂学》第3章第1节'麻黄汤'，含方源、组成、用法、功用、主治、方解、配伍特点、临床应用、现代研究" |
| **不可做** | 不可自行批准自己的稿件进入下一审核层；不可修改其他作者负责的章节 |

---

## 二、一干八枝树状结构详解

### 2.1 「干」：主干流水线

```
行业主编 (L1)
    │
    │ 下发教材编写任务、制定标准
    ▼
领域主编 (L2)
    │
    │ 拆分学科任务、审核跨学科一致性
    ▼
学科主编 (L3)
    │
    │ 拆分章节任务、审核内容质量
    ▼
章节作者 (L4)
    │
    │ 撰写章节内容
    ▼
[反向审核链：L4提交 → L3审核 → L2复核 → L1终审]
```

### 2.2 「枝」：八域知识分支

每一个领域是一个**自包含的知识分支**，拥有完整的 L2→L3→L4 子树：

```
中药域 (枝2)
├── L2-领域主编-中药 (1个实例)
│   ├── L3-学科主编-中药学 (1个实例)
│   │   ├── L4-章节作者-总论 (实例A)
│   │   ├── L4-章节作者-解表药 (实例B)
│   │   ├── L4-章节作者-清热药 (实例C)
│   │   └── ... (共27章，约27个L4实例)
│   ├── L3-学科主编-中药炮制学 (1个实例)
│   │   └── L4 × N
│   ├── L3-学科主编-中药药理学 (1个实例)
│   │   └── L4 × N
│   └── ... (共14个L3实例，对应14种教材)
│
方剂域 (枝3)
├── L2-领域主编-方剂 (1个实例)
│   ├── L3-学科主编-方剂学 (1个实例)
│   │   ├── L4-章节作者-总论 (实例)
│   │   ├── L4-章节作者-解表剂 (实例)
│   │   └── ...
│   └── ... (共6个L3实例)
│
... (其余6枝结构相同)
```

### 2.3 知识节点编码体系

每个知识节点有唯一路径编码，用于路由定位：

```
知识节点编码格式：
  {枝号}.{学科编号}.{章号}.{节号}.{知识点序号}

示例：
  3.1.3.1.2 = 枝3(方剂域) → 学科1(方剂学) → 第3章(解表剂) → 第1节(辛温解表) → 知识点2(麻黄汤)
  2.1.5.3.1 = 枝2(中药域) → 学科1(中药学) → 第5章(清热药) → 第3节(清热凉血药) → 知识点1(生地黄)
```

---

## 三、知识点搜索 → 专家定位路由系统（核心目标）

### 3.1 路由架构

```
用户输入："麻黄汤的君臣佐使配伍原理"
         │
         ▼
   ┌─────────────┐
   │ 知识解析器   │  → NLP 提取：实体=麻黄汤，意图=配伍分析
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ 树状索引    │  → 查知识树：麻黄汤 ∈ 枝3(方剂) > 方剂学 > 第3章(解表剂) > 第1节 > 知识点2
   │ (编码查询)  │
   └──────┬──────┘
          │
          ▼
   ┌─────────────────────────────────────────────┐
   │             Agent 路由器                      │
   │                                              │
   │  匹配优先级：                                  │
   │  1. 精确匹配 L4（章节作者-解表剂章的麻黄汤知识点） │
   │  2. 若 L4 不存在 → 上溯到 L3（学科主编-方剂学）  │
   │  3. 若 L3 不可用 → 上溯到 L2（领域主编-方剂域）  │
   │  4. 若 L2 不可用 → 上溯到 L1（行业主编）        │
   └──────┬──────────────────────────────────────┘
          │
          ▼
   ┌─────────────┐
   │ 路由到 Agent │  → 启动对应 Hermes Profile，注入上下文
   │ 返回结果     │  → 专家 Agent 输出知识描述
   └─────────────┘
```

### 3.2 路由优先级矩阵

| 匹配级别 | 路由目标 | 优势 | 适用场景 |
|:--:|------|------|------|
| **L4 精确** | 章节作者 | 对该知识点的上下文最熟悉 | 具体方剂/药物/证型的细节描述 |
| **L3 学科** | 学科主编 | 理解该知识点在整本教材中的定位 | 跨章节一致性、学科级知识问答 |
| **L2 领域** | 领域主编 | 理解该知识点在领域内的横向关联 | 跨学科对比、领域级趋势分析 |
| **L1 全局** | 行业主编 | 宏观视角，跨域仲裁 | 跨领域标准制定、全局规范 |

### 3.3 数据库核心表设计（Cursor 3.0 开发关注点）

```sql
-- 知识树节点表
CREATE TABLE knowledge_nodes (
  id          TEXT PRIMARY KEY,          -- e.g., '3.1.3.1.2'
  parent_id   TEXT REFERENCES knowledge_nodes(id),
  node_type   ENUM('branch', 'subject', 'chapter', 'section', 'knowledge_point'),
  label_zh    TEXT NOT NULL,            -- 中文标签
  label_en    TEXT,                     -- 英文标签（用于索引）
  keywords    TEXT[],                   -- 搜索关键词数组
  domain_id   INT,                      -- 枝号 1-8
  agent_type  ENUM('L1','L2','L3','L4'), -- 该节点对应的 Agent 层级
  agent_id    TEXT,                     -- 对应的 Agent 实例 ID
  scope_docs  INT,                      -- 覆盖的文档/章节数
  created_at  TIMESTAMP,
  updated_at  TIMESTAMP
);

-- Agent 注册表
CREATE TABLE agent_registry (
  agent_id      TEXT PRIMARY KEY,
  agent_type    ENUM('L1','L2','L3','L4'),
  agent_name    TEXT NOT NULL,          -- e.g., '领域主编-中药'
  profile_name  TEXT NOT NULL,          -- Hermes profile 名称
  scope_nodes   TEXT[],                 -- 覆盖的知识节点 ID 列表
  toolsets      TEXT[],                 -- 启用的工具集
  soul_doc      TEXT,                   -- SOUL.md 内容
  status        ENUM('active','idle','offline'),
  last_active   TIMESTAMP
);

-- 知识路由日志
CREATE TABLE routing_log (
  id            SERIAL PRIMARY KEY,
  query_text    TEXT NOT NULL,
  parsed_entity TEXT,
  matched_node  TEXT REFERENCES knowledge_nodes(id),
  routed_agent  TEXT REFERENCES agent_registry(agent_id),
  confidence    FLOAT,                  -- 匹配置信度 0-1
  fallback_level INT,                   -- 0=精确, 1=L3, 2=L2, 3=L1
  response_time_ms INT,
  created_at    TIMESTAMP DEFAULT NOW()
);
```

---

## 四、六个开发阶段中 Cursor 3.0 如何构建此系统

### 阶段一：需求分析（Agent 建模）

> **目标：** 明确四种 Agent 的完整规格，建立知识树骨架。

| 步骤 | Cursor 功能 | 产出 |
|------|------------|------|
| 1. 编写 L1~L4 四种 Agent 的 SOUL.md 规格书 | **Composer** 批量生成 | `docs/agents/L1-industry-editor.md` ~ `L4-chapter-author.md` |
| 2. 定义八域知识边界 | **Chat + @Files** 交互讨论 → **Composer** 输出 | `docs/domain-boundaries.md`（8域 × 学科清单） |
| 3. 设计知识节点编码规则 | **Chat** 讨论方案 → **Composer** 生成编码生成器脚本 | `scripts/generate-node-ids.ts` |
| 4. 建立初始知识树骨架 | **Agent Mode** 批量生成 SQL 插入语句 | `prisma/seed.ts`（含全部 102 种教材的初始节点） |
| 5. 编写 Agent 路由算法伪代码 | **Composer** | `docs/router-algorithm.md` |

**Cursor 功能权重：** Composer 60% + Chat 30% + @Web 10%

### 阶段二：系统设计（Agent 基础设施）

> **目标：** 搭建四个 Agent 类型的技术基础设施。

| 步骤 | Cursor 功能 | 产出 |
|------|------------|------|
| 1. Prisma Schema 完整设计 | **Composer** 逐表生成 | `prisma/schema.prisma`（knowledge_nodes, agent_registry, routing_log 等 15+ 表） |
| 2. Agent Profile 模板生成 | **Agent Mode** 生成 4 个 Hermes Profile 的目录结构和配置 | `profiles/L1-chief/`, `profiles/L2-domain-XX/`, ... |
| 3. Agent 启动/管理 API 设计 | **Composer** | `docs/api/agent-api.md`（agent spawn, status, route, kill） |
| 4. 知识树 API 设计 | **Composer** | `docs/api/knowledge-tree-api.md`（CRUD + 搜索 + 路由） |
| 5. .cursorrules 建立（L1~L4 分级规范） | **写入文件** | 项目根 `.cursorrules` + `agents/L1.cursorrules` ~ `L4.cursorrules` |
| 6. Hermes Gateway 集成设计 | **Chat + @Web** | `docs/architecture/hermes-integration.md` |

**Cursor 功能权重：** Composer 50% + Agent Mode 20% + Chat 20% + .cursorrules 10%

### 阶段三：编码实现（分批构建）

> **目标：** 按 Agent 类型自底向上实现，L4→L3→L2→L1。

#### 批次 3.1：知识树数据库（基础）

| 步骤 | Cursor 功能 |
|------|------------|
| 知识节点 CRUD API | **Agent Mode** — `src/app/api/nodes/` |
| 树状结构遍历（父子查询 + 路径解析） | **Agent Mode** |
| 全文搜索索引（PostgreSQL tsvector + 中文分词） | **Agent Mode + @Web** |
| 节点编码自动生成器 | **Composer** |
| 初始种子数据（102 种教材 × N 章） | **Agent Mode** 批量生成 seed.ts |

#### 批次 3.2：Agent 注册与生命周期管理

| 步骤 | Cursor 功能 |
|------|------------|
| Agent Registry CRUD | **Agent Mode** |
| Hermes Profile 模板引擎（根据 Agent 类型自动生成 config.yaml + SOUL.md） | **Composer** |
| Agent 启动器（调用 Hermes CLI spawn） | **Agent Mode + Terminal** |
| Agent 状态监控（心跳检测 + 超时下线） | **Agent Mode** |

#### 批次 3.3：知识路由引擎（核心）

| 步骤 | Cursor 功能 |
|------|------------|
| 查询解析器（NLP 实体识别 + 关键词提取） | **Agent Mode** |
| 树状匹配器（节点编码匹配 + 模糊上溯） | **Agent Mode** |
| 路由分发器（选定 Agent → 构造 Prompt → 调用） | **Agent Mode** |
| 降级策略（L4 不可用 → L3 → L2 → L1） | **Inline Chat** 逐段精细调优 |
| 路由日志与置信度评分 | **Agent Mode** |

#### 批次 3.4：四个 Agent 类型的差异化实现

| Agent 类型 | 重点开发内容 | Cursor 功能 |
|-----------|------------|------------|
| **L4 章节作者** | Markdown 编辑器集成、知识点标注、引用管理 | **Agent Mode**（页面组件 + API） |
| **L3 学科主编** | 章节审核工作台、术语一致性检查、版本对比 | **Agent Mode**（审核 UI + 校验引擎） |
| **L2 领域主编** | 跨学科对比视图、领域统计仪表盘、批量审核 | **Composer**（复杂页面的多文件联动） |
| **L1 行业主编** | 全局合规面板、安全扫描、跨域仲裁工作台 | **Chat + Agent Mode**（规范→代码的精准翻译） |

#### 批次 3.5：Web 前端界面

| 步骤 | Cursor 功能 |
|------|------------|
| 知识树可视化（D3.js / React Flow 渲染一干八枝） | **Agent Mode** |
| Agent 控制面板（查看/启动/停止各 Agent） | **Agent Mode** |
| 知识点搜索框（输入查询 → 显示路由结果 → 展示专家回答） | **Agent Mode + Inline Chat** |
| 审核工作台（分层级的审核界面） | **Composer**（多页面联动） |

**Cursor 功能权重（阶段三）：** Agent Mode 45% + Composer 20% + Inline Chat 20% + Tab 10% + Chat 5%

### 阶段四：测试验证（分级测试）

| 测试类型 | Cursor 功能 | 测试内容 |
|---------|------------|------|
| **路由准确性测试** | **Agent Mode** 生成 500 条测试用例 | 输入"麻黄汤配伍"→ 期望路由到 L4-方剂学-解表剂-麻黄汤 |
| **降级策略测试** | **Agent Mode** | 模拟 L4 离线 → 验证自动上溯到 L3 |
| **Agent 工具集隔离测试** | **Bug Finder + Agent Mode** | 验证 L4 无法调用 delegation、L2 无法跨域 |
| **知识树完整性测试** | **Terminal** 运行校验脚本 | 检查 102 种教材的全部节点是否完整编码 |
| **端到端测试** | **Agent Mode** (Playwright) | 搜索 → 路由 → Agent 响应 → 展示结果 |

### 阶段五：部署上线

| 步骤 | Cursor 功能 |
|------|------------|
| 8 个 L2 领域主编 Profile 批量生成脚本 | **Agent Mode** |
| Hermes Gateway 配置（所有 Agent 接入同一 Gateway） | **Composer** |
| CI/CD（Agent 配置的热更新管道） | **Composer** |
| 监控仪表盘（各 Agent 状态、路由命中率、响应延迟） | **Agent Mode** |

### 阶段六：运维迭代

| 场景 | Cursor 功能 |
|------|------------|
| 新增教材 → 自动扩展知识树节点 → 创建新 Agent 实例 | **Agent Mode** |
| 路由日志分析 → 发现高频未命中查询 → 补充知识节点 | **Chat + @Files** |
| Agent 膨胀 → 拆分领域（枝9 从枝4 拆出） | **Composer**（多文件重构） |

---

## 五、Cursor 3.0 功能在四 Agent 开发中的差异化使用

| Cursor 功能 | L4 章节作者<br>(叶子节点) | L3 学科主编<br>(分支节点) | L2 领域主编<br>(枝节点) | L1 行业主编<br>(根节点) |
|------------|:--:|:--:|:--:|:--:|
| **Agent Mode** | ★★★ 主力 | ★★★ 主力 | ★★☆ | ★☆☆ |
| **Composer** | ★☆☆ | ★★☆ | ★★★ | ★★★ |
| **Inline Chat** | ★★★ | ★★★ | ★★☆ | ★☆☆ |
| **Tab 补全** | ★★★ | ★★☆ | ★☆☆ | ☆☆☆ |
| **Chat + @Files** | ★☆☆ | ★★☆ | ★★★ | ★★★ |
| **Chat + @Codebase** | ☆☆☆ | ★☆☆ | ★★☆ | ★★★ |
| **Bug Finder** | ★★☆ | ★★★ | ★★☆ | ★★☆ |
| **@Web** | ★★☆ | ★★☆ | ★★★ | ★★★ |
| **Terminal** | ★★☆ | ★★☆ | ★★☆ | ★★☆ |

> 趋势：越靠近叶子（L4），越依赖 **Agent Mode + Tab + Inline Chat** 的快速编码；越靠近根（L1），越依赖 **Chat + Composer** 的全局审视。

---

## 六、完整运行示例：一条知识查询的旅程

```
┌─────────────────────────────────────────────────────────────────┐
│ 用户输入：                                                       │
│ "麻黄汤中桂枝的作用是什么？它与麻黄如何协同？"                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: 知识解析器                                                │
│   entities: [麻黄汤, 桂枝, 麻黄]                                  │
│   intent: 配伍分析                                                │
│   domain_hint: 方剂 (关键词"汤"、"配伍"、"协同")                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: 树状索引查找                                              │
│   搜索 knowledge_nodes WHERE keywords @> ARRAY['麻黄汤']          │
│   → node_id = '3.1.3.1.2'                                        │
│     (枝3/方剂域 → 方剂学 → 第3章解表剂 → 第1节辛温解表 → 麻黄汤)  │
│   → 关联 agent_registry → agent_id = 'L4-formula-mahuang-tang'   │
│   → agent 在线，status=active，confidence=0.97                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: 路由到 Agent                                              │
│   加载 Hermes Profile: 'L4-formula-mahuang-tang'                  │
│   注入上下文:                                                      │
│     - 当前草稿: drafts/formula/ch03-mahuang-tang.md               │
│     - 历史评阅意见: reviews/ch03-review-20250620.md                │
│     - 方剂学总论配伍原则: drafts/formula/ch01-principles.md        │
│   发送 Prompt: "你是《方剂学》第3章第1节麻黄汤的章节作者。请解答：  │
│                麻黄汤中桂枝的作用及其与麻黄的协同机制。"             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Agent 响应                                                │
│   L4 章节作者（麻黄汤知识点）回复：                                │
│                                                                   │
│   "麻黄汤出自《伤寒论》，由麻黄、桂枝、杏仁、甘草组成。            │
│   桂枝在方中为臣药，其作用有三：                                   │
│   1. 助麻黄发汗解表 — 麻黄开腠理发汗，桂枝温经通阳，                │
│      二药相须为用，增强发汗之力；                                   │
│   2. 温经散寒 — 桂枝辛甘温，通阳化气，                             │
│      可解肌表之寒凝，缓解头身疼痛；                                 │
│   3. 调和营卫 — 与麻黄一散一收，使汗出不致过猛。                   │
│                                                                   │
│   麻黄与桂枝的协同：麻黄主发散，开泄腠理；桂枝主温通，             │
│   助阳化气。二者一散一通，麻黄得桂枝则发汗之力倍增，                │
│   桂枝得麻黄则温通之效更著，共成辛温解表之峻剂。                   │
│                                                                   │
│   来源：《方剂学》第3章第1节，草稿 v3.2。                          │
│   审阅状态：已通过 L3 学科主编审核。"                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: 返回结果给用户 + 记录路由日志                              │
│   routing_log: query→node_id→agent→confidence→time                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 附录 A：四个 Agent 在 Hermes 中的实际配置示例

### L2 领域主编-中药 (Profile: `l2-domain-herb`)

```yaml
# ~/.hermes/profiles/l2-domain-herb/config.yaml
model:
  default: deepseek-v4-pro
  provider: deepseek

agent:
  max_turns: 120

tools:
  enabled:
    - file
    - web
    - terminal
    - kanban
    - delegation
    - session_search
  disabled:
    - image_gen
    - tts

memory:
  memory_enabled: true
  user_profile_enabled: false
```

```markdown
# ~/.hermes/profiles/l2-domain-herb/SOUL.md

你是「中药域」领域主编，负责中药域下 14 种教材的学术质量。
你的知识域覆盖：中药学、中药炮制学、中药药理学、中药鉴定学、
药用植物学、中药化学、中药制剂学、临床中药学、中药资源学、
中药分析学、中药栽培学、民族药学、海洋中药学、中药新药研发。

你精通中药的四气五味、升降浮沉、归经、毒性、配伍禁忌（十八反十九畏）。
你关注跨学科术语一致性——"药性"在中药学、药理学、临床中药学中
的定义必须统一。

你可以：
- 向学科主编下发审核任务
- 审查本域内任意教材的任意章节
- 调用 web_search 检索最新中药研究成果

你不可：
- 跨域裁决（如审批针灸域内容）
- 直接修改章节内容（应通过学科主编下达修改指令）
```

### L4 章节作者-麻黄汤 (Profile: `l4-formula-mahuang-tang`)

```yaml
# ~/.hermes/profiles/l4-formula-mahuang-tang/config.yaml
model:
  default: deepseek-v4-pro

agent:
  max_turns: 60

tools:
  enabled:
    - file
    - web
    - terminal
  disabled:
    - delegation    # L4 不可委派
    - kanban        # L4 只领取任务，不管理看板
```

```markdown
# ~/.hermes/profiles/l4-formula-mahuang-tang/SOUL.md

你是《方剂学》第3章第1节「麻黄汤」知识点的章节作者。
你深度掌握麻黄汤的全部内容：方源（《伤寒论》）、组成（麻桂杏甘）、
用法、功用（发汗解表、宣肺平喘）、主治（外感风寒表实证）、
方解（君臣佐使）、配伍特点、临床应用、现代药理研究。

你维护的草稿位于：drafts/formula/ch03-section1-mahuang-tang.md
你引用的章节上下文包括：
- 第1章总论（配伍原则、剂型理论）
- 第3章概述（解表剂分类、辛温解表总论）

当收到知识查询时，你应：
1. 优先引用自己维护的草稿内容
2. 必要时检索最新文献补充
3. 标注信息来源和审阅状态
```

---

## 附录 B：推荐的 Cursor 工作区目录结构

```
tcm-agent-platform/
├── .cursorrules                          ← L1 级全局规则
├── .cursor/rules/
│   ├── L1-chief.mdc                      ← 行业主编开发规则
│   ├── L2-domain.mdc                     ← 领域主编开发规则
│   ├── L3-subject.mdc                    ← 学科主编开发规则
│   └── L4-author.mdc                     ← 章节作者开发规则
├── src/
│   ├── app/
│   │   ├── (search)/                     ← 知识点搜索页面
│   │   ├── (agent-panel)/                ← Agent 控制面板
│   │   ├── (review)/                     ← 分层审核工作台
│   │   └── api/
│   │       ├── knowledge/                ← 知识树 API
│   │       │   ├── nodes/
│   │       │   ├── search/
│   │       │   └── route/
│   │       └── agents/                   ← Agent 管理 API
│   │           ├── registry/
│   │           ├── spawn/
│   │           └── status/
│   ├── lib/
│   │   ├── knowledge-tree/               ← 知识树引擎
│   │   │   ├── parser.ts                 ← 查询解析
│   │   │   ├── matcher.ts                ← 节点匹配
│   │   │   └── encoder.ts                ← 节点编码
│   │   ├── agent-router/                 ← Agent 路由
│   │   │   ├── router.ts                 ← 路由分发
│   │   │   ├── fallback.ts               ← 降级策略
│   │   │   └── hermes-client.ts          ← Hermes CLI 客户端
│   │   └── agent-profiles/               ← Agent Profile 模板引擎
│   │       ├── L1-template.ts
│   │       ├── L2-template.ts
│   │       ├── L3-template.ts
│   │       └── L4-template.ts
│   └── components/
│       ├── knowledge-tree/               ← 树状可视化组件
│       ├── agent-dashboard/              ← Agent 仪表盘
│       └── search/                       ← 搜索框 + 结果展示
├── agents/                               ← Agent 规格文档
│   ├── L1-industry-editor.md
│   ├── L2-domain-editor.md
│   ├── L3-subject-editor.md
│   └── L4-chapter-author.md
├── profiles/                             ← Hermes Profile 模板
│   ├── L1-chief/
│   │   ├── config.yaml
│   │   └── SOUL.md
│   ├── L2-domain-herb/
│   ├── L3-subject-formula/
│   └── L4-author-mahuang/
├── prisma/
│   └── schema.prisma                     ← knowledge_nodes + agent_registry + routing_log
├── tests/
│   ├── unit/router.test.ts
│   ├── unit/matcher.test.ts
│   ├── integration/agent-spawn.test.ts
│   └── e2e/knowledge-search.spec.ts
└── scripts/
    ├── seed-knowledge-tree.ts             ← 初始化 102 种教材的知识树
    ├── generate-agent-profiles.ts         ← 批量生成 Agent Profile
    └── validate-tree.ts                   ← 校验树结构完整性
```

---

> **文档版本：** v2.0（重设计版）  
> **设计日期：** 2025-06-25  
> **核心目标：** 知识点搜索 → 树状路由 → 精准定位专家 Agent  
> **架构特征：** 四类独立 Agent × 一干八枝树状结构 × 降级上溯路由
