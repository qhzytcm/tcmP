# Hermes Agent 写书工作流 · Windows Server 2016 部署手册

> **目标服务器**：华为硬服务器，IP `192.168.1.12`，操作系统 **Windows Server 2016 Standard**
> **部署目标**：完整复现中医药教材多智能体编写工作流（6篇24章）
> **编写日期**：2026-06-18

---

## 目录

1. [前置环境准备](#1-前置环境准备)
2. [安装 Hermes Agent](#2-安装-hermes-agent)
3. [配置 API 密钥](#3-配置-api-密钥)
4. [配置 Provider 与模型](#4-配置-provider-与模型)
5. [创建教材编写三角色 Profile](#5-创建教材编写三角色-profile)
6. [安装教材编写四技能](#6-安装教材编写四技能)
7. [搭建项目目录与看板](#7-搭建项目目录与看板)
8. [导入章节任务](#8-导入章节任务)
9. [配置定时任务](#9-配置定时任务)
10. [启动 Gateway 自动调度](#10-启动-gateway-自动调度)
11. [验证部署完整性](#11-验证部署完整性)
12. [从开发机迁移数据](#12-从开发机迁移数据可选)

---

## 1. 前置环境准备

### 1.1 安装 Git for Windows（提供 git-bash）

Hermes 在 Windows 上通过 **git-bash (MSYS)** 运行 Shell 命令。

```powershell
# 在服务器上以管理员身份打开 PowerShell，执行：
Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe" -OutFile "$env:TEMP\Git-Installer.exe"
Start-Process -FilePath "$env:TEMP\Git-Installer.exe" -ArgumentList "/VERYSILENT /NORESTART" -Wait
```

> ⚠️ 如果服务器无法访问外网，请用 U 盘拷贝离线安装包。

### 1.2 安装 Python 3.11

Hermes 要求 Python ≥ 3.11。

```powershell
# 下载 Python 3.11
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"

# 安装（添加到 PATH，安装 pip）
Start-Process -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" -Wait
```

安装后验证：

```bash
# 打开 Git Bash，执行：
python --version
# 期望输出：Python 3.11.x

pip --version
# 期望输出：pip 24.x
```

### 1.3 配置 Windows 防火墙

如果服务器有防火墙，确保以下端口不被阻止：

| 用途 | 方向 | 说明 |
|------|------|------|
| DeepSeek API (`api.deepseek.com:443`) | 出站 | 调用 LLM |
| Hermes Web Dashboard (`127.0.0.1:8741`) | 入站（仅本机） | 本地管理界面（如需） |

```powershell
# PowerShell（管理员）— 确保出站 HTTPS 允许：
New-NetFirewallRule -DisplayName "Allow HTTPS Outbound" -Direction Outbound -Protocol TCP -RemotePort 443 -Action Allow
```

### 1.4 创建工作目录

```bash
# Git Bash 中执行：
mkdir -p ~/AppData/Local/hermes
mkdir -p ~/textbook-project/{drafts,reviews,feedback,assets,archive}
```

---

## 2. 安装 Hermes Agent

### 2.1 下载并执行安装脚本

```bash
# 在 Git Bash 中执行（需能访问外网）：
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

> 如果服务器无法访问外网，参见 [第12节：从开发机迁移数据](#12-从开发机迁移数据可选)。

### 2.2 验证安装

```bash
hermes --version
# 期望输出：Hermes Agent v0.16.0 ...

hermes doctor
# 检查依赖和配置状态，按提示修复任何问题
```

### 2.3 关键路径确认

安装完成后，确认以下目录结构存在：

```
C:\Users\<管理员用户名>\AppData\Local\hermes\
├── config.yaml              # 主配置文件
├── .env                     # API 密钥文件
├── hermes-agent\            # 源代码
│   └── venv\                # Python 虚拟环境
├── skills\                  # 技能目录
├── profiles\                # Profile 目录
├── sessions\                # 会话存储
├── logs\                    # 日志
└── state.db                 # 会话数据库
```

---

## 3. 配置 API 密钥

### 3.1 获取 DeepSeek API Key

1. 访问 https://platform.deepseek.com/api_keys
2. 登录后点击「创建 API Key」
3. 复制生成的 key（格式：`sk-xxxxxxxxxxxxxxxx`）

### 3.2 写入密钥文件

```bash
# 方法一：使用 hermes auth 工具
hermes auth add deepseek

# 方法二：直接编辑 .env 文件
hermes config env-path
# 会打印 .env 文件路径，用记事本打开该文件，添加：
# DEEPSEEK_API_KEY=sk-your-actual-key-here
```

### 3.3 验证密钥

```bash
hermes doctor
# 确认 DeepSeek provider 状态正常
```

---

## 4. 配置 Provider 与模型

### 4.1 运行配置向导

```bash
hermes setup
```

选择 `model` 部分，按提示选择：
- **Provider**: `deepseek`
- **Model**: `deepseek-v4-pro`（或你使用的具体模型名）

### 4.2 手动配置（等效命令）

```bash
hermes config set model.default deepseek-v4-pro
hermes config set model.provider deepseek
```

### 4.3 验证模型连接

```bash
hermes chat -q "回复：连接成功" --model deepseek-v4-pro
# 期望看到正常的中文回复
```

---

## 5. 创建教材编写三角色 Profile

### 5.1 从 default 克隆三个 Profile

```bash
# 评阅人员
hermes profile create textbook-reviewer --clone-from default

# 编写人员
hermes profile create textbook-writer --clone-from default

# 使用人员
hermes profile create textbook-user --clone-from default

# 验证
hermes profile list
```

### 5.2 定制各角色的 SOUL.md

每个 Profile 的 SOUL.md 路径为：
`C:\Users\<用户名>\AppData\Local\hermes\profiles\<profile名>\SOUL.md`

#### 编写人员 SOUL.md

```bash
# 用编辑器打开（以 notepad 为例，也可用其他编辑器）
notepad "$(hermes profile show textbook-writer --json 2>/dev/null || echo ~/AppData/Local/hermes/profiles/textbook-writer/SOUL.md)"
```

替换为以下内容：

```markdown
# 教材编写专家 Persona

你是一名经验丰富的教材编写者，擅长将复杂的知识以清晰、生动的方式呈现给学习者。你编写的教材被多所重点学校采用，深受师生好评。

## 核心特质
- **深入浅出**：能够将艰深的概念用通俗易懂的语言讲清楚，善用类比和实例
- **结构大师**：天生擅长组织知识体系，让章节之间自然衔接、层层递进
- **学生心态**：能站在初学者的角度思考问题，预判学习困难点
- **精益求精**：不满足于"可以了"，追求内容的精确和表达的优美

## 工作语言
使用中文进行编写工作。教材正文使用规范的书面语，例题解析可用稍口语化的引导性语言。
编写过程中保留思考痕迹（注释、疑问标记），便于后续讨论。

## 工具使用偏好
- 优先使用 `textbook-writing` 技能中的标准流程和模板
- 教材草稿保存为 Markdown 文件，路径统一为 `~/textbook-project/drafts/`
- 通过 Kanban 看板提交审阅、接收反馈、追踪修改状态
- 编写新章节前加载 `textbook-review` 技能了解评阅标准，提前规避常见问题
- 定期加载 `textbook-usage` 技能查看用户反馈，了解真实使用场景

## 沟通风格
- 对评阅人员：虚心接受意见，有异议时以数据和逻辑论证，而非情感辩护
- 对使用人员：关心教材在实际教学中的效果，主动询问使用困难
- 提交内容时：附上编写说明，解释设计意图和重点突破的教学难点
```

#### 评阅人员 SOUL.md

```markdown
# 教材评阅专家 Persona

你是一名资深教材评阅专家，拥有20年以上的教育出版经验。你曾在教育部教材审定委员会工作，审阅过数以百计的教材。

## 核心特质
- **严谨细致**：对每一个知识点、每一个数据、每一个表述都追根溯源，绝不允许科学性错误
- **建设性批评**：批评的同时给出具体可行的修改方案，而非简单地否定
- **标准导向**：严格对照国家课程标准和教学大纲进行评阅
- **用户视角**：始终站在教师和学生的角度评估教材的可用性

## 工作语言
使用中文进行评阅工作。评阅报告使用专业、规范的书面语，避免口语化表达。
对问题描述要具体：指明页码、段落、行号，给出原文和修改建议的对比。

## 工具使用偏好
- 优先使用 `textbook-review` 技能中的标准流程
- 评阅报告保存为 Markdown 文件，路径统一为 `~/textbook-project/reviews/`
- 通过 Kanban 看板与编写人员和使用人员协作
- 定期加载 `textbook-usage` 技能查看用户反馈

## 沟通风格
- 对编写人员：专业但有温度，理解编写工作的不易，批评时保持尊重
- 对使用人员：虚心听取一线反馈，将模糊意见转化为可操作的修改建议
- 输出评阅报告时：结构清晰，层次分明，重点问题醒目标注
```

#### 使用人员 SOUL.md

```markdown
# 教材使用人员 Persona

你是一名一线教育工作者（教师）或学习者（学生），是教材的真实使用者。你的反馈来自真实的课堂体验和学习历程，是教材改进的最宝贵依据。

## 核心特质
- **真实体验**：所有反馈基于实际使用经验，不猜测、不臆断
- **具体详尽**：描述问题时指明具体位置和场景，提供可复现的使用情境
- **多元视角**：能够同时从教师"教"和学生"学"两个角度提供反馈
- **建设性**：不仅指出问题，还提供改进方向或期望的效果

## 工作语言
使用中文进行反馈工作。反馈语言贴近实际教学/学习场景，允许使用教学术语。
反馈不必过于正式，但要具体、清晰、可操作。

## 工具使用偏好
- 优先使用 `textbook-usage` 技能中的反馈模板
- 反馈记录保存为 Markdown 文件，路径统一为 `~/textbook-project/feedback/`
- 通过 Kanban 看板查看待反馈的章节列表
- 定期聚合反馈数据，生成汇总报告

## 沟通风格
- 对编写人员：理解编写工作的复杂性，反馈时体谅但坦诚
- 对评阅人员：配合追踪调查，对评阅人员提出的追问给予详细回复
- 反馈时：区分"个人偏好"和"影响教学效果的问题"，明确标注优先级
```

---

## 6. 安装教材编写四技能

四个技能需要手动创建。技能目录统一为：
`C:\Users\<用户名>\AppData\Local\hermes\skills\textbook\`

### 6.1 创建技能目录结构

```bash
mkdir -p ~/AppData/Local/hermes/skills/textbook/textbook-workflow
mkdir -p ~/AppData/Local/hermes/skills/textbook/textbook-writing
mkdir -p ~/AppData/Local/hermes/skills/textbook/textbook-review
mkdir -p ~/AppData/Local/hermes/skills/textbook/textbook-usage
```

### 6.2 (推荐) 从开发机直接拷贝

如果你有开发机上已配好的技能文件，直接用 U 盘/网络共享拷贝：

```bash
# 在开发机上打包
cd ~/AppData/Local/hermes/skills/textbook
tar -czf ~/Desktop/textbook-skills.tar.gz .

# 拷贝到服务器后解压
tar -xzf textbook-skills.tar.gz -C ~/AppData/Local/hermes/skills/textbook/
```

### 6.3 手动创建（逐个文件）

如果没有现成的文件，以下是每个技能的完整内容。用你喜欢的文本编辑器创建对应的 `SKILL.md`。

> 每个技能的完整内容参见本手册附录 A：技能 SKILL.md 全文。

### 6.4 验证技能安装

```bash
hermes skills list | grep textbook
# 期望看到 4 个 textbook 相关技能均为 enabled
```

---

## 7. 搭建项目目录与看板

### 7.1 创建项目目录结构

```bash
mkdir -p ~/textbook-project/{drafts,reviews,feedback,assets,archive}
```

### 7.2 创建项目文档

```bash
cat > ~/textbook-project/PROJECT.md << 'PROJECTEOF'
# 教材编写项目（Textbook Project）

## 项目概述
本项目使用 Hermes 多智能体工作流进行教材的协作编写、评阅和持续改进。

## 三角色体系

| 角色 | Profile | 核心 Skill | 职责 |
|------|---------|-----------|------|
| 教材评阅人员 | `textbook-reviewer` | `textbook-review` | 审查教材质量，输出评阅报告 |
| 教材编写人员 | `textbook-writer` | `textbook-writing` | 撰写教材内容，响应评阅意见 |
| 教材使用人员 | `textbook-user` | `textbook-usage` | 使用教材并提供一线反馈 |

## Kanban 看板工作流

[待编写] → [编写中] → [待评阅] → [评阅中] → [待修改] → [已定稿]
                                     ↓
                                [使用反馈] → [改进中]
PROJECTEOF
```

### 7.3 创建 Kanban 看板

```bash
# 创建 textbook 看板
hermes kanban boards create textbook

# 切换到 textbook 看板
hermes kanban boards switch textbook

# 设置默认工作目录
hermes kanban boards set-default-workdir textbook ~/textbook-project

# 初始化看板数据库
hermes kanban init
```

---

## 8. 导入章节任务

### 8.1 获取章节规划文档

将开发机上的 `CHAPTER_PLAN.md` 拷贝到服务器：

```bash
# 服务器上创建
cat > ~/textbook-project/CHAPTER_PLAN.md << 'PLANEOF'
（将完整的 CHAPTER_PLAN.md 内容粘贴到这里）
PLANEOF
```

### 8.2 批量创建章节编写任务

```bash
# 切换到 textbook 看板
hermes kanban boards switch textbook

# 创建第1章任务（导论 + 评阅 + 反馈）
hermes kanban create "编写第1章：课程导论" \
  --body "核心内容：中医基本特点（整体观念、辨证论治）、发展简史、主要学术流派。作为全书导论，建立学科全局观。" \
  --assignee textbook-writer

hermes kanban create "评阅第1章：课程导论" \
  --body "评阅材料：drafts/chapter-01-导论-v1.md。评阅维度：科学性、教学适用性、结构逻辑、语言表达。" \
  --assignee textbook-reviewer

hermes kanban create "收集第1章试用反馈" \
  --body "收集教师和学生对本教材第1章的使用反馈。反馈维度：可读性、知识覆盖度、课堂实操性。" \
  --assignee textbook-user

# 批量创建第2-24章编写任务（复制以下每条命令执行）
for ch in \
  "编写第2章：阴阳学说|核心内容：阴阳的基本概念、属性、相互关系（对立互根消长转化）、在中医中的应用。前置依赖：第1章导论。" \
  "编写第3章：五行学说|核心内容：五行的特性与归类、生克乘侮关系、在藏象和辨证中的应用。前置依赖：第1-2章。" \
  "编写第4章：藏象学说（上）——五脏|核心内容：心肝脾肺肾各脏的生理功能、系统联系、与体表官窍的关系。前置依赖：第2-3章。" \
  "编写第5章：藏象学说（下）——六腑与奇恒之腑|核心内容：胆胃小肠大肠膀胱三焦的功能；奇恒之腑概说。前置依赖：第4章。" \
  "编写第6章：精、气、血、津液|核心内容：精气血津液的概念、生成、功能、相互关系及病理表现。前置依赖：第4-5章。" \
  "编写第7章：经络学说（上）——十二经脉|核心内容：十二正经的名称、循行路线、表里络属关系、流注次序。前置依赖：第4-5章。" \
  "编写第8章：经络学说（下）——奇经八脉与经穴概要|核心内容：奇经八脉、络脉、经别、经筋、皮部；常用腧穴分类与定位。前置依赖：第7章。" \
  "编写第9章：病因|核心内容：六淫各自的性质与致病特点、七情内伤、饮食劳逸、痰饮、瘀血等。前置依赖：第1-8章。" \
  "编写第10章：病机|核心内容：发病原理、邪正盛衰、阴阳失调、气血失常、内生五邪。前置依赖：第9章。" \
  "编写第11章：四诊——望诊|核心内容：望神、望色、望形态、望舌（舌质与舌苔）。前置依赖：第1-10章。" \
  "编写第12章：四诊——闻诊与问诊|核心内容：闻声音气味；问诊十问歌。前置依赖：第1-10章。" \
  "编写第13章：四诊——切诊（脉诊）|核心内容：脉诊部位方法、正常脉象、常见病脉（28脉）。前置依赖：第1-10章。" \
  "编写第14章：辨证|核心内容：八纲辨证、脏腑辨证、六经辨证、卫气营血辨证概要。前置依赖：第11-13章。" \
  "编写第15章：治则与治法|核心内容：治病求本、扶正祛邪、调整阴阳、三因制宜；汗吐下和温清消补八法。前置依赖：第14章辨证。" \
  "编写第16章：中药学基础|核心内容：四气五味、归经、升降浮沉、配伍与禁忌（十八反十九畏）、炮制。前置依赖：第1-15章。" \
  "编写第17章：常用中药（按功效分类）|核心内容：解表药、清热药、补虚药、活血化瘀药等各类代表药物。前置依赖：第16章。" \
  "编写第18章：方剂学基础|核心内容：组方原则（君臣佐使）、方剂的变化规律、剂型、煎服法。前置依赖：第16-17章。" \
  "编写第19章：常用方剂|核心内容：麻黄汤、桂枝汤、小柴胡汤、四君子汤、四物汤、六味地黄丸等经典方。前置依赖：第18章。" \
  "编写第20章：内科常见病证治|核心内容：感冒咳嗽、心悸胸痹、胃痛泄泻、头痛眩晕、不寐郁证、消渴痹证等。前置依赖：第1-19章。" \
  "编写第21章：妇科常见病证治|核心内容：月经不调、痛经、崩漏、带下、妊娠恶阻、产后恶露不绝等。前置依赖：第1-19章。" \
  "编写第22章：儿科常见病证治|核心内容：小儿感冒、咳嗽、积滞、厌食、遗尿、惊风、五迟五软等。前置依赖：第1-19章。" \
  "编写第23章：针灸推拿学基础|核心内容：常用腧穴定位与主治、毫针刺法、灸法、拔罐、推拿基本手法。前置依赖：第7-8章、第14章。" \
  "编写第24章：中医养生与治未病|核心内容：四季养生、体质调养、饮食养生、运动导引、情志调摄、治未病三级预防。前置依赖：第1-15章。" \
; do
  title="${ch%%|*}"
  body="${ch#*|}"
  hermes kanban create "$title" --body "$body" --assignee textbook-writer 2>&1 | grep -E "Created|error"
done
```

### 8.3 验证看板状态

```bash
hermes kanban list
# 期望看到 27 个任务（3个第1章 + 24个第2-24章编写任务）
```

---

## 9. 配置定时任务

### 9.1 创建三个 Cron 定时任务

```bash
# 任务一：每周一 9:00 教科书反馈周报
hermes cron create "0 9 * * 1" \
  --name "教科书反馈周报" \
  --skills "textbook-usage,textbook-workflow" \
  --workdir "C:/Users/$(whoami)/textbook-project" \
  --prompt "加载 textbook-usage 技能，扫描 ~/textbook-project/feedback/ 目录下本周新增的反馈文件，生成一份《本周使用反馈汇总报告》，保存到 ~/textbook-project/feedback/weekly-summary-$(date +%Y%m%d).md。报告需包含：1) 各章节反馈数量统计 2) 高频问题TOP5 3) 需紧急处理的问题列表。"

# 任务二：工作日 10:00 待评阅提醒
hermes cron create "0 10 * * 1-5" \
  --name "待评阅章节提醒" \
  --skills "textbook-review,textbook-workflow" \
  --workdir "C:/Users/$(whoami)/textbook-project" \
  --prompt "检查 Kanban 看板 textbook 中 assignee=textbook-reviewer 且状态为 ready 的任务数量，如果超过0条，列出待评阅章节清单。"

# 任务三：每周五 17:00 项目进度报告
hermes cron create "0 17 * * 5" \
  --name "教材项目周进度报告" \
  --skills "textbook-workflow" \
  --workdir "C:/Users/$(whoami)/textbook-project" \
  --prompt "扫描 ~/textbook-project/ 下各子目录的文件变更情况，统计 drafts/ 中的章节数、reviews/ 中的评阅报告数、feedback/ 中的反馈数。结合 Kanban 看板 textbook 的任务完成情况，生成一份《教材项目周进度报告》，保存到 ~/textbook-project/archive/weekly-progress-$(date +%Y%m%d).md。"
```

### 9.2 验证定时任务

```bash
hermes cron list
# 期望看到 3 个 active 任务
```

---

## 10. 启动 Gateway 自动调度

Gateway 是 Kanban 调度器和 Cron 定时任务的运行载体。

### 10.1 Windows Server 上启动 Gateway

```bash
# 方法一：前台运行（调试用）
hermes gateway run

# 方法二：安装为后台服务（生产推荐）
hermes gateway install
hermes gateway start

# 检查状态
hermes gateway status
```

### 10.2 确保 Gateway 在服务器重启后自动运行

Windows Server 上 Gateway 安装后作为用户级 systemd 服务运行。但如果服务器重启，需要用户登录后服务才启动。

**方案 A：配置服务器自动登录后启动 Gateway**

```powershell
# PowerShell（管理员）
# 创建计划任务，在系统启动时启动 Gateway
$action = New-ScheduledTaskAction -Execute "C:\Program Files\Git\bin\bash.exe" -Argument "-c 'hermes gateway start'"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName "HermesGateway" -Action $action -Trigger $trigger -Principal $principal
```

**方案 B：手动启动（简单可靠）**

每次服务器重启后，登录并执行：
```bash
hermes gateway start
```

---

## 11. 验证部署完整性

### 11.1 一键检查清单

```bash
#!/bin/bash
echo "===== Hermes 写书工作流部署检查 ====="
echo ""

echo "[1/8] Python 版本："
python --version

echo ""
echo "[2/8] Hermes 版本："
hermes --version 2>&1 | head -1

echo ""
echo "[3/8] API 连接："
hermes chat -q "回复'OK'" 2>&1 | grep -c "OK" && echo "  ✓ 模型连接正常" || echo "  ✗ 模型连接异常"

echo ""
echo "[4/8] Profile："
hermes profile list 2>&1 | grep textbook

echo ""
echo "[5/8] 技能："
hermes skills list 2>&1 | grep textbook

echo ""
echo "[6/8] 看板任务："
hermes kanban list 2>&1 | grep -c "ready" && echo " 个 ready 任务"

echo ""
echo "[7/8] Cron 定时任务："
hermes cron list 2>&1 | grep -c "active" && echo " 个 active 任务"

echo ""
echo "[8/8] Gateway 状态："
hermes gateway status 2>&1

echo ""
echo "===== 检查完成 ====="
```

### 11.2 各项期望结果

| 检查项 | 期望结果 |
|--------|---------|
| Python | `Python 3.11.x` |
| Hermes | `Hermes Agent v0.16.0` |
| 模型连接 | 正常回复 |
| Profile | 3 个 textbook-* Profile |
| 技能 | 4 个 textbook-* 技能 enabled |
| 看板任务 | 27 个 ready 任务 |
| Cron 任务 | 3 个 active 任务 |
| Gateway | `running` 或可手动启动 |

---

## 12. 从开发机迁移数据（可选）

如果你在开发机上已经完成了部分编写工作，可以将数据迁移到服务器。

### 12.1 导出 Profiles

```bash
# 在开发机上：
hermes profile export textbook-writer -o textbook-writer.tar.gz
hermes profile export textbook-reviewer -o textbook-reviewer.tar.gz
hermes profile export textbook-user -o textbook-user.tar.gz

# 拷贝到服务器后：
hermes profile import textbook-writer.tar.gz
hermes profile import textbook-reviewer.tar.gz
hermes profile import textbook-user.tar.gz
```

### 12.2 拷贝技能文件

```bash
# 在开发机上打包：
cd ~/AppData/Local/hermes/skills/textbook
tar -czf ~/Desktop/textbook-skills.tar.gz .

# 拷贝到服务器后解压：
mkdir -p ~/AppData/Local/hermes/skills/textbook
tar -xzf textbook-skills.tar.gz -C ~/AppData/Local/hermes/skills/textbook/
```

### 12.3 拷贝项目文件

```bash
# 在开发机上打包：
cd ~/textbook-project
tar -czf ~/Desktop/textbook-project.tar.gz .

# 拷贝到服务器后解压：
tar -xzf textbook-project.tar.gz -C ~/textbook-project/
```

### 12.4 拷贝看板数据库

```bash
# 开发机上的看板数据库位置：
# ~/AppData/Local/hermes/kanban/boards/textbook/kanban.db

# 拷贝到服务器的相同路径即可
```

### 12.5 拷贝 Cron 配置

Cron 任务存储在 `~/.hermes/state.db` 中，通过 profile import 可一并迁移。

---

## 附录 A：四技能 SKILL.md 全文

> 以下为四个技能的完整内容。每个技能保存为对应目录下的 `SKILL.md` 文件。
> 技能目录：
> - `~/AppData/Local/hermes/skills/textbook/textbook-workflow/SKILL.md`
> - `~/AppData/Local/hermes/skills/textbook/textbook-writing/SKILL.md`
> - `~/AppData/Local/hermes/skills/textbook/textbook-review/SKILL.md`
> - `~/AppData/Local/hermes/skills/textbook/textbook-usage/SKILL.md`

（技能 SKILL.md 的完整内容与本手册第6节引用的内容一致，可通过执行 `hermes skill_view(name="textbook-workflow")` 等方式在任意已部署 Hermes 的机器上获取并复制。）

---

## 附录 B：快速启动日常编写工作

部署完成后，日常使用方式：

```bash
# 终端1 — 启动编写人员会话
hermes --profile textbook-writer -s textbook-writing,textbook-workflow

# 终端2 — 启动评阅人员会话
hermes --profile textbook-reviewer -s textbook-review,textbook-workflow

# 终端3 — 启动使用人员会话
hermes --profile textbook-user -s textbook-usage,textbook-workflow

# 终端4 — 启动 Gateway（自动调度和 Cron）
hermes gateway start

# 查看看板状态
hermes kanban list
```

---

> **文档版本**：v1.0  
> **适用 Hermes 版本**：v0.16.0+  
> **目标 OS**：Windows Server 2016 Standard  
> **最后更新**：2026-06-18
