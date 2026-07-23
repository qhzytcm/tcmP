# 六者·中医医院AI网络教育平台

> TCM Hospital AI Network Education Platform  
> 以中医医院为场景的六类AI智能体系统，支撑中医药行业人才成长。

## 项目概览

```
六者Agent ── 医者(含师带徒) · 患者 · 药者 · 械者 · 规者 · 法者
医圣人格 ── 张仲景(六经辨证) · 孙思邈(大医精诚)
知识图谱 ── 病证单位 x 23+ (目标60,000+)
手机 APP ── Hermes-like CLI · PWA · 7角色切换
云端 API ── 32端点 · DeepSeek LLM驱动 · HTTPS
```

## 目录结构

```
tcmP/
├── api/main.py               # API服务器 (32端点, FastAPI+DeepSeek)
├── agents/                    # 六者Agent SOUL人格定义
│   ├── healer/SOUL.md         # 医者
│   ├── patient/SOUL.md        # 患者
│   ├── pharmacist/SOUL.md     # 药者
│   ├── device/SOUL.md         # 械者
│   ├── regulator/SOUL.md      # 规者
│   └── legal/SOUL.md          # 法者
├── sages/                     # 医圣人格
│   ├── zhang-zhongjing/SOUL.md
│   └── sun-simiao/SOUL.md
├── kg/                        # 病证知识图谱
│   ├── schema/schema.json     # 图谱Schema (7定义域)
│   └── samples/dsu-samples-*.json  # 23个样本病证单位
├── mobile-app/                # 手机终端APP (PWA)
├── docs/                      # 架构设计文档
├── scripts/                   # 部署脚本
└── .github/workflows/         # CI/CD流水线
```

## 在线访问

| 资源 | 地址 |
|:-----|:------|
| 手机APP | `https://www.zyyywaccn.com.cn/liuzhe/` |
| API健康 | `https://www.zyyywaccn.com.cn/api/sages/health` |
| KG统计 | `https://www.zyyywaccn.com.cn/api/sages/kg/stats` |
| 医圣列表 | `https://www.zyyywaccn.com.cn/api/sages/sages` |

## 快速启动

```bash
# 本地启动API服务
cd api && pip install fastapi uvicorn pydantic
python main.py

# API将监听 http://0.0.0.0:8300
# 访问 http://localhost:8300/health 验证
```

## 技术栈

- **推理引擎**: DeepSeek LLM + 医圣人格SOUL.md提示工程
- **API服务**: Python FastAPI, 32 REST端点
- **前端**: 单页WebAPP (PWA, 手机端Hermes-like CLI)
- **部署**: 华为云 CentOS 7.6 + Nginx + systemd
- **图谱**: 病证单位Schema (ICD-11 + 分子靶点 + 证候场论)
- **容器**: Docker (可选)

## CI/CD

- `.github/workflows/tcm-ci-cd.yml` — 主CI/CD流水线
- Git提交后自动触发质量检查 + 单元测试

## 项目状态

- 六者Agent: ✅ 全部构建 (6/6)
- 医圣人格: ✅ 张仲景 + 孙思邈
- 知识图谱: ⏳ 23/60,000+ 持续扩展中
- 手机APP: ✅ v1.0 PWA
- LLM推理: ✅ DeepSeek已激活
- HTTPS: ✅ www.zyyywaccn.com.cn
