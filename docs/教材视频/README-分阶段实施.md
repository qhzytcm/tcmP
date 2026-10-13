# 学科教材 → 授课网络视频 · 分阶段实施

> tcmP 中医药网络教育平台 · 学科教材视频课程线
> 建立日期：2026-10-13 ｜ 责任人：Hermes Agent

## 一、目标

把已有学科教材（`data/textbooks-released/*.xlsx`）**分阶段逐步**转化为**授课网络视频 + 网页课件**，发布到主/从前端浏览器页面：

| 端 | 位置 | 角色 | 可达性 |
|:--|:--|:--|:--|
| **主前端** | 华为云 `114.115.211.254` → `/var/www/tcmai/books/<slug>/` | 公网站点（www.zyyywaccn.com.cn） | ✅ SSH（密钥） |
| **从前端** | 华为硬服务器 `192.168.0.106`（IIS:80） | 内网镜像 | ⚠️ 阻塞（无 SSH/SMB 凭据） |

GitHub 仓库**只收录**「平台建立内容」（管线脚本 / 课件 HTML / 索引 JSON）与「学科教材内容」（教材 xlsx）；**媒体（mp4/wav）不入库**，走 .gitignore + 服务器上传。

## 二、交付物结构（每本书）

```
docs/教材视频/<slug>/
├── index.html                    # 课程目录页（入库）
├── <slug>-course.json            # 课程清单（入库）
├── 第NN章-<章名>-视频课程.html      # 逐章课件：视频+同步字幕+正文（入库）
├── 第NN章-<章名>.mp4              # 逐章授课视频（gitignore，上传服务器）
└── chNN/                         # 中间件 wav/png/seg（gitignore）
```

线上访问：`https://www.zyyywaccn.com.cn/books/<slug>/index.html`

## 三、工具链（scripts/）

| 脚本 | 作用 |
|:--|:--|
| `textbook_course_pipeline.py` | 主编译器：xlsx 章 sheet → 段落切分 → TTS → 幻灯 → ffmpeg 合成 → 课件 HTML → 课程索引。`--parse-only` 可只解析；`--chapter N` / `--all` 续跑 |
| `sapi_tts.ps1` | 离线 Windows SAPI 合成（zh-CN Huihui）——**edge-tts 服务端 403 失效时的可靠替代** |
| `deploy_course_to_frontends.py` | SFTP 上传课程到主前端；探测从前端并如实报告阻塞 |

运行：
```powershell
$env:PATH = "C:\Users\DELL\AppData\Local\hermes\hermes-agent\venv\Scripts;" + $env:PATH
python scripts\textbook_course_pipeline.py --book "data\textbooks-released\中医基础理论final.xlsx" `
       --slug zhongji-jichu --name 中医基础理论 --all
python scripts\deploy_course_to_frontends.py --slug zhongji-jichu --local "docs\教材视频\zhongji-jichu"
```

## 四、分阶段路线

| 阶段 | 范围 | 章数 | 状态 |
|:--:|:--|:--:|:--|
| **一** | 基础设施 + 试点：《中医基础理论》第1章 | 1 | ✅ **已完成**（视频 8:38 / 1080p / 0 解码错误，已部署主前端） |
| **二** | 《中医基础理论》全 12 章 | 12 | 进行中（待批量续跑） |
| **三** | 《中医诊断学》全 14 章 | 14 | 待启动 |
| **四** | 《方剂学》全 24 章 | 24 | 待启动 |
| **五** | 《中药学》全 30 章（章节长，分段上限 13 段/章） | 30 | 待启动 |
| **六** | 全平台课程总索引 + 主前端首页接入 + 从前端打通 + 反馈闭环 | — | 待启动 |

合计 ~81 章视频。每章离线 TTS ≈ 35s、合成 ≈ 60s → 单章约 2 分钟；81 章 ≈ 3 小时（可后台/分批续跑）。

## 五、已知问题与决策

1. **⚠️ edge-tts 全面失效（2026-10 实测）**：`speech.platform.bing.com` 对**本机与浪潮两个 IP 均返回 403**（本地 7.2.7 / 浪潮 7.2.8 / 升级至最新版后仍 403）——属**服务端封锁**，非客户端问题。
   → **决策：改用离线 Windows SAPI（zh-CN Huihui）**，零外部依赖、稳定（实测 2.6s/段）。代价：音色偏机械，后续如需高质量可切换至 Azure TTS（需 key）或平台数字人 TTS（`/dh/tts/`，当前 502 未启动）。
2. **⚠️ 从前端（华为硬服务器 192.168.0.106）不可自动上传**：22(SSH) 关闭、445(SMB) 访问被拒、仅 80(IIS 默认页) 可达。
   → 需项目方提供 SSH/SMB 凭据或 IIS 站点路径后，`deploy_course_to_frontends.py` 可直接复用。
3. **中文文件名 URL 编码**：浏览器自动处理；命令行验证须**整体** percent-encode（`urllib.parse.quote`），否则 nginx 会回退 SPA 壳页（假象 200）。
4. **段落切分**：以四级目录「小节」为段单位，>13 段自动合并，单段 >520 字按句号截断。

## 六、验收标准（每章）

- `ffmpeg -v error -i x.mp4 -f null -` → **0 error 行**
- 探针：1920×1080 / h264 / aac / 含音轨
- 课件 HTML：含 `const SUBS=` 与 `<video>`
- 线上：`curl` 课件 → `200 text/html`（非 SPA 壳）；mp4 → `206 video/mp4`
