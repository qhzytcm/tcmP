# 病证单元 Embedding 引擎 — 架构与技术扩展

> **论著依据**：Cremaschi et al., *Decoding the mind: A RAG-LLM on ICD-11 for decision support in psychology*, Expert Systems with Applications 279 (2025) 127191（ESWA, DOI: 10.1016/j.eswa.2025.127191）
> **版本**：v3.0（2026-08-04）| **落地位置**：`scripts/tcm_embed.py` + `api/main.py`（/diag /bianzheng /semantic-search /rag）

---

## 一、论著方法理解（LLMind Chat RAG 管线）

| 论著步骤 | 方法 | tcmP 落地 |
|:--------|:-----|:----------|
| 数据集构建 | ICD-11 API（官方 Docker 容器）→ JSON→CSV；合并 ICD-11-CDDR 诊断标准（按 code join）；每障碍生成单文本 **prompt/Document** 字段 | kg/samples 103 个病证单元(DSU) → **build_document()** 合并病侧+证侧+方药为单文本 |
| 向量化 | LangChain embeddings（Ollama 本地 embedding 模型） | **TF-IDF 字符 n-gram**（零依赖）→ 预留 **BGE-small-zh 语义向量**（见 §四） |
| 存储 | ChromaDB 向量库 | 内存稀疏向量 + SQLite **FTS5** 全文索引 |
| 检索 | 余弦相似度 **Top-4**（经验值） | 余弦相似度 Top-K（RRF 融合 FTS5 召回） |
| 上下文 | Top-4 障碍文档注入 LLM | Top-K 病证单元注入 DeepSeek（可选） |
| 生成 | Gemma 2 27B（Ollama）生成诊断 | DeepSeek 生成诊断报告（**仅消费小上下文**） |
| 评估 | DSM-5-TR 104 案例，专家验证，**76% 准确率** | 病证单元金标准交叉验证（见 §五） |

**核心范式（embedding 编程）**：
```
Document(text) --embed--> vector ──┐
                                    ├─> 余弦相似度 ─> Top-K ─> 上下文 ─> LLM 诊断
Query(text)   --embed--> vector ──┘      （同空间）
```

---

## 二、疾病诊断流程（diagnose）

```
输入症状（如：恶寒,发热,无汗）
  → tokenize（中文 bigram + 英文词）
  → TF-IDF 向量化（与 DSU 文档同空间）
  → 余弦相似度 Top-K 病证单元（RRF 融合 FTS5 关键词召回）
  → 输出：疾病名 + ICD-11 编码 + 证候 + 方剂 + 证据分数
```
实测：`恶寒,发热,无汗` → **CA00 普通感冒（风寒束表证→麻黄汤）**，score 0.52

## 三、证候辨证流程（bianzheng）— 支撑病证单元

```
输入症状（如：口苦,咽干,胁肋胀痛）
  → 同空间向量化 → Top-K DSU（证候侧加权）
  → 输出：证候名 + 脏腑 + 六经 + 推荐方剂
```
实测：`口苦,咽干,胁肋胀痛` → **肝胆湿热证（肝·胆/少阳）→ 茵陈蒿汤合龙胆泻肝汤**

**病证单元闭环**：DSU = 病侧（病名+ICD-11 编码+分子靶点）× 证侧（证候+六经+八纲）× 临床（方/穴/调护）——诊断流程锚定病侧、辨证流程锚定证侧，两端收敛到同一 DSU，完全支撑平台"病证单元"逻辑。

## 四、技术扩展路线（可持续升级）

### 4.1 语义向量搜索（升级：TF-IDF → BGE）
- **现状**：TF-IDF 字符 n-gram（零依赖、零下载、内网运行，103 DSU 检索 <10ms）
- **升级路径**（代码已预留 `self._bge` 接口）：
  1. `pip install torch sentence-transformers`（CPU 版）
  2. 模型：`BAAI/bge-small-zh-v1.5`（512 维，~24M 参数）经 **ModelScope** 下载（hf-mirror 不可达时；modelscope.cn 已验证可达）
  3. 替换 `TfidfIndex` → `SentenceTransformer.encode()`，余弦不变
  4. 收益：同义表达（"口苦"/"口中泛苦"）语义召回，摆脱字面匹配

### 4.2 FTS5 全文索引（已落地）
- SQLite `FTS5` 虚拟表：dsu_id/disease/syndrome/symptoms/formula/text 六列
- 查询 tokenize 后 `MATCH` 布尔检索 → 关键词级精确召回
- 与向量分数 **RRF（Reciprocal Rank Fusion）融合**：`rrf = Σ 1/(k+rank)`
- 可扩展：FTS5 `highlight()` 片段高亮、`snippet()` 摘要

### 4.3 内网支撑降 token（核心收益）

| 场景 | 无内网检索（纯 LLM） | 内网 embedding 检索（本引擎） |
|:-----|:---------------------|:------------------------------|
| 全库提示注入 | 103 DSU × ~300 token ≈ **31K token/次** | Top-5 ≈ **1.5K token/次**（↓95%） |
| 检索成本 | LLM 自读全库（慢、贵、易错） | 本地向量余弦 <10ms，**零 token** |
| 辨证推理 | 需 LLM 推理 | 本地检索直接给证候+方剂（零 token） |
| RAG 报告 | — | 仅 Top-K 上下文 + LLM 精修（~800 token） |

**结论**：常规诊断/辨证/搜索走本地检索（零 token）；仅需报告/鉴别诊断时才调 LLM 精修——token 消耗降低一个数量级，且数据不出内网。

### 4.4 后续可升级点
1. **向量库持久化**：`vectors.npy` + `docs.json` 落盘（当前内存构建 <1s，量级上来后再持久化）
2. **增量索引**：DSU 新增时局部重建
3. **多路召回**：BGE 语义 + TF-IDF 字面 + FTS5 关键词 + ICD-11 编码精确匹配，RRF 四路融合
4. **Agent 联动**：六者 Agent chat 中注入 `diagnose()/bianzheng()` 检索结果作为 tool 输出（替代部分 LLM 推理）
5. **评估闭环**：以 103 DSU 为金标准，症状扰动测试 Top-1 命中率，纳入 CI

---

## 五、验证记录（2026-08-04）

| 端点 | 输入 | 输出 | 结果 |
|:-----|:-----|:-----|:----:|
| GET /diag | 恶寒,发热,无汗 | CA00 普通感冒 · 风寒束表证 → 麻黄汤 | ✅ 本地+公网 |
| POST /bianzheng | 口苦,咽干,胁肋胀痛 | 肝胆湿热证 → 茵陈蒿汤合龙胆泻肝汤 | ✅ 本地+公网 |
| GET /semantic-search | 咳嗽,痰黄,气喘 | 肺癌/肺炎/支气管炎 Top3 | ✅ 公网 |
| POST /rag | 失眠多梦,心悸,健忘,神疲 | Top3 检索 + DeepSeek 报告（鉴别诊断表） | ✅ 公网 |
| 部署 | 华为云 /var/www/tcm-dashboard | 引擎 103 DSU + FTS5 就绪 | ✅ v3.0 |

## 六、文件清单

| 文件 | 说明 |
|:-----|:-----|
| `scripts/tcm_embed.py` | 引擎：Document 构建 / TF-IDF 向量 / FTS5 / 余弦+RRF / diagnose / bianzheng / rag |
| `api/main.py` | /diag /bianzheng /semantic-search /rag 四端点（懒加载引擎） |
| `scripts/deploy-v3.sh` | 华为云一键部署（key 注入+编译+引擎自检+重启） |
| `kg/samples/*.json` | 103 病证单元数据源（已含 ICD-11 标注） |
