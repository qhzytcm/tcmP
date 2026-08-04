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
