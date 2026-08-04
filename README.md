# 六者·中医医院AI网络教育平台

> 支撑中医药行业人才成长的AI网络平台

以中医医院为场景，构建**医·患·药·械·规·法**六类AI智能体，映射医院真实分工；医圣人格（张仲景/孙思邈）驱动成长，病证知识图谱（103单位）支撑推理。

## 架构

```
六者Agent + 医圣人格 + 知识图谱
    └── API(35端点, FastAPI+DeepSeek)
          └── 手机PWA + HTTPS
```

## 目录

api(后端) · agents(六者SOUL) · sages(医圣) · kg(图谱) · mobile-app(PWA) · docs(架构) · .github(CI/CD)

## 访问

- APP: https://www.zyyywaccn.com.cn/
- API: /api/sages/

## 技术栈

DeepSeek · FastAPI · PWA · Nginx · 华为云

## 启动

```bash
cd api && pip install -r requirements.txt
python main.py
```

## 依赖离线安装包

`deps/` 已预下载两套 wheel（与生产环境锁定版本一致：fastapi 0.95.1 / uvicorn 0.21.1 / pydantic 1.10.7 / starlette 0.26.1）：

| 目录 | 平台 | 用途 |
|---|---|---|
| `deps/wheels-linux/` | manylinux2014_x86_64 (cp39) | 华为云 CentOS 7 离线安装 |
| `deps/wheels-win/` | win_amd64 (cp39) | 本地 Windows 开发离线安装 |

离线安装：`pip install --no-index --find-links deps/wheels-linux -r api/requirements.txt`（服务器见 `deps/install-linux.sh`）

## ICD-11 编码桥接（v2.2）

病证图谱 ICD-11 标准编码（病历/医保对接）双通道：

| 通道 | 说明 |
|---|---|
| 内网 API | `192.168.0.111:8080`（WHO whoicd/icd-api 容器，2026-01 MMS en+zh），中文搜索 |
| 本地 db | `data/icd11_mms.db`（31,838 实体，release 2026-01），Foundation ID → 标准编码 |

- **API 端点**：`GET /icd/search?q=病名`（中文桥接，长词滑动窗口自适应）· `GET /icd/code/{编码}` 反查 · `GET /icd/id/{foundation_id}`
- **工具**：`python scripts/icd11_client.py 高血压`（中文桥接）/ `--code BA00` / `--en hypertension`
- **标注**：103 个病证单位已标注（74 个标准编码 + 29 个实体 ID），字段 `disease_side.icd11_*`
- **限制**：华为云（公网）访问不到内网 API，中文搜索自动降级英文；编码端点由镜像 API 能力决定（MMS 线性化端点镜像未实现，db 补齐）
