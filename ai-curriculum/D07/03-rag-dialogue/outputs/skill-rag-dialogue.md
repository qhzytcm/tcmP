---
name: skill-rag-dialogue
description: RAG 病证问答助手——「症状 → 诊断 → 辨证 → 方剂建议」问答链的标准调用与结果校验。封装 /api/sages/rag 端点调用、本地降级判读、faithfulness 校验，供医者 Agent 在门诊问答/教学场景使用。
version: 1.0.0
phase: 2
lesson: 3
domain: D07
tags: [RAG, 问答, 病证, 医者]
---

# RAG 病证问答助手（RAG Dialogue）

> 口诀：**检索锚定事实，生成只做综合；输出必须可溯源。**
> 平台问答链 = 内网检索（零 token）→ Top-K 上下文 → LLM 精修（几百 token）。
> 本技能封装该链路的调用与**输出校验**——RAG 的答案必须能指着证据说"我根据这 3 条病证给出的"。

## 触发条件

- 用户给出症状主诉，需要「最可能疾病 + 证候 + 方剂方向」的综合回答
- 医者需要鉴别诊断候选的书面化表述
- 教学场景：用真实病案演示辨证思路

## 标准流程

### 1. 调用问答端点

```bash
curl -X POST "https://www.zyyywaccn.com.cn/api/sages/rag" \
  -H "Content-Type: application/json" \
  -d '{"symptoms": ["难以入睡","多梦易醒","心烦不安"], "top_k": 3}'
```

本地对照（零 token 教学版）：

```bash
python ai-curriculum/D07/03-rag-dialogue/code/main.py "难以入睡 多梦易醒 心烦不安"
```

### 2. 判读返回结构

| 字段 | 含义 | 使用要点 |
|------|------|---------|
| `results` | 检索 Top-K（含病名/ICD-11/证候/方剂/证据分数） | 答案的**事实基础** |
| `rag_report` | LLM 综合报告（或本地模式提示） | 引用结果展示 |
| `mode` | `local`（无 key 降级）/ `llm` | local 时向用户说明"未联网精修" |
| `token_estimate` | 本次问答 LLM 消耗估算 | 平台降 token 设计的度量 |

### 3. faithfulness 校验（本技能的关键步骤）

**把 `rag_report` 与 `results` 对照**：

```python
from code.main import RAGPipeline, MINI_CORPUS, corpus_texts  # 教学版
rag = RAGPipeline(MINI_CORPUS, corpus_texts(MINI_CORPUS))
a = rag.ask("难以入睡 多梦易醒 心烦不安")
f = rag.faithfulness(a["results"], a["report"])
print(f["coverage"])   # 报告引用的 Top-K 病名覆盖率
```

| coverage | 判定 | 处置 |
|:--------:|------|------|
| 100% | 完全锚定证据 | 正常展示 |
| ≥60% | 大部分锚定 | 展示但提示个别表述超出检索范围 |
| <60% | 疑似幻觉 | **不展示**，回退本地模板或重新生成 |

### 4. 展示规范（医者 Agent）

- 先展示 Top-K 检索证据（让用户看到"依据"）
- 再展示综合报告
- 固定附注："以上为检索增强的辅助建议，非诊断结论，请以四诊合参与线下就诊为准"

## 常见错误

1. **跳过 faithfulness**：LLM 报告直接转发——RAG 最危险的失效模式就是"检索是对的，生成编了新的"
2. **把方剂建议当处方**：推荐方剂方向 ≠ 处方，必须声明医师确认
3. **本地模式未声明**：`mode=local` 时不说明，用户误以为是 LLM 综合
4. **top_k 过大**：上下文膨胀推高 token；门诊问答 3-5 足够

## 验证

```bash
python ai-curriculum/D07/03-rag-dialogue/code/main.py --self-test
# ✅ 全部 5 项断言通过（含 faithfulness=100%）
```
