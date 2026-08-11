---
name: skill-structured-output
description: 结构化输出守卫——六者 Agent 与图谱/下游流程交换数据的 JSON 契约层。封装「LLM JSON 输出 → Schema 校验 → 错误喂回重试 → 本地模板降级」的标准流程，保证平台数据交换永远可机器消费。
version: 1.0.0
phase: 2
lesson: 4
domain: D07
tags: [结构化输出, JSON Schema, 校验, 六者]
---

# 结构化输出守卫（Structured Output Guard）

> 口诀：**先定义契约，再相信输出；机器要消费，校验不可省。**
> 自由文本只给人看，JSON 契约才给机器用。本技能封装平台数据交换的契约层：
> 参数校验（调用前）+ 输出校验（调用后）+ 重试降级（失败时）。

## 触发条件

- Agent 需要把 LLM 输出交给下游流程（图谱注入、处方审核、风险评估）
- 六者 SOUL 工具调用的参数需要机器校验
- 任何「LLM 输出 → JSON → 消费」的链路

## 标准流程

### 1. 定义 Schema（先定契约）

```python
SCHEMA = {
    "type": "object",
    "required": ["disease", "icd11_code", "syndrome", "formula",
                 "confidence", "differential", "evidence_gap"],
    "properties": {
        "disease": {"type": "string", "minLength": 2},
        "icd11_code": {"type": "string", "pattern": r"^[0-9A-Z][0-9A-Z.]*$"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "differential": {"type": "array", "minItems": 1,
                         "items": {"type": "string"}},
        "evidence_gap": {"type": "boolean"},
        # ...
    },
}
```

> 平台生产参考：`tcmP/kg/schema/schema.json`（DSU 六段结构，$ref 组织）；`api/main.py` 的 Pydantic BaseModel（FastAPI 自动校验请求）。

### 2. 调用 LLM 时要求 JSON

```bash
# DeepSeek 生产级开关
python ai-curriculum/D07/04-structured-output/code/main.py \
  "难以入睡 多梦易醒 心烦不安" --api-key $env:DEEPSEEK_API_KEY
# 内部 prompt 含结构说明 + response_format={"type":"json_object"}
```

### 3. 校验 + 重试 + 降级

```
LLM 输出 → JSON 解析 → Schema 校验
  ├─ 通过 → 交给下游 ✅
  ├─ 失败 → 错误喂回 prompt 重试（≤2 次）
  └─ 仍失败 → 降级本地模板（确定性 JSON，graceful degradation）
```

| 失败类型 | 处理 |
|---------|------|
| JSON 解析失败 | 重试（错误信息：解析异常） |
| 缺必填字段 | 重试（列明缺哪个字段） |
| 类型/pattern/枚举违规 | 重试（给具体违规路径） |
| 重试用尽 | 降级本地模板 + 标记 `degraded: true` |

### 4. 下游消费

```python
from code.main import MiniValidator, RAG_REPORT_SCHEMA  # 教学版
v = MiniValidator()
assert v.validate(data, RAG_REPORT_SCHEMA) == []  # 消费前最后一关
```

## 常见错误

1. **只靠 response_format 不校验**：`json_object` 只保证「是 JSON」，不保证「符合契约」
2. **校验失败直接丢弃**：浪费一次有价值的 LLM 调用——错误喂回重试的成功率很高
3. **schema 过度设计**：字段越多校验越严，LLM 首次通过率越低；先用最小必填集
4. **忽略降级标记**：`degraded: true` 的输出质量低于 LLM 模式，下游应降权处理

## 验证

```bash
python ai-curriculum/D07/04-structured-output/code/main.py --self-test
# ✅ 5 项断言：合法通过/四类违规拦截/local_json 合规/重试成功/全坏降级
```
