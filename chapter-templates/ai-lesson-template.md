# AI 课程 Lesson 模板（中医语境版）

> 移植自 `ai-engineering-from-scratch/LESSON_TEMPLATE.md`（rohitg00，MIT）。
> 保留其"六拍教学法"（MOTTO→PROBLEM→CONCEPT→BUILD IT→USE IT→SHIP IT）与目录规范，
> 将全部语境替换为中医临床 / 六者平台 / 病证数据。
> 适用对象：D07 中医智能学院 15 门 AI 课程、面向六者用户的 AI 素养微课程。

## 目录规范（每课四件套）

```
NN-lesson-slug/
├── docs/
│   └── zh.md              # 课程正文（本模板的文档格式）
├── code/
│   ├── main.py            # 从零实现（BUILD IT）
│   └── tests.py           # 确定性测试（≥5 个，无外部依赖）
├── quiz.json              # 6 题契约：1 pre + 3 check + 2 post
└── outputs/
    ├── prompt-*.md        # 本课产出的提示词制品
    └── skill-*.md         # 本课产出的技能制品（Hermes SKILL.md 格式，可装进六者 Agent）
```

## 文档格式（docs/zh.md）

```markdown
# [课程标题]

> [一句话医谚式 MOTTO —— 记住这一句，整课就学会了]

**类型:** Build | Learn
**语言:** Python
**前置:** [上一课编号，或"无"]
**学时:** ~[分钟]
**关联:** [本平台对应 API / 端点 / 教材章目，如 tcmP /semantic-search、D07-S03]

## 学习目标

- 4-6 条以动词开头的目标（会用/能解释/能实现/能上平台验证）

## 问题（The Problem）

[2-3 段。一个真实的中医临床/医院场景痛点：
没有它做不到什么？为什么值得学？
示例句式：门诊医生想检索同类病证文献，只能逐条翻页……]

## 概念（The Concept）

[图表 + 直觉，不写代码。用 Mermaid 或 SVG（禁止 ASCII 框线图）。
先用病证类比建立心智模型，再给公式/流程。]

## 从零实现（BUILD IT）

[分步从零实现，每段代码可独立运行。只许用标准库 + 白名单依赖
（numpy/torch/h5py/zstandard/safetensors）。
示例范式：手写 TF-IDF → 手写余弦相似度 → 手写倒排索引（对齐 tcm_embed.py 的教学切片）]

### 步骤 1：[名称]

[讲解]

```python
[代码]
```

### 步骤 2：[名称]

[...继续]

## 平台实现（USE IT）

[用本平台现成能力跑同一件事，与从零实现对照：
- 生产检索 → `GET /semantic-search?q=...`（tcmP 病证单元 Embedding 引擎，TF-IDF+FTS5+RRF）
- ICD 编码 → `GET /icd/search`（内网 ICD-11 桥接）
- 病证双栏 → `GET /diag/:id`（病侧分子靶点 + 证侧场论）
结论范式：先手写 80 行明白原理，再调一个端点拿到生产级结果。]

## 交付制品（SHIP IT）

[本课产出什么可复用制品？存入 outputs/：
- 一条 prompt（六者岗位专用提示词）
- 一个 skill（可装入 healer/patient/pharmacist/... 的 SOUL 工具集）
- 一个 agent 行为模式（师带徒/处方审核/导诊……）
- 一批病证标注或图谱边（注入 kg/）
制品的 frontmatter 见下节。]

## 习题（60-30-10）

1. [基础 60% —— 复述核心概念]
2. [综合 30% —— 换一个病证域应用]
3. [拓展 10% —— 与前置课程/平台功能结合]

## 术语表

| 术语 | 常见误解 | 实际含义 |
|------|---------|---------|
| [术语] | [错误说法] | [准确定义] |

## 延伸阅读

- [资源](url) —— [为什么值得读]
```

## 制品 frontmatter（对齐 Hermes SKILL.md / 仓库输出规范）

```markdown
---
name: skill-名称
description: 本技能做什么（六者角色 + 场景）
version: 1.0.0
phase: [课程阶段号]
lesson: [课号]
domain: D07            # 所属领域（中医智能学院）
tags: [相关, 标签]
---
```

## quiz.json 契约（6 题，机器可校验）

```json
{
  "lesson": "NN-lesson-slug",
  "title": "课程标题",
  "questions": [
    {"stage": "pre",   "question": "...", "options": ["a","b","c","d"], "correct": 0, "explanation": "..."},
    {"stage": "check", "question": "...", "options": ["a","b","c","d"], "correct": 1, "explanation": "..."},
    {"stage": "check", "question": "...", "options": ["a","b","c","d"], "correct": 2, "explanation": "..."},
    {"stage": "check", "question": "...", "options": ["a","b","c","d"], "correct": 1, "explanation": "..."},
    {"stage": "post",  "question": "...", "options": ["a","b","c","d"], "correct": 3, "explanation": "..."},
    {"stage": "post",  "question": "...", "options": ["a","b","c","d"], "correct": 0, "explanation": "..."}
  ]
}
```

规则：恰好 6 题（1 前测 + 3 课中 + 2 后测）；`correct` 零索引；
`options` 固定 4 项；每题必须带 explanation。

## 门禁规则（对应 G1 级质量检查，脚本可自动化）

| 规则 | 校验内容 |
|:----:|---------|
| L01 | 目录命名 `NN-lesson-slug/`，存在 docs/zh.md |
| L02 | docs/zh.md 含 H1 标题 + MOTTO 引用块 + 六拍全部小节 |
| L03 | code/ 非空，main.py 可独立运行（10s 超时） |
| L04 | quiz.json 通过 6 题契约 schema |
| L05 | outputs/ 至少 1 个制品，frontmatter 含 name/description/phase/lesson |
| L06 | 代码块均带语言标签（python/json/bash/console/mermaid/yaml） |
| L07 | 不引入白名单外依赖（numpy/torch/h5py/zstandard/safetensors + 标准库） |
| L08 | 每课一个 commit，commit subject ≤72 字符 |

## 编写轮次建议（D07 中医智能学院 15 门 AI 课程）

| 轮次 | 课程主题 | 对应平台能力（USE IT 锚点） |
|:----:|---------|---------------------------|
| 1 | Python 与数据基础 / 中医数据形态 | tcmP data/ 病证 JSON、icd11_mms.db |
| 2 | 检索与文本表示（TF-IDF → 向量） | /semantic-search（tcm_embed.py） |
| 3 | RAG 与病证知识问答 | /rag、/diag、/bianzheng |
| 4 | LLM 工程：提示词 / 结构化输出 / 工具调用 | /agents（六者 SOUL 三端点） |
| 5 | Agent 工程：医圣人格与师带徒回路 | sages/（张仲景/孙思邈 SOUL） |
| 6 | 多智能体编排与六者协作 | agents/（healer/patient/pharmacist/...） |
| 7 | 评估与对齐：病证答案可信度、证据等级 | kg/ 证据等级字段、质量门禁 |
