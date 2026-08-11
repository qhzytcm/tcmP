---
name: skill-sage-mentor
description: 医圣带教助手——医圣 Agent（SOUL 人格 + 师带徒回路）的标准调用。封装 /api/sages/consult 调用、user_level 深度映射、本地降级判读、会话记忆，供六者平台医者成长路径使用。
version: 1.0.0
phase: 2
lesson: 5
domain: D07
tags: [Agent, SOUL, 师带徒, 医圣, 成长引擎]
---

# 医圣带教助手（Sage Mentor）

> 口诀：**人格定边界，阶段定深度，检索定事实，记忆定成长。**
> 医圣 Agent = SOUL（我是谁）× 工具（能查证）× 师带徒（怎么教）× 记忆（成长档案）。

## 触发条件

- 学生（住院医-1 → 副主任医）向医圣问诊/请教
- 医圣成长引擎的教学环节
- 需要"辨证 → 论治 → 引经典 → 思考题"结构化带教的场景

## 标准流程

### 1. 按学生阶段选择深度

| user_level | 成长阶段 | 讲解要求 |
|-----------|---------|---------|
| 住院医-1 | 入门 · 伤寒导读 | 基础概念，术语必解释，基础思考题 |
| 住院医-2 | 辨证初成 · 张仲景 | 辨证要点 + 方剂配伍，引用条文 |
| 主治医 | 博采众长 · 孙思邈 | 鉴别诊断 + 经方加减，引经据典 |
| 副主任医 | 融会贯通 | 疑难病机 + 经典互参，鼓励思辨 |

### 2. 调用咨询端点

```bash
curl -X POST "https://www.zyyywaccn.com.cn/api/sages/consult/sage-zhang-zhongjing" \
  -H "Content-Type: application/json" \
  -d '{"user_level":"主治医","chief_complaint":"失眠多梦 心烦不安",
       "key_symptoms":["难以入睡","多梦易醒"]}'
```

本地对照（零 token 教学版）：

```bash
python ai-curriculum/D07/05-agent-soul/code/main.py "失眠多梦 心烦不安" --user-level 主治医
```

### 3. 判读返回

| 字段 | 含义 |
|------|------|
| `sage` / `user_level` | 人格与当前学生阶段 |
| `mode` | `llm`（DeepSeek 带教）/ `local`（模板降级） |
| `reply` | 五步结构：辨证 → 论治 → 经典 → 思考题 → 免责 |
| `results` | 检索工具回注的 Top-K（回答的事实基础） |
| `history_len` | 会话记忆长度（成长档案在积累） |

### 4. 教学闭环

- `mode=local` 时告知学生"离线带教模式"
- 思考题让学生回答 → 下一轮 consult 带上学生答案 → 形成师带徒对话链
- 问诊记录沉淀为成长档案（对应平台"对话=进化信号"闭环）

## 常见错误

1. **跳过检索工具**：医圣直接凭记忆回答——丢了"先查证再回答"的 observe→act 闭环
2. **不按 user_level 教学**：给住院医讲鉴别诊断、给主治医讲基础概念，都违背成长路径
3. **把带教当处方**：reply 的方剂方向须医师确认，免责声明不可省略
4. **忽略 local 降级**：LLM 失败时模板仍给出结构完整带教，但要标注降级

## 验证

```bash
python ai-curriculum/D07/05-agent-soul/code/main.py --self-test
# ✅ 6 项断言：SOUL 结构/深度变化/工具/本地结构/记忆/LLM prompt 组装
```
