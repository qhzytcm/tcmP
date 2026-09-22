# 素问讲读视频线 — 主仓外归档与备份策略

**定策日期：** 2026-09-22
**执行方式：** Hermes Agent 自动执行（抽检 → 定位置 → 拷贝 → 全量校验）
**关联：** `.gitignore`「Large media」节 · `archive/suwen-video-spotcheck-20260922.md`（抽检报告）

---

## 一、为什么出主仓

| 指标 | 值 |
|:--|:--|
| 文件数 | **2,693** |
| 总体积 | **4.68 GB**（5,030,095,695 字节） |
| 结构 | 83 个子目录（`suwen1`–`suwen81` + `v3` + `tables`），每篇 10 段 |
| 二进制构成 | 893 mp4 + 820 mp3 + 816 png + 82 txt + 81 `.video` + 1 m4a |

该体量（源于 Git 会为二进制做全量历史快照、不可增量压缩）不适合放入主仓。主仓历史上**从未跟踪任何二进制**（仅 md/py/json/sh/html/yml），故本次决策与既有约定一致。

## 二、位置与校验（已执行）

| 角色 | 路径 | 状态 |
|:--|:--|:--|
| 主仓（源码，保留原位置） | `~/textbook-project/drafts/cmrl/figures/book/video/` | 保留（被 .gitignore 排除） |
| **主仓外主位置** | `F:\hermes\archive\suwen-video-20260922\video\` | ✅ 2,693 文件 / 4.68 GB |
| **备份副本（异盘）** | `H:\hermes-archive\suwen-video-20260922\video\` | ✅ 2,693 文件 / 4.68 GB |
| 校验清单（主） | `F:\hermes\archive\suwen-video-20260922\SHA256SUMS.txt` | ✅ 2,693 条 |
| 校验清单（备） | `H:\hermes-archive\suwen-video-20260922\SHA256SUMS.txt` | ✅ 2,693 条 |

**校验方法**：robocopy `/E` 全量拷贝 → 逐文件 **SHA-256 源↔目标全量比对**（非抽样）。

```
[PRIMARY] files: src=2693 dst=2693 | bytes: src=5030095695 dst=5030095695
[PRIMARY] missing=0 extra=0 size_diff=0 | hash mismatches=0
[BACKUP ] files: src=2693 dst=2693 | bytes: src=5030095695 dst=5030095695
[BACKUP ] missing=0 extra=0 size_diff=0 | hash mismatches=0
ARCHIVE_STATUS=ALL_OK
```

## 三、抽检结论（前置步骤，5/81 篇）

见 `archive/suwen-video-spotcheck-20260922.md`：

- **5 篇全部通过**（suwen2 / suwen21 / suwen41 / suwen61 / suwen81）
- 每篇 10 段 mp4 全部可解码、时长 > 0、1920×1080 h264+aac；中位帧灰度 σ ≥ 30.8（无空白帧）
- 10 张幻灯片 PNG 全部可解码且非空白；10 个 TTS mp3 均可解码
- `concat.txt` 段序与 `seg01..seg10` 完全一致
- mp4 总时长与 mp3 总时长偏差稳定在 **+18.4 ~ +19.8s**（每篇一致的固定偏移，疑为分段静音/转场加帧，非异常）
- 🔴 **唯一缺口：`suwen1` 未成片**——只有 10 个 mp3（3.6 MB），**无 png、无 mp4**

## 四、尚无的备份层级（显式声明缺口）

| 层级 | 状态 | 阻塞原因 |
|:--|:--|:--|
| 本机同盘 | ✅ 源目录（不视为备份） | — |
| 异盘副本 | ✅ `H:\hermes-archive\...` | — |
| **异地/离线（浪潮 192.168.1.11）** | ❌ **未完成** | SSH 拒绝：`Permission denied (publickey,password,keyboard-interactive)`——无非交互凭据 |
| **异地（华为硬服务器 192.168.1.12）** | ❌ **未完成** | 主机 ping 可达，但 **22 端口 Connection refused**（未开 SSH） |
| 对象存储 | ❌ 未评估 | 需项目方提供凭据/桶策略 |

> **明确边界**：当前只做到「同机异盘双份 + 全量哈希校验」。异盘副本可防单盘故障，**不能防整机/机房级灾难**。补齐异地副本需项目方提供上述任一通道凭据，届时用同一 manifest 做增量校验即可。

## 五、恢复流程（可直接执行）

```powershell
# 1. 从主位置恢复（覆盖式，保留目录结构）
robocopy "F:\hermes\archive\suwen-video-20260922\video" `
         "C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video" /E

# 2. 校验完整性（与随附清单比对）
cd "F:\hermes\archive\suwen-video-20260922"
Get-FileHash -Algorithm SHA256 -Path (Get-ChildItem video -Recurse -File).FullName
# 或逐条比对 SHA256SUMS.txt（2693 条）
```

## 六、变更后维护约定

- 视频线**新增或重生成**任一文件后，需重新执行本流程（robocopy → sha256 → 更新 manifest），并更新本文件的结构统计表。
- `.gitignore` 中的 `drafts/cmrl/figures/book/video/` 与 `*.mp4/*.mp3/...` 规则**不得移除**，否则 4.68GB 会造成误入库。
- 本文件与抽检报告均**随主仓入库**（轻量文本），二进制本体留在上述两个位置。

---

*本文件由 Hermes Agent 于 2026-09-22 自动生成（归档执行者 = 同一进程，非事后追记）*
