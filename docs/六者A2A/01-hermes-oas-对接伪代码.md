# 01 · HermesAgent 对接 open-agent-studio 核心伪代码

> 对接模型：**HermesAgent = 编排方**（会话发起 / 消息注入 / 结果与日志消费），open-agent-studio = 远端智能体运行平台。
> 三原语：**会话创建 → 消息推送 → 日志拉取**；两条数据通道：控制面 REST + 事件面 SSE；日志面游标增量。

## 1. 通道与约定

| 面 | 用途 | 协议 |
|---|---|---|
| 控制面 | 会话创建/关闭、消息投递 | HTTPS REST（JSON） |
| 事件面 | 增量文本、工具调用、运行状态 | SSE（`text/event-stream`） |
| 日志面 | 历史日志补拉（断点续传、审计） | REST 游标分页 |

## 2. 会话创建

```python
import httpx, uuid

OAS_BASE = "https://oas.tcmp.local/api/v1"
HEADERS = {
    "Authorization": f"Bearer {OAS_TOKEN}",
    "Content-Type": "application/json",
    "X-Request-Id": str(uuid.uuid4()),        # 幂等键：重试不重复建会话
}

def create_session(agent_id: str, user_id: str,
                   model: str = None, params: dict = None) -> dict:
    """绑定 agent + 租户用户 + 运行参数 → session_id（长生命周期, 一次创建多次消息）"""
    payload = {
        "agent_id": agent_id,                  # 'doctor'/'patient'/'pharmacist'/'device'/'regulator'/'lawyer'
        "user_id":  user_id,                   # 租户/终端用户隔离
        "channel":  "hermes-tcmP",             # 来源标识（路由/审计）
        "model":    model,                     # 可选覆盖平台默认
        "params":   params or {
            "temperature": 0.3,
            "tools": ["semantic_search", "rag", "icd11_lookup", "graph_query"],
            "max_steps": 20, "timeout_s": 180,
        },
        "meta": {"locale": "zh-CN", "course": "HDNJ_SW18", "case_id": None},
    }
    resp = httpx.post(f"{OAS_BASE}/sessions", json=payload,
                      headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    assert data.get("session_id"), f"创建失败: {data}"
    return {"session_id": data["session_id"],
            "event_url": data.get("event_url",
                                  f"{OAS_BASE}/sessions/{data['session_id']}/events"),
            "status": data.get("status", "ready")}
```

## 3. 消息推送（同步终态 + SSE 流式）

```python
def send_message(sess: dict, content: str, *, attachments=None,
                 stream: bool = True, parent_msg_id: str = None):
    """推送用户消息。stream=False 同步取终态；True 走 SSE 逐事件 yield"""
    payload = {"content": content,
               "attachments": attachments or [],     # [{type, uri, mime}]
               "parent_msg_id": parent_msg_id}
    url = f"{OAS_BASE}/sessions/{sess['session_id']}/messages"

    if not stream:
        resp = httpx.post(url, json=payload, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        return resp.json()["message_id"]

    with httpx.stream("POST", url, json=payload, headers=HEADERS,
                      timeout=httpx.Timeout(600)) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line.startswith("data:"):
                continue
            evt = json.loads(line[5:].strip())
            match evt["type"]:
                case "message.created": msg_id = evt["message_id"]
                case "message.delta":   yield ("delta", evt["text"])
                case "tool.call":       yield ("tool", evt)          # 含参数
                case "tool.result":     yield ("tool_result", evt)
                case "run.completed":   yield ("done", evt)
                case "run.failed":      raise RuntimeError(evt.get("error"))
                case "ping":            continue
```

## 4. 日志拉取（游标增量）

```python
import time

def pull_logs(sess, *, after_cursor="", event_types=None, limit=200) -> dict:
    params = {"after": after_cursor, "limit": limit,
              "types": ",".join(event_types or ["thinking", "tool", "error", "metrics"])}
    resp = httpx.get(f"{OAS_BASE}/sessions/{sess['session_id']}/logs",
                     params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return {"next_cursor": data.get("next_cursor", ""),
            "logs": data.get("items", []),
            "has_more": data.get("has_more", False)}

def log_watch_loop(sess, on_log):
    """心跳增量同步（审计/过程可视化/断点续传）"""
    cursor = ""
    while sess["status"] != "closed":
        page = pull_logs(sess, after_cursor=cursor)
        for lg in page["logs"]:
            on_log(lg)                              # 入库 / 过程可视化 / 告警
        cursor = page["next_cursor"]
        time.sleep(2 if page["has_more"] else 8)    # 忙时 2s / 闲时 8s
```

## 5. 三原语时序

```
HermesAgent                       open-agent-studio
   │ POST /sessions                     │
   │───────────────────────────────────▶│  create_session
   │◀──────── {session_id,event_url} ───│
   │ POST /sessions/{id}/messages       │
   │───────────────────────────────────▶│  消息推送
   │◀─ SSE: message.delta ×N ──────────│  流式增量
   │◀─ SSE: tool.call / tool.result ───│  工具轨迹
   │◀─ SSE: run.completed ─────────────│  终态
   │ GET /sessions/{id}/logs?after=..  │
   │───────────────────────────────────▶│  日志增量补拉
   │◀────── {next_cursor, items[]} ─────│
```

## 6. 工程红线

| 关注点 | 约定 |
|---|---|
| 鉴权 | 控制面 Bearer；SSE 短期 event token；`user_id` 租户隔离 |
| 幂等 | 创建/推送均带 `X-Request-Id`，平台去重 |
| 断线续传 | 流中断 → `GET /logs?after=<最后 seq>` 补齐，不重推消息 |
| 状态机 | session：`ready → running → idle → closed`；仅 `idle/ready` 可推送 |
| 超时 | 创建 10s；同步推送 60s；流式 600s；日志 15s |
| 背压 | SSE 消费慢 → 降级「同步终态 + 日志补拉」双通道 |
