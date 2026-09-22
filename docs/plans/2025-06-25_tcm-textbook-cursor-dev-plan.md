# 中医中药教材编写网络软件服务 — Cursor 3.0 开发规划

> **目标：** 使用 Cursor 3.0 开发「中医中药教材协作编写平台」Web 应用，贯穿四层审核 Agent 体系（行业主编→领域主编→学科主编→章节作者），覆盖软件工程六个阶段。

**技术栈预设：** Next.js 14+ / TypeScript / Prisma / PostgreSQL / TipTap 编辑器 / NextAuth.js

**四层 Agent 审核体系：**

| 层级 | 角色 | Cursor 中的映射载体 | 职责 |
|:--:|------|-------------------|------|
| L1 | **行业主编** | `.cursorrules`（项目根） | 全局编码规范、TCM 领域规则、安全策略、API 设计标准 |
| L2 | **领域主编** | `domain/{name}/.cursorrules` + `@domain/{name}/DOMAIN.md` | 领域模块架构、数据库 Schema 审核、接口协议一致性 |
| L3 | **学科主编** | Agent Mode（模块级） + Inline Chat 精细编辑 | 具体模块/功能点的实现审核、代码质量把关 |
| L4 | **章节作者** | Composer + Tab + Agent Mode（功能级） | 具体编写：页面组件、API 路由、数据库迁移、测试 |

---

## 阶段一：需求分析（Requirements Analysis）

> **目标：** 产出 PRD、用户故事地图、功能清单、四层角色权限矩阵。

### Cursor 3.0 功能穿插

| 步骤 | Cursor 功能 | 操作方式 | 涉及 Agent 层 |
|------|------------|---------|:-----------:|
| 1. 需求调研与竞品分析 | **Chat + @Web** | `@Web 调研现有在线协作文档编辑平台的技术方案` | L1 |
| 2. 用户故事生成 | **Composer** | 逐模块提示生成用户故事卡片，输出到 `docs/user-stories/` | L1→L2 |
| 3. 权限矩阵设计 | **Inline Chat (Ctrl+K)** | 选中草稿表 → "按四层角色补充 CRUD 权限" | L1→L2 |
| 4. 功能清单汇总 | **Composer** | 将所有用户故事汇总为 `docs/features.md` 功能清单 | L1 |
| 5. PRD 编写 | **Composer** | 分章节生成 PRD（背景→目标→范围→非目标→里程碑） | L1 |
| 6. 需求评审 | **Chat + @Files** | `@docs/PRD.md 从技术可行性角度逐条评审需求` | L2（领域主编介入） |

### 四层 Agent 在此阶段的分工

```
行业主编 (L1)：审批最终 PRD，制定 .cursorrules 规范框架
领域主编 (L2)：拆分功能模块归属（基础平台 / 中医基础域 / 中药域 / 方剂域 / 临床域）
学科主编 (L3)：评估各模块技术可行性
章节作者 (L4)：本阶段暂不介入
```

### 产出物

```
docs/
├── PRD.md                    # 产品需求文档
├── user-stories/             # 用户故事卡片
│   ├── auth.md
│   ├── editor.md
│   ├── review-workflow.md
│   └── export.md
├── features.md               # 功能清单（带优先级）
├── role-matrix.md            # 四层权限矩阵
└── tech-feasibility.md       # 技术可行性评估（L2/L3 输出）
```

---

## 阶段二：系统设计（System Design）

> **目标：** 产出技术架构图、数据库 ER 图、API 文档、组件树、路由设计。

### Cursor 3.0 功能穿插

| 步骤 | Cursor 功能 | 操作方式 | 涉及 Agent 层 |
|------|------------|---------|:-----------:|
| 1. 技术架构设计 | **Chat + @Web** | `@Web 对比 Next.js App Router 与 Pages Router 在协作编辑场景的优劣` | L1 |
| 2. 数据库 Schema 设计 | **Composer** | 逐领域生成 Prisma Schema → `prisma/schema.prisma` | L2（领域主编主导） |
| 3. API 路由规划 | **Composer** | 按 RESTful 规范生成 API 路由骨架 → `docs/api/` | L2→L3 |
| 4. 四层审核状态机设计 | **Chat + Composer** | 讨论状态流转 → Composer 输出状态图代码 | L1→L2→L3 |
| 5. 组件树设计 | **Composer** | 生成 React 组件树 → `docs/architecture/component-tree.md` | L3 |
| 6. .cursorrules 正式建立 | **写入文件** | 写入项目根 .cursorrules，覆盖 L1 级全部规范 | L1 |
| 7. 领域级规则建立 | **写入文件** | `domain/{name}/.cursorrules` 各领域独立规则 | L2 |
| 8. 原型/线框图 | **Composer + 代码生成** | 用 React + Tailwind 生成可点击的低保真原型 | L3→L4 |

### 四层 Agent 在此阶段的分工

```
行业主编 (L1)：
  ├── 确立 .cursorrules 核心规范（命名、目录结构、Git 规范、安全红线）
  ├── 审批总体技术架构
  └── 制定跨领域 API 协议标准

领域主编 (L2)：
  ├── 各领域独立 Schema 设计（user-domain, textbook-domain, review-domain...）
  ├── 领域内 API 路由规划
  └── domain/{name}/.cursorrules 撰写

学科主编 (L3)：
  ├── 组件树与页面路由设计
  ├── 状态管理方案选型（Zustand vs Jotai vs Context）
  └── 审核领域主编的 Schema 设计（交叉审查）

章节作者 (L4)：
  └── 原型页面实现（可点击低保真原型，后续可直接演进为正式代码）
```

### .cursorrules 四层体系设计

```
project-root/
├── .cursorrules                    ← L1：行业主编级全局规则
│   ├── 项目概述与 TCM 领域知识
│   ├── 命名规范（文件/变量/数据库）
│   ├── TypeScript 严格模式要求
│   ├── API 设计规范（RESTful + 错误码体系）
│   ├── 安全红线（XSS/CSRF/注入防护）
│   └── Git 提交规范（Conventional Commits）
│
├── domain/
│   ├── auth/.cursorrules           ← L2：认证授权领域规则
│   ├── textbook-core/.cursorrules  ← L2：教材核心领域规则
│   ├── review/.cursorrules         ← L2：审核工作流领域规则
│   └── export/.cursorrules         ← L2：导出/发布领域规则
│
└── modules/
    ├── editor/.cursorrules         ← L3：编辑器模块规则（TipTap 扩展规范）
    ├── diff-viewer/.cursorrules    ← L3：版本对比模块规则
    └── kanban/.cursorrules         ← L3：看板模块规则
```

### 产出物

```
docs/
├── architecture/
│   ├── system-architecture.md      # 系统架构图 + 技术选型说明
│   ├── component-tree.md           # React 组件树
│   ├── route-design.md             # Next.js App Router 路由设计
│   └── state-management.md         # 状态管理方案
├── api/
│   ├── auth-api.md
│   ├── textbook-api.md
│   ├── review-api.md
│   └── export-api.md
├── database/
│   └── er-diagram.md               # ER 图 + 表结构说明
└── workflow/
    └── review-state-machine.md     # 四层审核状态机设计
```

---

## 阶段三：编码实现（Implementation）

> **目标：** 按领域/模块分批实现全部功能，每个模块经历 L4→L3→L2→L1 递进式开发与审核。

### 核心策略：逐层递进开发

```
章节作者(L4) → 学科主编(L3) → 领域主编(L2) → 行业主编(L1)
  写代码         审核模块       审核领域       最终审批
```

### Cursor 3.0 功能穿插（迭代周期内）

每个功能模块遵循统一的 Red-Green-Refactor 节奏：

| 步骤 | Cursor 功能 | 操作方式 | Agent 层 |
|------|------------|---------|:-------:|
| **Sprint 启动** | | | |
| 1. 拆分任务 | **Chat** | `@docs/features.md 将编辑器模块拆分为可独立开发的任务` | L2→L3 |
| 2. 生成任务卡片 | **Composer** | 输出到 `docs/sprints/sprint-N.md` | L3 |
| **开发阶段** | | | |
| 3. 搭建模块骨架 | **Agent Mode** | "在 `src/app/(editor)/` 下搭建 TipTap 编辑器页面，含路由、layout、loading、error 边界" | L4 |
| 4. 实现核心逻辑 | **Agent Mode** | "实现四层审核状态流转的 Prisma 模型 + API 路由" | L4 |
| 5. 精细调校 | **Inline Chat (Ctrl+K)** | 选中组件 → "将审核按钮改为受角色权限控制" | L4 |
| 6. 补全胶水代码 | **Tab 补全** | 自然触发：导入语句、类型注解、样板代码 | L4 |
| **审核阶段** | | | |
| 7. 模块级审核 | **Chat + @Files** | `@src/modules/editor/ 审查编辑器模块是否符合 L3 规范` | L3 |
| 8. 领域级审核 | **Chat + @Folder** | `@domain/textbook-core/ 审查教材核心域各模块一致性` | L2 |
| 9. 全局合规审查 | **Chat + @Codebase** | `@codebase 检查是否存在违反 .cursorrules 安全红线的代码` | L1 |
| 10. 修复与合入 | **Agent Mode** | "根据审核意见逐一修复，PR 合并" | L4 |

### 开发批次规划（建议顺序）

```
批次 1：基础设施（Batch 0）
├── 项目脚手架（Next.js + TypeScript + Prisma + Tailwind）
├── 认证系统（NextAuth.js + 四角色模型）
├── 基础 UI 组件库（Button, Modal, Table, Form...）
├── 文件上传服务（章节草稿/图片/附件）
└── API 基础框架（错误处理中间件、分页、过滤、排序）

批次 2：教材编辑器域（MVP 核心）
├── TipTap 富文本编辑器集成（含 TCM 术语自动补全）
├── 章节草稿 CRUD + 自动保存
├── 版本管理（修改历史 → Diff 对比）
├── 四层审核状态机（提交→L3审核→L2审核→L1终审）
└── 评论/批注系统（行内标注）

批次 3：审核工作流域
├── Kanban 看板（Backlog → Writing → Review → Done）
├── 审核报告模板与生成
├── 通知系统（任务分配、审核提醒、截止预警）
└── 审核统计仪表盘

批次 4：教材管理域
├── 教材系列管理（102种教材元数据）
├── 四层级教学场景编排（本/硕/博/博后）
├── 编写轮次自动生成（拓扑排序）
└── 导入/导出（Markdown ↔ Word/PDF/LaTeX）

批次 5：协作与反馈域
├── 使用反馈收集（教师/学生双视角）
├── 反馈数据聚合与可视化
├── 实时协作（可选：Y.js 集成）
└── 通知邮件/站内信

批次 6：管理与运维
├── 用户与权限管理后台
├── 操作日志与审计
├── 数据备份与恢复
└── 系统配置面板
```

### Cursor 功能在开发阶段的使用权重

```
Agent Mode    ████████████████████ 40%  ← 主力：模块搭建、批量代码生成
Tab 补全      ████████████ 25%        ← 胶水代码、样板代码、导入语句
Inline Chat   ██████████ 20%          ← 精细修改：单一函数/组件的重构
Chat + @Files ██████ 10%              ← 跨文件理解：上下文问答、审核
Composer      █████ 5%                ← 多文件联动修改（重构阶段）
```

---

## 阶段四：测试验证（Testing & QA）

> **目标：** 各层级的全面测试，从单元→集成→E2E，结合四层 Agent 的分级审核。

### Cursor 3.0 功能穿插

| 步骤 | Cursor 功能 | 操作方式 | Agent 层 |
|------|------------|---------|:-------:|
| 1. 生成单元测试 | **Agent Mode** | "为 `src/lib/review-state-machine.ts` 生成完整的单元测试，覆盖所有状态转换" | L4 |
| 2. 补充边界用例 | **Inline Chat** | 选中测试文件 → "补充空值、超长字符串、并发冲突的边界测试" | L3 |
| 3. 生成集成测试 | **Agent Mode** | "生成审核流程的端到端 API 集成测试：提交→L3驳回→修改→重新提交→L3通过→L2审核" | L4 |
| 4. E2E 测试 | **Agent Mode + @Web** | "用 Playwright 生成教材编辑→提交审核→审批通过→导出的完整流程 E2E 测试" | L4 |
| 5. Bug 扫描 | **Bug Finder** | 对关键模块启动 AI Bug 检测 | L3 |
| 6. 测试报告审核 | **Chat + @Files** | `@tests/ 审查测试覆盖率，识别缺失的测试场景` | L2 |
| 7. 性能测试 | **Terminal** | `k6 run load-test.js` 结合 Chat 分析结果 | L1 |

### 四层 Agent 的测试职责

```
章节作者 (L4)：编写单元测试 + 集成测试 + E2E 测试
学科主编 (L3)：审查测试覆盖率和边界用例完整性
领域主编 (L2)：审查跨模块集成测试的正确性
行业主编 (L1)：审批性能测试报告 + 安全渗透测试结果
```

### 测试分层策略

```
┌─────────────────────────────────────────┐
│            E2E Tests (Playwright)        │  ← 10%：关键业务路径
├─────────────────────────────────────────┤
│        Integration Tests (Jest)          │  ← 30%：API + 数据库 + 状态机
├─────────────────────────────────────────┤
│         Unit Tests (Vitest)              │  ← 60%：纯函数、组件、hooks
└─────────────────────────────────────────┘
```

### Cursor 在测试阶段的专项用法

```bash
# 1. Agent Mode 批量生成测试
"为 src/app/api/ 下所有 API 路由生成集成测试，使用 MSW mock"

# 2. Bug Finder 主动扫描
在 Cursor 中打开关键文件 → 右键 "Find Bugs" → AI 自动标注可疑代码

# 3. Inline Chat 快速修复
选中测试中失败的断言 → Ctrl+K → "修复这个断言逻辑使其符合最新 API 返回格式"

# 4. Chat 上下文问答
@src/lib/ @tests/ "为什么审核状态机的 integration test 在 CI 中偶发性失败？"
```

---

## 阶段五：部署上线（Deployment）

> **目标：** 生产环境部署、CI/CD 管道、监控告警、灰度发布。

### Cursor 3.0 功能穿插

| 步骤 | Cursor 功能 | 操作方式 | Agent 层 |
|------|------------|---------|:-------:|
| 1. Docker 化 | **Agent Mode** | "生成多阶段 Dockerfile + docker-compose.yml（Next.js + PostgreSQL + Redis）" | L4 |
| 2. CI/CD 配置 | **Composer** | 生成 GitHub Actions 工作流（lint→test→build→deploy） | L4 |
| 3. 环境变量管理 | **Composer** | 生成 `.env.example` + 各环境配置模板 | L3 |
| 4. 部署脚本 | **Agent Mode** | "生成 Vercel/Railway 部署配置，含预览环境" | L4 |
| 5. 监控配置 | **Chat + @Web** | `@Web Sentry + Grafana 在 Next.js 中的最佳实践` | L2 |
| 6. 安全扫描 | **Chat + Agent Mode** | "扫描整个项目，生成安全加固清单" | L1 |
| 7. 灰度策略 | **Chat** | "设计基于四角色分批放量的灰度发布方案" | L1 |

### CI/CD 管道设计（Cursor 辅助生成）

```yaml
# .github/workflows/ci.yml — Cursor Agent Mode 可批量生成
name: CI Pipeline
on: [push, pull_request]
jobs:
  lint:       # ESLint + Prettier + TypeScript 类型检查
  test-unit:  # Vitest 单元测试
  test-e2e:   # Playwright E2E 测试
  security:   # CodeQL + 依赖审计
  build:      # Next.js 生产构建
  deploy-preview: # Vercel Preview（PR 环境）
  
# .github/workflows/deploy.yml — Cursor Composer 生成
name: Deploy Pipeline
on:
  push:
    branches: [main]
jobs:
  deploy-production:
    # 灰度发布：先 10% → 观察监控 → 100%
```

### L1 行业主编在部署阶段的最终审批清单

```markdown
## 上线前 L1 终审批次
- [ ] .cursorrules 全部安全红线通过检查
- [ ] 四角色权限模型正确实现（无越权风险）
- [ ] 数据库备份策略就绪
- [ ] API 限流与防滥用措施到位
- [ ] PII 数据处理符合合规要求
- [ ] 监控告警通道畅通（Sentry + Slack/飞书）
- [ ] 回滚方案已验证
```

---

## 阶段六：运维迭代（Maintenance & Iteration）

> **目标：** 持续收集反馈、修复缺陷、迭代功能，四层 Agent 进入"持续审核"模式。

### Cursor 3.0 功能穿插

| 场景 | Cursor 功能 | 操作方式 | Agent 层 |
|------|------------|---------|:-------:|
| 线上 Bug 修复 | **Chat + @Files + Agent Mode** | `@src/ 错误出现在审核状态机流转时，定位根因并修复` | L4→L3 审核 |
| 用户反馈驱动迭代 | **Chat + @Codebase** | "用户反馈：章节编辑器在移动端工具栏遮挡内容，搜索类似布局问题并修复" | L3→L4 |
| 架构小重构 | **Composer** | "将审核通知从轮询改为 WebSocket 推送"（多文件联动） | L3→L2 |
| 技术债务清理 | **Agent Mode** | "将 `src/lib/review.ts` 中的 3 处 any 类型改为严格类型" | L4 |
| 性能优化 | **Chat + Bug Finder** | "找出数据库查询中的 N+1 问题并批量修复" | L3 |
| 依赖升级 | **Agent Mode** | "将项目从 Next.js 14 升级到 15，处理 Breaking Changes" | L2 |
| 新功能提案 | **Chat + Composer** | "基于使用反馈数据，生成下一个迭代的功能优先级排序" | L1→L2 |

### 四层 Agent 在运维阶段的持续职责

```
行业主编 (L1)：
  ├── 每月审查 .cursorrules 是否需要更新
  ├── 审批重大架构变更
  └── 制定下季度技术路线图

领域主编 (L2)：
  ├── 每周审查负责领域的 Issue/PR
  ├── 维护领域级 .cursorrules
  └── 处理跨领域集成问题

学科主编 (L3)：
  ├── 每日 Code Review（利用 Chat + @Files 高效审查）
  ├── 维护模块级 .cursorrules
  └── 指导章节作者的实现方案

章节作者 (L4)：
  ├── 认领 Issue → 使用 Agent Mode 实现 → 提交 PR
  ├── 补充测试（利用 Agent Mode 快速补齐）
  └── 响应 Bug 修复（Chat 定位 + Agent Mode 修复）
```

### 迭代节奏建议

```
┌──────────────────────────────────────────────────┐
│  周一：Bug 清扫（L4 主导 + L3 审核）              │
│  周二-四：功能开发（L4 开发 → L3 审核 → L2 领域审 │
│  周五：周报 + 技术债务评估（L2 + L1）            │
│                                                   │
│  每月末：L1 发起全局架构审视 + .cursorrules 更新  │
│  每季度：大版本规划（L1→L2→L3→L4 逐层下发）     │
└──────────────────────────────────────────────────┘
```

---

## 附录 A：Cursor 3.0 功能在六阶段的总体使用矩阵

| Cursor 功能 | 阶段一<br>需求 | 阶段二<br>设计 | 阶段三<br>编码 | 阶段四<br>测试 | 阶段五<br>部署 | 阶段六<br>运维 |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Chat + @Files/@Codebase** | ★★★ | ★★★ | ★★☆ | ★★★ | ★★☆ | ★★★ |
| **Agent Mode** | ☆☆☆ | ★☆☆ | ★★★ | ★★★ | ★★☆ | ★★★ |
| **Composer** | ★★★ | ★★★ | ★☆☆ | ★☆☆ | ★★☆ | ★★☆ |
| **Inline Chat (Ctrl+K)** | ★★☆ | ★★☆ | ★★★ | ★★☆ | ☆☆☆ | ★★☆ |
| **Tab 补全** | ☆☆☆ | ☆☆☆ | ★★★ | ★☆☆ | ★☆☆ | ★☆☆ |
| **Bug Finder** | ☆☆☆ | ☆☆☆ | ★☆☆ | ★★★ | ★★☆ | ★★★ |
| **.cursorrules** | ★☆☆ | ★★★ | ★★★ | ★★☆ | ★★★ | ★★★ |
| **Terminal 集成** | ☆☆☆ | ☆☆☆ | ★★☆ | ★★★ | ★★★ | ★★☆ |
| **@Web** | ★★★ | ★★☆ | ★☆☆ | ★☆☆ | ★★☆ | ★☆☆ |
| **@Docs（外部文档）** | ★★☆ | ★★★ | ★★☆ | ★★☆ | ★★★ | ★☆☆ |

> ★★★ = 核心依赖  ★★☆ = 高频使用  ★☆☆ = 辅助使用  ☆☆☆ = 基本不用

---

## 附录 B：四层 Agent 在 Cursor 中的实际操作示例

### L1 行业主编操作示例

```bash
# 建立 .cursorrules（在 Cursor 中直接编辑项目根 .cursorrules 文件）
# 内容示例：

## 项目概述
你正在开发「中医中药教材协作编写平台」，一个面向中医药高校的多角色协作文档编辑系统。

## 核心约束
- 所有面向用户的文案必须使用简体中文
- 数据库字段名使用 snake_case，TypeScript 变量使用 camelCase
- 任何 API 返回用户数据前必须经过角色权限过滤

## TCM 领域术语
- "教材" = textbook, "章节" = chapter, "审核" = review
- "行业主编" = editor_in_chief (role), "领域主编" = domain_editor
- "学科主编" = subject_editor, "章节作者" = chapter_author

## 安全红线（违反即阻塞合入）
1. 禁止在前端直接拼接 SQL 或暴露数据库结构
2. API 路由必须验证 JWT 并检查角色权限
3. 用户输入在渲染前必须经过 DOMPurify 清洗
4. 文件上传路径不得包含用户可控的文件名

# L1 审核命令示例（在 Cursor Chat 中执行）：
@codebase 扫描是否存在硬编码的 API 密钥或数据库密码
@src/app/api/ 审查所有 API 路由是否都包含角色权限校验中间件
```

### L2 领域主编操作示例

```bash
# domain/review/.cursorrules
## 审核工作流领域规则
- 状态机枚举值：DRAFT → SUBMITTED → L3_REVIEW → L2_REVIEW → L1_FINAL → APPROVED
- 任何状态变更必须写入 audit_log 表
- 驳回时必须附带驳回原因（reason 字段不可为空）

# L2 审核命令示例（在 Cursor Chat 中执行）：
@domain/review/ 审查所有审核相关 API 是否遵循状态机约束
@prisma/schema.prisma 审查 review 域的数据库表设计是否满足跨领域查询需求
```

### L3 学科主编操作示例

```bash
# 模块级审核 — 使用 Inline Chat (Ctrl+K)
# 选中编辑器组件代码 → 输入：
"为这个组件添加 TCM 术语自动补全功能，术语列表从 /api/terms 获取"

# 模块级审核 — 使用 Chat + @Folder
@src/modules/editor/ 审查 TipTap 编辑器扩展是否都正确处理了中文输入法组合输入
```

### L4 章节作者操作示例

```bash
# 使用 Agent Mode 实现功能
"在 src/app/(editor)/[textbookId]/[chapterId]/ 下实现章节编辑器页面：
 1. 使用 TipTap 富文本编辑器，工具栏包含：标题/加粗/斜体/列表/引用/批注
 2. 页面顶部显示章节标题（可编辑）+ 审核状态标签
 3. 底部有「保存草稿」和「提交审核」按钮
 4. 「提交审核」点击后调用 POST /api/review/submit，成功后状态变更为 SUBMITTED
 5. 使用 Tailwind CSS，响应式布局"

# 使用 Inline Chat 快速调整
# 选中「保存草稿」按钮的 onClick → Ctrl+K →
"添加防抖：2秒内连续点击只触发一次保存，同时显示'保存中…'状态"
```

---

## 附录 C：推荐的 Cursor 工作区结构

```
tcm-textbook-platform/
├── .cursorrules                          ← L1 全局规则
├── .cursor/
│   └── rules/                            ← Cursor 3.0 多规则文件目录
│       ├── tcm-domain-knowledge.mdc      ← L1：TCM 领域知识
│       ├── coding-standards.mdc          ← L1：编码规范
│       └── security.mdc                  ← L1：安全红线
├── src/
│   ├── app/                              ← Next.js App Router
│   │   ├── (auth)/                       ← 认证相关页面
│   │   ├── (dashboard)/                  ← 仪表盘
│   │   ├── (editor)/                     ← 编辑器
│   │   └── api/                          ← API 路由
│   ├── components/
│   │   ├── ui/                           ← 基础 UI 组件
│   │   ├── editor/                       ← 编辑器组件 → .cursorrules(L3)
│   │   └── review/                       ← 审核组件 → .cursorrules(L3)
│   ├── lib/
│   │   ├── auth/                         ← 认证逻辑 → domain/auth/.cursorrules
│   │   ├── review/                       ← 审核状态机 → domain/review/.cursorrules
│   │   └── tcm/                          ← TCM 术语/知识库
│   └── styles/
├── domain/
│   ├── auth/.cursorrules                 ← L2 认证领域规则
│   ├── textbook-core/.cursorrules        ← L2 教材核心领域规则
│   ├── review/.cursorrules               ← L2 审核工作流领域规则
│   └── export/.cursorrules               ← L2 导出领域规则
├── prisma/
│   └── schema.prisma
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                                 ← 全部设计文档
└── docker-compose.yml
```

---

## 附录 D：与现有 Hermes 多 Agent 体系的协同

本项目规划与已有的 Hermes 多 Agent 教材编写体系（textbook-workflow / textbook-review / textbook-writing / textbook-usage）**互补而非替代**：

| 维度 | Hermes 多 Agent | Cursor 3.0 本项目 |
|------|----------------|-------------------|
| **定位** | 教材内容的生产与审核（内容层） | 教材编写平台的软件开发（工具层） |
| **Agent** | textbook-writer / reviewer / user | L1-L4 四层开发审核 |
| **产物** | 教材 Markdown 草稿、评阅报告、使用反馈 | Web 应用代码、API、数据库 |
| **协作** | Kanban 看板 + Cron 定时 | Cursor Rules + PR Review |
| **关联** | 本平台是 Hermes 体系的可视化 Web 前端 | Hermes 仍可作为后端 AI 引擎 |

```
              ┌──────────────────────────┐
              │   Cursor 3.0 开发的      │
              │   Web 协作平台（本项目）  │ ← 工具层
              └──────────┬───────────────┘
                         │ 调用 API
              ┌──────────▼───────────────┐
              │   Hermes 多 Agent        │
              │   (textbook-* skills)    │ ← 内容层
              └──────────────────────────┘
```

---

> **文档版本：** v1.0  
> **生成日期：** 2025-06-25  
> **适用范围：** Cursor 3.0 + 中医中药教材编写 Web 服务项目全生命周期
