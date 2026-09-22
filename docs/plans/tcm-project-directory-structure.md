# 中医中药系列教材编写平台 — 项目结构目录

> **树形结构遵循「病证同存·一干八枝」组织原则，按四层 Agent 层级 + 六阶段工作流 + 七后端部署 + 120学科（8域×15门）展开。**

---

## 顶层结构

```
tcm-knowledge-tree/
│
├── README.md                           # 项目概述
├── .cursorrules                        # L1 行业主编全局规则
├── .cursor/
│   └── rules/
│       ├── L1-chief.mdc                # L1 编码规范
│       ├── L2-domain.mdc               # L2 领域规范
│       ├── L3-subject.mdc              # L3 学科规范
│       └── L4-author.mdc               # L4 编写规范
│
├── docs/                               # 📄 文档中心
│   ├── requirements.md                 #   项目需求分析
│   ├── architecture.md                 #   系统架构说明
│   ├── workflow-6phases.md             #   六阶段工作流定义
│   ├── cognitive-awakening.md          #   认知觉醒五阶段模型
│   ├── domain-mapping.md               #   八域→院系→岗位三层映射表
│   └── SERIES_102_PLAN.md              #   102种教材完整元数据
│
├── backends/                           # 🖥 七类终端后端配置
│   ├── local/
│   │   └── config.yaml                 #     本地执行配置
│   ├── docker/
│   │   ├── Dockerfile.agent            #     Agent 容器镜像
│   │   ├── docker-compose.agents.yml   #     批量 Agent 编排
│   │   └── config.yaml
│   ├── ssh/
│   │   ├── hosts.yaml                  #     远程服务器清单
│   │   └── config.yaml
│   ├── modal/
│   │   ├── agent_runner.py             #     Modal 函数定义
│   │   └── config.yaml
│   ├── daytona/
│   │   ├── workspace-template.yaml     #     工作空间模板
│   │   └── config.yaml
│   ├── singularity/
│   │   ├── agent.def                   #     Singularity 定义文件
│   │   └── config.yaml
│   └── managed_modal/
│       ├── production.yaml             #     生产环境配置
│       └── config.yaml
│
├── src/                                # 💻 源代码
│   ├── app/                            #   Next.js App Router
│   │   ├── (home)/                     #     首页（知识树总览 + 搜索入口）
│   │   ├── (tree)/                     #     知识树浏览与导航
│   │   │   ├── [branchId]/             #       枝1~枝8 领域视图
│   │   │   │   ├── [subjectId]/        #         学科视图
│   │   │   │   │   ├── [chapterId]/    #           章视图
│   │   │   │   │   │   └── [nodeId]/   #             知识点视图
│   │   ├── (search)/                   #     知识点搜索与路由结果
│   │   ├── (editor)/                   #     章节编辑器（L4工作区）
│   │   ├── (review)/                   #     审核工作台（L3/L2/L1）
│   │   │   ├── L3-subject/             #       L3学科主编审核
│   │   │   ├── L2-domain/              #       L2领域主编审核
│   │   │   └── L1-chief/               #       L1行业主编终审
│   │   ├── (dashboard)/                #     仪表盘（进度/统计）
│   │   ├── (admin)/                    #     管理后台（Agent/用户/权限）
│   │   └── api/                        #     API 路由
│   │       ├── knowledge/              #       知识树 API
│   │       │   ├── nodes/              #         节点 CRUD
│   │       │   ├── search/             #         知识点搜索
│   │       │   └── route/              #         节点路由
│   │       ├── agents/                 #       Agent 管理 API
│   │       │   ├── registry/           #         Agent 注册表
│   │       │   ├── spawn/              #         Agent 启动
│   │       │   └── status/             #         Agent 状态
│   │       ├── workflow/               #       工作流 API
│   │       │   ├── phases/             #         六阶段管理
│   │       │   └── tasks/              #         任务分发
│   │       ├── review/                 #       审核 API
│   │       └── export/                 #       导出 API
│   │
│   ├── lib/                            #   核心库
│   │   ├── knowledge-tree/             #     知识树引擎
│   │   │   ├── parser.ts               #       查询解析（NLP实体识别）
│   │   │   ├── matcher.ts              #       节点匹配（编码+关键词）
│   │   │   ├── encoder.ts              #       节点编码生成器
│   │   │   ├── traverser.ts            #       树遍历（父子/兄弟/路径）
│   │   │   └── types.ts                #       知识树类型定义
│   │   ├── agent-router/               #     Agent 路由引擎
│   │   │   ├── router.ts               #       路由分发主逻辑
│   │   │   ├── fallback.ts             #       降级策略（L4→L3→L2→L1）
│   │   │   ├── hermes-client.ts        #       Hermes CLI 客户端
│   │   │   └── types.ts                #       路由类型定义
│   │   ├── agent-profiles/             #     Agent Profile 模板引擎
│   │   │   ├── L1-template.ts          #       L1行业主编模板
│   │   │   ├── L2-template.ts          #       L2领域主编模板
│   │   │   ├── L3-template.ts          #       L3学科主编模板
│   │   │   └── L4-template.ts          #       L4章节作者模板
│   │   ├── workflow-engine/            #     六阶段工作流引擎
│   │   │   ├── phase-manager.ts        #       阶段状态机
│   │   │   ├── task-generator.ts       #       阶段任务自动生成
│   │   │   └── direction-controller.ts #       交互方向控制
│   │   ├── review-system/              #     审核系统
│   │   │   ├── state-machine.ts        #       审核状态机
│   │   │   ├── escalation.ts           #       驳回升级逻辑
│   │   │   └── report-template.ts      #       审核报告模板
│   │   ├── cognitive-engine/           #     认知觉醒引擎
│   │   │   ├── level-classifier.ts     #       认知层级分类（Bloom）
│   │   │   ├── content-adapter.ts      #       内容深度适配
│   │   │   └── stage-profile.ts        #       五阶段认知画像
│   │   ├── db/                         #     数据库客户端
│   │   │   ├── prisma.ts               #       Prisma 单例
│   │   │   └── search.ts               #       全文搜索（pg_trgm + jieba）
│   │   └── utils/                      #     工具函数
│   │
│   ├── components/                     #   React 组件
│   │   ├── ui/                         #     基础 UI（Button/Modal/Table）
│   │   ├── knowledge-tree/             #     知识树可视化
│   │   │   ├── TreeView.tsx            #       React Flow 完整树
│   │   │   ├── TreeNode.tsx            #       单节点组件
│   │   │   ├── TreeSearch.tsx          #       树内搜索
│   │   │   └── BranchBadge.tsx         #       枝标签（枝1~枝8）
│   │   ├── search/                     #     搜索组件
│   │   │   ├── SearchBar.tsx           #       搜索框
│   │   │   ├── SearchResult.tsx        #       搜索结果（含Agent信息）
│   │   │   └── RouteVisualizer.tsx     #       路由路径可视化
│   │   ├── editor/                     #     编辑器组件
│   │   │   ├── MarkdownEditor.tsx      #       TipTap 编辑器
│   │   │   ├── ChapterToolbar.tsx      #       章节工具栏
│   │   │   └── VersionDiff.tsx         #       版本对比
│   │   ├── review/                     #     审核组件
│   │   │   ├── ReviewPanel.tsx         #       审核面板（通用）
│   │   │   ├── L3ReviewChecklist.tsx   #       L3审核清单
│   │   │   ├── L2CrossCheck.tsx        #       L2跨学科对比
│   │   │   └── L1FinalSignoff.tsx      #       L1终审签批
│   │   ├── dashboard/                  #     仪表盘组件
│   │   │   ├── PhaseProgress.tsx       #       六阶段进度
│   │   │   ├── AgentStatusBoard.tsx    #       Agent状态面板
│   │   │   └── DomainStats.tsx         #       八域统计
│   │   ├── agent/                      #     Agent 管理组件
│   │   │   ├── AgentRegistry.tsx       #       Agent注册表视图
│   │   │   ├── AgentSpawner.tsx        #       Agent启动器
│   │   │   └── AgentLog.tsx            #       Agent运行日志
│   │   └── cognitive/                  #     认知觉醒组件
│   │       ├── StageIndicator.tsx      #       五阶段指示器
│   │       └── ContentDepthSlider.tsx  #       内容深度调节
│   │
│   └── styles/
│       └── globals.css
│
├── agents/                             # 🤖 Agent 规格定义
│   ├── L1-industry-editor.md           #   L1行业主编规格书
│   ├── L2-domain-editor.md             #   L2领域主编规格书
│   ├── L3-subject-editor.md            #   L3学科主编规格书
│   ├── L4-chapter-author.md            #   L4章节作者规格书
│   └── domains/                        #   八域分别定义
│       ├── branch-01-basic/
│       │   ├── DOMAIN.md               #     枝1·基础域定义
│       │   ├── TERMS.md                #     域内术语规范表
│       │   └── JOB-MAP.md              #     毕业生岗位映射
│       ├── branch-02-herb/             #     枝2·中药域
│       ├── branch-03-acupuncture/      #     枝3·针灸域
│       ├── branch-04-internal/         #     枝4·内科域
│       ├── branch-05-surgery/          #     枝5·外科域
│       ├── branch-06-integrative/      #     枝6·结合域
│       ├── branch-07-nursing/          #     枝7·护理域
│       └── branch-08-management/       #     枝8·管理域
│
├── profiles/                           # ⚙️ Hermes Agent Profiles
│   ├── L1-chief/                       #   L1行业主编 Profile
│   │   ├── config.yaml
│   │   └── SOUL.md
│   ├── L2-branch-01-basic/             #   枝1基础域 L2 Profile
│   ├── L2-branch-02-herb/              #   枝2中药域
│   ├── L2-branch-03-acupuncture/       #   枝3针灸域
│   ├── L2-branch-04-internal/          #   枝4内科域
│   ├── L2-branch-05-surgery/           #   枝5外科域
│   ├── L2-branch-06-integrative/       #   枝6结合域
│   ├── L2-branch-07-nursing/           #   枝7护理域
│   ├── L2-branch-08-management/        #   枝8管理域
│   ├── L3-template/                    #   L3学科主编 Profile 模板
│   │   ├── config.yaml
│   │   └── SOUL.md
│   └── L4-template/                    #   L4章节作者 Profile 模板
│       ├── config.yaml
│       └── SOUL.md
│
├── content/                            # 📝 教材内容（102种教材）
│   ├── branch-01-basic/                #   枝1·基础域
│   │   ├── subject-001-zhongji/        #     中医基础理论
│   │   │   ├── drafts/                 #       章节草稿
│   │   │   │   ├── ch01-intro.md
│   │   │   │   ├── ch02-yinyang.md
│   │   │   │   └── ...
│   │   │   ├── reviews/               #       审核报告
│   │   │   └── metadata.json          #       学科元数据
│   │   ├── subject-002-zhenduan/       #     中医诊断学
│   │   └── ...                         #     枝1共8个学科
│   ├── branch-02-herb/                 #   枝2·中药域
│   │   ├── subject-009-zhongyaoxue/    #     中药学
│   │   ├── subject-010-paozhi/         #     中药炮制学
│   │   └── ...                         #     枝2共14个学科
│   ├── branch-03-acupuncture/          #   枝3·针灸域
│   ├── branch-04-internal/             #   枝4·内科域
│   ├── branch-05-surgery/              #   枝5·外科域 (15学科)
│   ├── branch-06-tcm-ai/               #   枝6·中医智能学院 (15学科)
│   ├── branch-07-nursing/              #   枝7·护理域 (15学科)
│   └── branch-08-management/           #   枝8·管理域 (15学科)
│
├── feedback/                           # 📊 使用反馈
│   ├── teacher-feedback/               #   教师反馈
│   ├── student-feedback/               #   学生反馈
│   └── aggregation/                    #   反馈聚合报告
│
├── prisma/
│   ├── schema.prisma                   #   数据库 Schema
│   ├── migrations/                     #   迁移文件
│   └── seed.ts                         #   种子数据（初始化知识树）
│
├── scripts/                            # 🔧 工具脚本
│   ├── seed-knowledge-tree.ts          #   初始化完整知识树
│   ├── generate-agent-profiles.ts      #   批量生成 Agent Profiles
│   ├── validate-tree.ts                #   校验树结构完整性
│   ├── generate-node-ids.ts            #   节点编码生成器
│   └── export-knowledge-graph.ts       #   导出知识图谱
│
├── tests/                              # 🧪 测试
│   ├── unit/
│   │   ├── knowledge-tree/             #   知识树单元测试
│   │   ├── agent-router/               #   路由引擎单元测试
│   │   └── workflow-engine/            #   工作流引擎单元测试
│   ├── integration/
│   │   ├── api/
│   │   └── agent-spawn/                #   Agent启动集成测试
│   └── e2e/
│       └── knowledge-search.spec.ts    #   搜索→路由→响应 端到端
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      #   CI管道
│       └── deploy.yml                  #   部署管道
│
├── docker-compose.yml
├── Dockerfile
├── package.json
├── tsconfig.json
├── next.config.ts
└── tailwind.config.ts
```

---

## 关键目录说明

### `src/lib/knowledge-tree/` — 知识树引擎

```
parser.ts     : 接收自然语言查询 → 提取实体和意图 → 生成搜索向量
matcher.ts    : 在知识树中匹配节点 → 返回匹配度排序
encoder.ts    : 生成节点唯一编码（如 3.1.3.1.2）
               编码规则：枝号.学科号.章号.节号.知识点序号
traverser.ts  : 树遍历操作（父/子/兄弟/路径/子树）
```

### `src/lib/agent-router/` — Agent 路由引擎

```
router.ts     : 接收节点匹配结果 → 查找对应Agent → 构造Prompt
fallback.ts   : L4不在线 → 上溯到L3 → 上溯到L2 → 上溯到L1
hermes-client.ts : 调用 Hermes CLI 启动/查询 Agent
```

### `profiles/` — Hermes Agent Profiles

每个 Agent 实例对应一个 Hermes Profile，包含：
- `config.yaml`：模型、工具集、记忆配置
- `SOUL.md`：Agent 身份、知识域、权力范围、交互协议

L3/L4 使用模板批量生成（`scripts/generate-agent-profiles.ts`），
L1/L2 的 1+8 个 Profile 手工精调。

### `content/` — 教材内容

```
content/
└── branch-XX-YYY/               # 每个领域
    └── subject-NNN-name/         # 每个学科
        ├── drafts/               # 章节草稿（L4产出）
        │   ├── ch01-xxx.md
        │   ├── ch02-xxx.md
        │   └── ...
        ├── reviews/              # 审核报告（L3/L2/L1产出）
        │   ├── ch01-L3-review.md
        │   ├── ch01-L2-review.md
        │   └── ch01-L1-final.md
        └── metadata.json         # 学科元数据
```

---

## 规模统计

| 目录 | 内容 | 规模 |
|------|------|:--:|
| `agents/domains/` | 八域定义文档 | 8 × 3 = 24 个文件 |
| `profiles/` | Hermes Profiles | 1(L1) + 8(L2) + 模板 |
| `content/` | 教材草稿 + 审核报告 | 102学科 × ~25章 = ~2,550 草稿文件 |
| `src/lib/` | 核心引擎 | 8 个子模块 |
| `src/components/` | React 组件 | 6 大组件群 |
| `src/app/api/` | API 路由 | 5 大类 |
