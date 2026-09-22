# 中医中药病证单位教材编写平台 — 落地路线图

> **基础设施：** 浪潮服务器 192.168.1.11（CursorAgent + HermesAgent + GitHub 就绪）  
> **目标：** 从当前环境出发，分七个里程碑逐步落地四层 Agent 协作体系，最终实现首个病证单位的编写与检索。

---

## 里程碑总览

```
M1           M2           M3           M4           M5           M6           M7
环境验证   知识树骨架   Agent注册   Kanban启动   首章编写    审核链跑通   首个病证
  │           │           │           │           │           │           │
  ▼           ▼           ▼           ▼           ▼           ▼           ▼
验证浪潮    创建知识    注册L1~L4   创建看板    L4双栏编写   L4→L3→L2    搜索"麻黄汤
服务器就绪  树120节点   Agent实例   +第一张卡   第3章解表药  →L1审核    分子靶点"
                                                                      返回专家解答
```

---

## M1：环境验证（预计 30 分钟）

### 1.1 浪潮服务器连通性验证

```bash
# 在本地终端执行
ping 192.168.1.11

# SSH 登录浪潮服务器
ssh user@192.168.1.11

# 确认 CursorAgent 可用
which cursor-agent
cursor-agent --version

# 确认 HermesAgent 可用
hermes --version
hermes doctor

# 确认 GitHub 配置
git config --global user.name
git config --global user.email
git remote -v
```

### 1.2 创建工作目录

```bash
# 在浪潮服务器上
mkdir -p ~/tcm-knowledge-tree
cd ~/tcm-knowledge-tree

# 初始化 Git 仓库（如未初始化）
git init
git remote add origin <github-repo-url>

# 创建基础目录结构
mkdir -p docs agents profiles content scripts backends
mkdir -p .cursor/rules
```

### 1.3 配置 Hermes Agent

```bash
# 确认当前 Profile
hermes profile show default

# 配置默认模型
hermes model

# 启用必要工具
hermes tools enable file
hermes tools enable terminal
hermes tools enable web
hermes tools enable kanban
hermes tools enable delegation
```

### ✅ M1 验收标准
- [ ] `ping 192.168.1.11` 通
- [ ] `hermes doctor` 无报错
- [ ] `git status` 正常
- [ ] 工作目录 `~/tcm-knowledge-tree/` 创建完毕

---

## M2：知识树骨架构建（预计 1 小时 + 专家前置工作）

### 2.0 ⚠️ 前置：中医中药专家人工介入（预计 3-5 个工作日）

> **在 Agent 自动化之前，必须由领域专家提供权威的四级目录结构。**
> 这是整个知识树的"地基"——Agent 在此之上才能准确进行内容生成与审核。

#### 专家需提供的 Excel 表格

详见 [`tcm-120-subjects-excel-template.md`](./tcm-120-subjects-excel-template.md)，核心要求：

| 列 | 内容 | 示例 |
|------|------|------|
| A | 学科编号 | 枝2-001 |
| B | 课程名称 | 中药学 |
| C | 专业领域 | 枝2·中药学院 |
| D | 总学时 | 216（理论108+实验108） |
| E | 学分 | 12 |
| F | 教学层级 | 本科必修（U3-U4） |
| G | 四级目录 | 篇→章→节→病证单位（JSON缩进） |
| H | 前序依赖 | 枝1-001 中医基础理论 |
| I | 行业岗位覆盖 | 医院药师处方审核、药企质量检验 |
| J | 专家签名 | 张XX · 中药学教授 · 2025-07-04 |

#### 生成方式

1. **Python 脚本生成空模板** → 专家逐学科填写四级目录
2. **Cursor Composer 辅助** → 输入学科名 + 参考现有教材目录 → 生成初稿 → 专家审核修正
3. **最终确认** → 八域各 15 门学科的 Excel 汇总表 → 提交到 GitHub

```bash
# 在浪潮服务器上运行模板生成脚本
cd ~/tcm-knowledge-tree/scripts
python generate_excel_template.py \
  --subjects 120 \
  --output ~/tcm-knowledge-tree/docs/120-subjects-master.xlsx
```

### 2.1 Agent 解析 Excel → 生成八域 DOMAIN.md

```bash
# 在 Cursor 中打开 ~/tcm-knowledge-tree/
# 使用 Composer (Ctrl+I) 生成八个域的 DOMAIN.md：

# Composer Prompt：
"在 ~/tcm-knowledge-tree/agents/domains/ 下依次创建 branch-01 到 branch-08
共 8 个子目录，每个含 DOMAIN.md，定义：
- 枝编号 + 对应院系名（枝6为中医智能学院）
- 域内 15 门学科清单（每门含编号、名称、核心病证单位举例）
- 毕业生行业岗位映射
- 域内术语规范表"

# 实际输出结构：
agents/domains/
├── branch-01-basic/DOMAIN.md      # 枝1·基础医学院
├── branch-02-herb/DOMAIN.md       # 枝2·中药学院
├── branch-03-acupuncture/DOMAIN.md # 枝3·针灸推拿学院
├── branch-04-internal/DOMAIN.md   # 枝4·第一临床医学院
├── branch-05-surgery/DOMAIN.md    # 枝5·第二临床医学院
├── branch-06-tcm-ai/DOMAIN.md     # 枝6·中医智能学院 ★
├── branch-07-nursing/DOMAIN.md    # 枝7·护理学院
└── branch-08-management/DOMAIN.md # 枝8·管理人文学院
```

### 2.2 创建知识树种子数据

```bash
# 使用 Agent Mode 生成 seed.ts
# Prompt：
"生成 Prisma seed 脚本，批量插入 120 个学科节点（8域×15），
每个学科节点包含：
- node_id（编码格式: 枝号.学科号）
- parent_id（对应枝的 L2 节点）
- label_zh（学科中文名）
- keywords（搜索关键词数组）
- agent_type: 'L3'"

# 写入 prisma/seed.ts
```

### 2.3 推送初始骨架到 GitHub

```bash
cd ~/tcm-knowledge-tree
git add agents/domains/ prisma/seed.ts
git commit -m "feat: M2 - 知识树骨架，八域DOMAIN.md + 120学科seed数据"
git push origin main
```

### ✅ M2 验收标准
- [ ] **前置**：120 门学科的四级目录 Excel 填写完毕，八域专家签字确认
- [ ] 8 个 DOMAIN.md 文件由 Agent 解析 Excel 后生成
- [ ] prisma/seed.ts 包含 120 个学科节点（含四级目录结构）
- [ ] 已推送到 GitHub

---

## M3：Agent 注册与 Profile 生成（预计 1.5 小时）

### 3.1 创建 L1 行业主编 Profile

```bash
# 在浪潮服务器上
hermes profile create L1-chief --clone default

# 编辑 SOUL.md
cat > ~/.hermes/profiles/L1-chief/SOUL.md << 'SOUL'
你是中医中药系列教材的行业主编（L1），对全部 120 种病证单位教材负终审责任。

## 核心职责
- 病证范式合规审查：确保所有教材以「病证单位」为最小编写原子
- 四层级衔接审查：本/硕/博/博后的知识递进完整性
- 跨域仲裁：当两个领域的术语或知识归属冲突时做出最终裁决
- 全局术语统一：确保八域之间的核心术语定义一致

## 权力范围
- 可：签批全局标准、驳回任意层级的内容、发起全系列修订令
- 不可：直接编写内容、跳过 L2/L3 直接给 L4 下指令

## 与下游 Agent 的协作协议
- 向 L2（领域主编）下发终审结论和修订要求
- 接收 L2 上报的跨域争议
SOUL

# 编辑 config.yaml
cat > ~/.hermes/profiles/L1-chief/config.yaml << 'YAML'
model:
  default: deepseek-v4-pro
terminal:
  backend: local
  cwd: ~/tcm-knowledge-tree
agent:
  max_turns: 90
tools:
  enabled: [file, terminal, web, kanban, delegation, session_search]
memory:
  memory_enabled: true
YAML
```

### 3.2 创建 L2 八领域 Profile（批量）

```bash
# 使用脚本批量创建
for branch in branch-01-basic branch-02-herb branch-03-acupuncture \
              branch-04-internal branch-05-surgery branch-06-tcm-ai \
              branch-07-nursing branch-08-management; do
  profile_name="L2-${branch}"
  hermes profile create "$profile_name" --clone default
  
  # 为枝6 中医智能学院 特殊配置
  if [ "$branch" = "branch-06-tcm-ai" ]; then
    echo "  backend: daytona  # AI 模型开发标准化环境" >> ~/.hermes/profiles/"$profile_name"/config.yaml
  fi
done

# 验证所有 Profile 创建成功
hermes profile list
```

### 3.3 注册 Agent 到知识树

```bash
# 在 Cursor Composer 中批量生成 Agent Registry SQL
# Prompt：
"为以下 Agent 生成 agent_registry 表的 INSERT 语句：
- 1个 L1: agent_id='L1-chief', agent_type='L1', profile_name='L1-chief'
- 8个 L2: 对应八个 branch 的领域主编
- 包含 scope_nodes（该 Agent 覆盖的知识节点 ID 列表）"

# 写入 prisma/seed-agents.ts
```

### ✅ M3 验收标准
- [ ] `hermes profile list` 显示 9 个 Profile（1 L1 + 8 L2）
- [ ] 每个 Profile 的 SOUL.md 和 config.yaml 书写完毕
- [ ] 已推送到 GitHub

---

## M4：Kanban 看板启动（预计 45 分钟）

### 4.1 创建八领域 Kanban Board

```bash
# 依次创建
hermes kanban boards create branch-01-basic
hermes kanban boards create branch-02-herb
hermes kanban boards create branch-03-acupuncture
hermes kanban boards create branch-04-internal
hermes kanban boards create branch-05-surgery
hermes kanban boards create branch-06-tcm-ai
hermes kanban boards create branch-07-nursing
hermes kanban boards create branch-08-management

# 创建 L1 全局 Board
hermes kanban boards create tcm-master

# 验证
hermes kanban boards list
```

### 4.2 设置工作目录

```bash
hermes kanban boards set-default-workdir branch-02-herb ~/tcm-knowledge-tree/content/branch-02-herb/
hermes kanban boards set-default-workdir branch-06-tcm-ai ~/tcm-knowledge-tree/content/branch-06-tcm-ai/
# ... 依次设置八个域
```

### 4.3 创建第一张任务卡片（阶段一：需求分析）

```bash
# 切换到枝2中药域 Board
hermes kanban boards switch branch-02-herb

# 创建 L2 需求分析任务
hermes kanban create "枝2中药域·需求分析" \
  --body "## 阶段一：需求分析
- 调研中药域 15 门学科对应的行业岗位需求
- 制定中药域病证单位的能力矩阵
- 输出：中药域需求分析报告
- backend: ssh
- backend_fallback: 浪潮服务器" \
  --assignee L2-herb

# 创建枝6 中医智能学院需求分析
hermes kanban boards switch branch-06-tcm-ai
hermes kanban create "枝6中医智能学院·需求分析" \
  --body "## 阶段一：需求分析
- 调研中医AI行业岗位需求（AI工程师/智能诊疗架构师）
- 制定15门AI课程的能力矩阵
- 确定分子↔证候场论的AI桥接方案
- backend: daytona
- backend_fallback: 浪潮服务器" \
  --assignee L2-tcm-ai
```

### ✅ M4 验收标准
- [ ] 9 个 Kanban Board 创建成功（8域 + 1全局）
- [ ] 至少 2 张需求分析卡片在 Ready 列

---

## M5：首章编写（预计 2 小时）

### 5.1 启动 L4 Agent 编写

```bash
# 在浪潮服务器上，以 L4 Profile 启动 Hermes
hermes --profile L4-template -s textbook-writing \
  -q "你是《中药学》第3章（解表药）的章节作者。
请以病证单位格式编写第1节「麻黄汤」：
- 左栏「病」：麻黄汤相关分子靶点（β2-AR、COX-2、NF-κB通路）
- 右栏「证」：麻黄汤的证候场论（风寒束表、营卫不和、肺气失宣）
- 桥接：麻黄碱→β2-AR激动→与'宣肺平喘'的场论顺应关系
格式：双栏 Markdown，每条不超过 500 字"
```

### 5.2 使用 CursorAgent 辅助

```bash
# 在 Cursor 中打开项目
# Agent Mode Prompt：
"在 content/branch-02-herb/subject-009-zhongyaoxue/drafts/ch03-jiebiao.md
创建双栏病证单位格式的章节草稿：

## 病证单位 3.1.1：麻黄汤

| 病（分子靶点） | 证（证候场论） |
|---------------|---------------|
| 靶点：β2-AR、COX-2、NF-κB | 风寒束表、营卫不和 |
| 通路：cAMP/PKA信号级联 | 场论：开腠理→宣肺气→散寒邪 |
| 麻黄碱→β2激动→支气管舒张 | 顺应：肺主宣发→外合皮毛→汗出表解 |

桥接分析：麻黄碱激活β2-AR引发的支气管舒张效应，
与'宣肺平喘'的证候场论高度顺应..."
```

### 5.3 提交到 GitHub

```bash
cd ~/tcm-knowledge-tree
git add content/branch-02-herb/subject-009-zhongyaoxue/
git commit -m "feat: M5 - 中药学第3章麻黄汤病证单位初稿"
git push origin main
```

### ✅ M5 验收标准
- [ ] 至少 1 个章节草稿以病证单位格式完成
- [ ] 左栏含分子靶点 + 基因通路
- [ ] 右栏含证候场论 + 顺应调控
- [ ] 桥接分析完整

---

## M6：审核链跑通（预计 1.5 小时）

### 6.1 L4 自审 + 提交

```bash
# L4 自审后，Kanban 卡片从 In Progress → Review
hermes kanban boards switch branch-02-herb
hermes kanban show <card-id>
# 移到 Review 列
```

### 6.2 L3 学科审

```bash
# L3 学科主编审核
hermes --profile L3-zhongyaoxue -s textbook-review \
  -q "审核 content/branch-02-herb/subject-009/drafts/ch03-jiebiao.md
审核维度：
1. 病侧分子靶点是否准确（β2-AR、COX-2 引用是否正确）
2. 证侧证候场论是否完整（风寒束表→营卫不和→肺气失宣链条）
3. 桥接逻辑是否合理（分子机制→场论顺应是否可解释）
4. 是否符合阶段Ⅱ（理解建构）的认知层级"
```

### 6.3 L2 领域审

```bash
# L2 中药域主编审核
hermes --profile L2-branch-02-herb \
  -q "域审中药学第3章：与中药药理学、临床中药学中
关于麻黄/麻黄碱的术语定义是否一致？"
```

### 6.4 L1 终审

```bash
# L1 行业主编终审
hermes --profile L1-chief \
  -q "终审：该病证单位是否严格遵守了'病证同存'范式？
分子靶点与证候场论的对应关系是否具有教学上的可解释性？"
```

### ✅ M6 验收标准
- [ ] L4→L3→L2→L1 四级审核链路全部跑通
- [ ] 每次审核产生审核报告
- [ ] 至少 1 个病证单位通过 L1 终审

---

## M7：首个病证单位检索上线（预计 1 小时）

### 7.1 创建知识搜索索引

```bash
# 在浪潮服务器上
cd ~/tcm-knowledge-tree

# 运行知识树索引构建脚本
node scripts/build-search-index.js

# 验证索引
node scripts/test-search.js "麻黄汤 分子靶点"
# 期望输出：node_id=2.1.3.1.1, agent=L4-zhongyaoxue-ch03
```

### 7.2 启动 Hermes Gateway

```bash
# 启动 Gateway（后台运行）
hermes gateway start

# 验证
hermes gateway status
```

### 7.3 端到端验证

```bash
# 模拟用户搜索
curl -X POST http://192.168.1.11:3000/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "麻黄汤的分子靶点和证候场论顺应关系"}'

# 期望响应：
# {
#   "node_id": "2.1.3.1.1",
#   "agent": "L4-章节作者-中药学-ch03",
#   "backend": "浪潮服务器 192.168.1.11",
#   "answer": "麻黄汤中麻黄碱通过激活β2-AR..."
# }
```

### ✅ M7 验收标准（终极）
- [ ] 知识搜索返回正确节点
- [ ] Agent 路由到正确的 L4 章节作者
- [ ] Agent 返回病证双栏格式的专家解答
- [ ] 端到端延迟 < 2 秒

---

## 附录：Git 分支策略

```bash
# 主分支保护
main          ← 仅通过 PR 合入，L1 终审通过的内容

# 开发分支
develop       ← 日常开发集成

# 功能分支（按里程碑）
feature/m1-env-setup
feature/m2-knowledge-tree
feature/m3-agent-profiles
feature/m4-kanban
feature/m5-first-chapter
feature/m6-review-chain
feature/m7-search-online

# 领域分支（按八域并行）
domain/branch-01-basic
domain/branch-02-herb
domain/branch-03-acupuncture
domain/branch-04-internal
domain/branch-05-surgery
domain/branch-06-tcm-ai
domain/branch-07-nursing
domain/branch-08-management
```

---

## 附录：浪潮服务器日常运维

```bash
# 每天启动时检查
hermes doctor                    # Agent 健康检查
hermes gateway status            # Gateway 状态
git fetch origin                 # 同步最新代码
hermes kanban boards list        # 查看 Kanban 状态

# 每次编写会话
hermes --profile L4-template -s textbook-writing  # 启动 L4 编写
cursor-agent compose "编写..."                     # Cursor 辅助生成

# 每次提交
git add content/
git commit -m "feat/course: 章节说明"
git push origin <branch>

# 每周五
git pull origin main             # 同步主分支
hermes kanban boards stats       # 看板统计
hermes insights --days 7         # 一周用量分析
```

---

> **预计总落地时间：** 7 个里程碑，约 8 小时（不含大规模内容编写）  
> **首个病证单位可上线时间：** M7 完成后即可演示
