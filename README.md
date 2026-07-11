# 🏥 中医中药病证单位教材编写平台

> **8 大院系 · 120 门学科 · ~134 种教材 · 四层架构 · CI/CD 人机互动**

---

## 一、项目概况

本项目是一个大规模、系统化的**中医药教材编写平台**，基于"病证单位"（西医分子靶点 × 中医证候场论）为最小编写原子，构建覆盖中医药高等教育全学科链路的教材体系。

### 八大院系（D01–D08）

| 领域 | 院系 | 学科数 | 教材数 | 编写轮次 |
|:---:|:----|:-----:|:-----:|:-------:|
| D01 | 🏛️ 中医学院 | 28 | 32 | 1–6 |
| D02 | 🌿 中药学院 | 20 | 24 | 1–5 |
| D03 | 📍 针灸学院 | 12 | 14 | 1–4 |
| D04 | ✋ 推拿学院 | 10 | 10 | 2–5 |
| D05 | 🦴 骨伤学院 | 12 | 14 | 2–5 |
| D06 | 👄 五官口腔学院 | 10 | 10 | 3–6 |
| D07 | 🤖 中医智能学院 | 14 | 16 | 2–6 |
| D08 | 📊 中医管理学院 | 14 | 14 | 3–6 |
| **合计** | — | **120** | **~134** | **6 轮次** |

### 四层架构（L1–L4）

```
L1  行业规划主编 ── 总体规划、标准制定、质量把控
  └── L2  领域主编 × 8 ── 各院系领域规范、学科框架
        └── L3  学科主编 × 40 ── 学科内容统筹、章节规划
              └── L4  章节作者 × 800 ── 病证单位编写（最小编写单元）
```

### 六阶段流程

1. **需求分析** → 2. **体系设计** → 3. **内容编写** → 4. **审核评阅** → 5. **教学应用** → 6. **修订迭代**

---

## 二、版本管理策略

### 分支模型

| 分支 | 用途 | 保护规则 |
|:----|:-----|:--------|
| `master` | 稳定发布分支 | 受保护，需 PR + CI 通过 |
| `develop` | 集成开发分支 | 日常合并目标 |
| `feature/<domain>-<topic>` | 功能/章节分支 | 如 `feature/D01-S01-yinyang` |
| `review/<domain>-<textbook>` | 审核分支 | 如 `review/D01-CM-10` |
| `hotfix/<issue>` | 紧急修复 | 如 `hotfix/frontmatter-validation` |

### 提交规范

```
<类型>(<范围>): <简短描述>

类型: feat / fix / docs / review / style / refactor / chore
范围: D01–D08 / S01–S28 / CM-01… 等
```

**示例：**
- `feat(D01-S01): 完成阴阳学说第一章初稿`
- `review(D02): 中药鉴定学全篇内容审核`
- `fix(domain-specs): 修正 DOMAIN_SPEC_D03 轮次编号`

### 版本号规则

遵循语义化版本 `v<主>.<次>.<补>`：
- **主版本**：教材体系结构变更
- **次版本**：内容章节增删改
- **补丁版本**：勘误、格式修正

---

## 三、CI/CD 人机互动流程

本平台采用 **Hermes Agent（AI 原始编写）→ 人类三方审核** 的人机互动模式。

### 工作流概览

```
┌─────────────────────────────────────────────────────┐
│                   推送 / PR                          │
│                        │                            │
│               ┌────────┴────────┐                   │
│               ▼                 ▼                    │
│        ┌────────────┐   ┌──────────────┐            │
│        │ 质量检查    │   │ Frontmatter  │            │
│        │ Markdown    │   │ 域规范校验   │            │
│        │ JSON 摘要   │   │ 差异检查     │            │
│        └──────┬─────┘   └──────┬───────┘            │
│               └────┬──────────┘                     │
│                    ▼                                │
│          ┌──────────────────┐                       │
│          │ 生成审核清单     │  ← workflow_dispatch   │
│          │ 标记审核状态     │                       │
│          └──────────────────┘                       │
│                    │                                │
│                    ▼                                │
│          ┌──────────────────┐                       │
│          │ 人类三方审核     │                       │
│          │ ① 编委审稿       │                       │
│          │ ② 同行评议       │                       │
│          │ ③ 学生代表审读   │                       │
│          └──────────────────┘                       │
│                    │                                │
│                    ▼                                │
│          ┌──────────────────┐                       │
│          │ 修订迭代         │                       │
│          │ 每日进度报告     │  ← cron 定时           │
│          └──────────────────┘                       │
└─────────────────────────────────────────────────────┘
```

### CI/CD 工作流说明

#### 1. `tcm-ci-cd.yml` — 主 CI/CD 流水线

| 触发条件 | 执行内容 |
|:---------|:---------|
| **推送至 `master`** | Markdown 语法检查、文件 JSON 摘要生成、评论式推送摘要 |
| **Pull Request** | 文档变更差异检查、领域规范（domain-specs）Frontmatter 元数据完整性校验 |
| **每日 UTC 08:00** | 基于看板数据生成项目进度报告并发布 Issue |
| **`workflow_dispatch`** | 手动触发任意步骤 |

#### 2. `tcm-human-review.yml` — 人机互动审核工作流

| 参数 | 说明 |
|:----|:-----|
| `department` | 院系领域（D01–D08 或全部） |
| `textbook_id` | 教材编号（如 CM-01） |
| `review_type` | 审核类型：`content`（内容）/ `technical`（技术）/ `pedagogical`（教学）/ `full`（全面） |
| `reviewer_role` | 审核角色：`author`（作者）/ `editor`（主编）/ `domain-lead`（领域主编）/ `peer`（同行）/ `student`（学生） |

---

## 四、如何贡献与审核

### 贡献流程

1. **Fork 本仓库** 或创建功能分支
2. 在对应院系目录下编写或修改教材内容
3. 提交 PR 到 `develop` 分支
4. CI 自动执行：
   - ✅ Markdown 语法检查
   - ✅ Frontmatter 完整性校验
   - ✅ 文档差异审查
5. PR 通过后合并至 `develop`，定期发版至 `master`

### 审核流程

1. **领域主编** 通过 `workflow_dispatch` 触发人机互动审核
2. CI 自动生成**审核清单**（含审核项表格 + 待审文件清单）
3. 下载产物 `tcm-review-checklist` 中的 `review-checklist.md`
4. 逐项审核并标记：
   - ✅ 通过 / ✏️ 需修改 / ⏭️ 不适用
5. 填写审核结论，提交审阅意见至对应 PR

### 内容编写规范

- 使用 **Markdown** 格式，遵循 [GFM 规范](https://github.github.com/gfm/)
- 每章以 `# 第 X 章 标题` 开头，含学习目标表格
- 文件命名规则：`chapter-XX-英文标题-v1.md`
- 图片资源存放于 `assets/` 目录
- 参考文献采用脚注格式 `[^ref_id]`

---

## 五、项目结构

```
textbook-project/
├── .github/workflows/
│   ├── tcm-ci-cd.yml          # 主 CI/CD 流水线
│   └── tcm-human-review.yml   # 人机互动审核工作流
├── domain-specs/
│   ├── DOMAIN_SPEC_D01.md     # 中医学院领域规范
│   ├── DOMAIN_SPEC_D02.md     # 中药学院领域规范
│   ├── …                      # D03–D08
│   └── DOMAIN_INDEX.md        # 领域索引总表
├── drafts/                    # 各学科章节草稿
│   ├── D01-S01/               # 中医学院-学科01
│   ├── D22-S01/               # 中医智能-学科01
│   └── …
├── reviews/                   # 审核记录
├── feedback/                  # 反馈汇总
├── archive/                   # 归档文件
├── assets/                    # 资源文件（图片等）
├── scripts/
│   └── github-push.sh         # GitHub 一键推送脚本
├── sample-chapters/           # 样章示例
├── subject-outlines/          # 学科大纲
├── chapter-templates/         # 章节模板
├── dashboard/                 # 项目看板 / 仪表盘
├── SERIES_102_PLAN.md         # 102系列教材规划
├── ARCHITECTURE_FOUR_LAYER.md # 四层架构说明
├── KANBAN_SOFTWARE_ENGINEERING.md  # 看板与软件工程方法
└── PROJECT.md                 # 项目元信息
```

---

## 六、相关链接

| 资源 | 链接 |
|:----|:-----|
| 📦 **GitHub 仓库** | [github.com/beijingcdy/tcm-textbook-series](https://github.com/beijingcdy/tcm-textbook-series) |
| 📊 **在线看板** | [项目看板 · GitHub Projects](https://github.com/beijingcdy/tcm-textbook-series/projects) |
| 📈 **CI/CD 流水线** | [Actions · Workflows](https://github.com/beijingcdy/tcm-textbook-series/actions) |
| ☁️ **云端部署** | [TCM Dashboard (Cloud Server)](https://tcm-textbook-dashboard.example.com) |
| 📖 **编写指南** | 详见 `ARCHITECTURE_FOUR_LAYER.md` |
| 📋 **领域规范索引** | 详见 `DOMAIN_INDEX.md` |

---

## 七、技术栈

| 领域 | 技术 |
|:----|:-----|
| **版本控制** | Git + GitHub |
| **CI/CD** | GitHub Actions |
| **AI 编写助手** | Hermes Agent @ Nous Research |
| **文档格式** | Markdown (GFM) |
| **看板管理** | GitHub Projects (KANBAN) |
| **数据管理** | JSON + Excel |
| **部署** | 云服务器（Dashboard） |

---

> **维护者**：beijingcdy · **AI 协助**：Hermes Agent @ Nous Research
> **协议**：本项目内容遵循 CC-BY-NC 4.0 协议
> **最后更新**：2026-07-11
