---
name: prompt-json-output
description: JSON 输出提示词模板——让 LLM 输出符合 Schema 的 JSON，含字段说明、输出示例、约束与「校验失败错误喂回」的重试反馈格式。对齐 DeepSeek response_format=json_object 的工程用法。
phase: 2
lesson: 4
tags: [prompt, JSON, 结构化输出, 重试]
---

# JSON 输出提示词模板（Schema 约束 + 错误反馈重试）

> 适用：RAG 生成、六者工具调用、图谱注入前的 LLM 结构化输出。
> 生产对照：`StructuredRAG.build_prompt()`（04-structured-output/code/main.py）。

## 首次调用模板

```
患者症状：{symptoms}

病证库 Top-{k} 检索结果：
{retrieved_context}

请只输出一个 JSON 对象（不要任何其他文本），结构：
{"disease": "最可能疾病名(必须来自检索结果)",
 "icd11_code": "ICD-11编码",
 "syndrome": "中医证候",
 "formula": "推荐方剂",
 "confidence": 0.0到1.0,
 "differential": ["鉴别要点1", "鉴别要点2"],
 "evidence_gap": true或false}

约束：
- 只引用检索结果中的病证
- Top1 证据分数低于 0.05 时 evidence_gap 置 true
```

## 重试模板（校验失败后）

```
⚠️ 你上一轮输出未通过 JSON Schema 校验：
{validation_errors}

请修正后重新输出完整 JSON（不要任何其他文本）。
```

## 三要素与动机

| 要素 | 内容 | 工程动机 |
|------|------|---------|
| 结构说明 | 逐字段列出（含类型/来源约束） | 让模型"看着 Schema 填空"，而非自由发挥 |
| 输出示例 | 完整 JSON 骨架 | 少样本提示，降低格式漂移 |
| 错误反馈 | 校验器原样喂回（缺字段/pattern 违规…） | 错误是最强的修正信号，重试成功率显著高于盲重试 |

## 配套开关（生产级）

```json
{"response_format": {"type": "json_object"}}
```

`json_object` 让模型尽量输出合法 JSON；Schema 校验兜底字段契约。**两者缺一不可**。

## 质量自检

- [ ] 字段说明与 Schema 完全一致（增删字段时同步更新模板）
- [ ] 约束（引用范围/证据不足）在 JSON 语义中有对应字段（evidence_gap）
- [ ] 重试模板包含上轮错误原文
- [ ] 降级路径存在（本地模板），且调用方感知 `degraded` 标记
