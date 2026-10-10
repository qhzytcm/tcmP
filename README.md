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

api(后端) · agents(六者SOUL) · sages(医圣) · kg(图谱 & **知识树** & **信息学**) · mobile-app(PWA) · docs(架构) · .github(CI/CD)

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

## 病证单元 Embedding 引擎（v3.0）

论著落地（ESWA 2025 "Decoding the mind: A RAG-LLM on ICD-11"）：病证单元 Document → embedding → 余弦检索 Top-K → 诊断/辨证/RAG 报告。**内网零 token 检索，仅报告需 LLM 小上下文（↓95% token）**。

| 端点 | 功能 | 示例 |
|:-----|:-----|:-----|
| `POST/GET /diag` | 疾病诊断（症状→病） | `/diag?q=恶寒,发热,无汗` → CA00 普通感冒 |
| `POST/GET /bianzheng` | 证候辨证（症状→证） | `/bianzheng?q=口苦,咽干` → 肝胆湿热证 |
| `GET /semantic-search` | 语义检索（向量+FTS5 融合） | `?q=失眠多梦` |
| `POST /rag` | RAG 诊断报告（LLM 精修） | 症状 → Top-K + 报告 |

技术：TF-IDF 字符 n-gram + SQLite FTS5 + RRF 融合；BGE 语义向量为升级路径（ModelScope 下载）。详见 `docs/ARCH-EMBEDDING.md`。

## 中医知识树 · 平台统一知识结构（v1.0.0）

把「120 门学科 / 病证知识图谱 / ICD-11 / 六者 Agent / 医圣成长」编织成**树图一体**的知识结构：
**须—根—干—枝—叶 五级骨架 × 跨枝经脉图边**（3063 节点 / 3370 边）。

> 知识图谱回答「谁和谁有关系」，知识树回答「谁从哪里来、该先学谁、在哪门课里」——二者合起来才是中医药知识的完整结构。

| 资产 | 说明 |
|---|---|
| 构建器 | `scripts/build_knowledge_tree.py`（单一构建点，源变更重跑即可） |
| 生成物 | `kg/tree/tcm-knowledge-tree.json` · `kg/tree/schema.json` |
| 查询引擎 | `kg/tree/tcm_tree.py`（零依赖 CLI/库） |
| 平台 API | `api/tree_router.py` → `/tree/*`（挂载于 sage-api） |
| 自检 | `scripts/verify_knowledge_tree.py`（24 项） |
| 部署 | `scripts/deploy-knowledge-tree.ps1`（开发机 → 华为云） |
| 说明 | [`kg/tree/README.md`](kg/tree/README.md) |

```bash
python scripts/build_knowledge_tree.py      # 构建（8域/120学科/2489章节叶/103病证单元）
python scripts/verify_knowledge_tree.py     # 24 项自检
python kg/tree/tcm_tree.py path DSU-00001   # 根→域→学科→单元 定位
```

线上：`https://www.zyyywaccn.com.cn/api/sages/tree/stats`

## 中医信息学 · 平台信息结构（v1.0.0）

> 知识树管**组织**（谁从哪里来），信息学管**运算**（怎么编码、怎么检索、怎么挖出规律）。

`kg/informatics/` 以平台真实资产（103 病证单元 / 31,838 ICD-11 实体 / 120 学科 / 84 技能）现算
**S 信息标准 × A 数据资产 × M 信息挖掘算子** 三层结构，产物确定性、可校验。

| 能力 | 端点 | 实测 |
| --- | --- | --- |
| 统计概览 | `GET /api/sages/informatics/stats` | 103 单元 · 96 证候 · 45 规则 |
| 信息标准 / 资产 / 算子 | `/standards` `/assets` `/operators` | 5 / 4 / 7 |
| 频次分布 | `/dist/{key}` | 六经 · 证据 · 分类 … |
| 关联规则（support/confidence/lift） | `/rules/{kind}` | 症状→证候 · 证候→方剂 · 脏腑→方剂 |
| 证候聚类 / 编码覆盖 / 数据质量 | `/clusters` `/coverage` `/quality` | 覆盖 74/103 · 质量 36 项 |
| 检索（TF-IDF ⊕ FTS5 ⊕ RRF） | `/retrieve?q=` | 向量 + FTS5 + RRF 融合 |

- 构建：`python scripts/build_informatics.py`（单一构建点，两次构建字节一致）
- 自检：`python scripts/verify_informatics.py`（27 项）
- 部署：`powershell -File scripts/deploy-informatics.ps1`
- 教材素材：桌面 `中医信息学.xlsx`（23 sheet · D07-S02 / AI-02）
- 详文档：`kg/informatics/README.md`