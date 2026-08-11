# 倒排索引与 RRF 融合：让检索既快又准

> **查方如查词，先翻目录，再翻全书。**
> 倒排索引就是那本"词 → 页码"的书后索引；RRF 则是多位老药工把各自排名"合计"出最终意见的智慧——各有所长，按名次投票。

**类型:** Build
**语言:** Python（纯标准库，零依赖）
**前置:** Lesson 1「病证检索与文本表示：手写 TF-IDF」（本课复用其 `tokenize` / `TfidfIndex`）
**学时:** ~90 分钟
**关联:** tcmP `tcmP/scripts/tcm_embed.py`（`FTS5Index` + `_rrf_fuse`）· `/api/sages/semantic-search`

## 学习目标

- 实现倒排索引（词 → 文档集合），理解查询复杂度从 O(N) 降到 O(命中词条数)
- 区分 OR 并集（recall 优先）与 AND 交集（precision 优先）的语义
- 实现 RRF 倒数秩融合（`score = Σ 1/(k+rank_i)`），理解"只看名次不看分数"的原因
- 组装混合检索：向量 Top-K + 关键词召回 → RRF 融合，并识别双路命中标记
- 理解融合分打平时的破局机制（tiebreaker），对齐生产引擎排序

## 问题（The Problem）

Lesson 1 的检索有两个痛点，全量病证库（60,000+ 单元）下会放大：

**痛点一：慢。** 每查一次就要跟所有文档算一遍余弦。实测（本课对照 3）：103 条语料全扫约 0.9-1.0ms/次；扩到 6 万条就是约 0.5 秒/次，平台每个查询都要排队——不可接受。

**痛点二：单一信号不可靠。** 语义词（"难以入睡"）向量抓得好，但词面精确的查询（"麻黄汤"）被泛词稀释；反过来关键词精确匹配又会漏掉语义相关的表述（Lesson 1 的跨病种干扰）。**没有一路检索是银弹**——需要"多路互补 + 融合"。

## 概念（The Concept）

### 倒排索引：为查询而生的"书后索引"

```
正向（建库时）:  文档 → [词, 词, ...]      一遍扫描即可
倒排（查询时）:  词 → [文档1, 文档3, ...]   查询 = 按词取列表
```

| 查询方式 | 复杂度 | 类比 |
|---------|--------|------|
| 全库扫描 | O(N) | 每查一个词翻一遍全书 |
| 倒排索引 | O(命中词条数) | 先翻书后索引，直接翻到对应页 |

查询时两种合并模式：

| 模式 | 语义 | 结果特征 |
|------|------|---------|
| OR 并集 | 含任一查询词即召回 | recall 高、噪声多 |
| AND 交集 | 含全部查询词才召回 | precision 高、易漏检 |

### RRF：多路排序怎么合成一路

两路排序（向量余弦分数、关键词命中次序）**量纲不同，分数不可直接相加**。RRF 的解法：把每路都降维成名次，融合分 = 各路人次的倒数秩之和：

```
score(d) = Σ_rank  1 / (k + rank_i)      k = 60（经验常数）
```

| 情形 | 向量名次 | 关键词名次 | 融合分 |
|------|:--------:|:----------:|:------:|
| 文档A | 1 | 1 | 1/61 + 1/61 ≈ 0.0328 |
| 文档B | 2 | 2 | 1/62 + 1/62 ≈ 0.0323 |
| 文档C | 1 | 未命中 | 1/61 ≈ 0.0164 |

两路都靠前的文档（A）融合分最高——**语义与词面互相印证**。k=60 的作用：压缩第一名优势（1/61 vs 1/62 只差 1.6%），避免某一路的首名霸权。

## 从零实现（BUILD IT）

> 完整可运行代码：`code/main.py`（约 350 行，含 4 个演示场景）。关键切片如下。

### 步骤 1：倒排索引（本课核心 1）

```python
class InvertedIndex:
    """词 → 文档 ID 集合（posting list）"""
    def __init__(self):
        self.postings = {}   # term -> set(doc_idx)

    def build(self, texts):
        """建库：每篇文档分词去重，词指向文档 ID"""
        for i, text in enumerate(texts):
            for term in set(tokenize(text)):
                self.postings.setdefault(term, set()).add(i)

    def query(self, text, mode="or", limit=None):
        """查询：OR 并集 / AND 交集"""
        terms = [t for t in set(tokenize(text)) if t in self.postings]
        if not terms:
            return []
        if mode == "and":
            hits = set(self.postings[terms[0]])
            for t in terms[1:]:
                hits &= self.postings[t]
        else:
            hits = set()
            for t in terms:
                hits |= self.postings[t]
        return sorted(hits)
```

### 步骤 2：RRF 融合（本课核心 2）

```python
def rrf_fuse(vector_ranked, keyword_hits, k=60, tiebreak=None):
    """只看名次：score(d) = Σ 1/(k + rank_i)"""
    rank = {}
    for i, (idx, _s) in enumerate(vector_ranked):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + i + 1)
    for j, idx in enumerate(sorted(keyword_hits)):
        rank[idx] = rank.get(idx, 0.0) + 1.0 / (k + j + 1)
    tb = tiebreak or {}
    # 融合分打平时用向量分数破局（对齐生产引擎 (-rrf, -vec) 排序）
    return sorted(rank.items(), key=lambda kv: (-kv[1], -tb.get(kv[0], 0.0)))
```

### 步骤 3：混合检索（组装）

```python
def hybrid_search(query, tfidf, inv, docs, top_k=3, k=60):
    qv = tfidf.vectorize(query)
    vec_ranked = sorted(((i, tfidf.cosine(qv, dv)) for i, dv in enumerate(tfidf.vectors)
                         if tfidf.cosine(qv, dv) > 0), key=lambda x: -x[1])
    inv_hits = inv.query(query, mode="or")                    # 关键词路
    fused = rrf_fuse(vec_ranked, set(inv_hits), k,
                     tiebreak={i: s for i, s in vec_ranked})  # 融合路
    ...
```

### 运行与自检

```bash
python code/main.py --demo        # 4 个演示场景（速度/精确词/三路对比/AND vs OR）
python code/main.py --self-test   # ✅ 5 项断言
python code/tests.py              # ✅ 6/6 确定性测试
```

## 平台实现（USE IT）

同一件事，看生产引擎怎么跑。**以下全部为本课实测输出。**

### 对照 1：速度——倒排为什么是必需品

```console
$ python code/main.py --demo --data ../../tcmP/kg/samples     # 103 病证单元
── 场景1 · 速度：全库扫描 vs 倒排索引 ──
  查询词: ['难以', '以入', '入睡']
  计算量: 全扫 103 次余弦 vs 倒排查 8 个条目
  实测耗时: 向量全扫 999µs/次 vs 倒排 4µs/次（226x）
```

> 加速比随机器负载浮动（本课两次实测为 175x / 226x）——数值本身不重要，重要的是**量级**：查询耗时与文档总量解耦。

查询只涉及 3 个词，倒排只查 8 个条目——**耗时与文档总量解耦**。6 万条全量库的理论加速比更高（posting list 长度由词频决定，与库规模无关）。

### 对照 2：精确词「麻黄汤」——倒排的召回完整性

```console
── 场景2 · 精确词「麻黄汤」：两路召回对比 ──
  倒排召回: ['普通感冒（上呼吸道感染）', '支气管哮喘', '急性髓系白血病', '银屑病']
  向量Top2: [('普通感冒（上呼吸道感染）', 0.2615), ('支气管哮喘', 0.2128)]
```

倒排召回 4 条、向量只看前 2——**recall 差异的直接证据**。注意召回里的"支气管哮喘"：它的推荐方剂是**射干麻黄汤**（含"麻黄汤"子串），bigram 分词让"麻黄汤"能部分匹配"射干麻黄汤"；白血病/银屑病则命中了方剂里的"麻黄"（如麻黄升麻汤）。词面匹配既带来召回，也带来噪声——这正是融合排序要处理的。

### 对照 3：语义查询——三路对比与融合平局

```console
── 场景3 · 语义查询「难以入睡 多梦易醒 心烦不安」：三路对比 ──
  纯向量Top3: [('原发性失眠', 0.5883), ('原发性高血压', 0.1156), ('心律失常', 0.0571)]
  倒排召回: ['原发性高血压', '原发性失眠', '心律失常', '抑郁症(抑郁发作)',
             '广泛性焦虑障碍', '失眠症(慢性)']
  RRF融合Top3: [('原发性失眠', 0.0325), ('原发性高血压', 0.0325), ('心律失常', 0.0317)]
```

三个观察：

1. **倒排召回 6 条 > 向量 Top3**：抑郁症、广泛性焦虑障碍等因症状含"失眠多梦"词面被召回——向量路根本看不到它们；
2. **融合分打平**：失眠 = 1/61(向量1) + 1/62(关键词2)；高血压 = 1/62(向量2) + 1/61(关键词1)——**两路互顶，数学上完全对称**。此时需要第三信号破局：生产引擎用向量分数做 tiebreaker（`(-rrf, -vec)` 排序），失眠 0.5883 > 高血压 0.1156，稳居第一；
3. 融合保留了向量路的排序主旋律，同时让关键词路的新候选（抑郁/焦虑）进入候选池——**这就是多路互补**。

### 对照 4：跨病种查询「心悸 失眠」——教学版 vs 生产版

```console
# 教学版混合检索（向量 + 倒排 → RRF）
  1. [RRF 0.0323 | 向量+关键词] 原发性高血压   → 天麻钩藤饮
  2. [RRF 0.0320 | 向量+关键词] 心律失常      → 炙甘草汤
  3. [RRF 0.0318 | 仅关键词]   原发性失眠     → 黄连阿胶汤合交泰丸

# 生产引擎 tcm_embed.py（TF-IDF + FTS5 + RRF，hermes venv python）
═══ 疾病诊断「心悸，失眠」═══
  1. 心律失常 [MC81] — 向量 0.209 + FTS 0
  2. 广泛性焦虑障碍 [6B00] — 向量 0.000 + FTS 1
  3. 甲状腺功能亢进症 [5A02.1] — 向量 0.157 + FTS 0
```

**排序不同，但都在合理范围内**——差异源于实现细节：① 生产版 `build_document` 拼接了病名/ICD/症状/证候/方剂全字段（向量空间不同）；② FTS5 的 unicode61 分词器对中文整段切词，偶发"失眠"独立成 token 命中（`FTS 1`）；③ 教学版字段更精简。**这是本课最重要的工程教训：检索排序不是"标准答案"，而是"候选集的合理排序"——平台输出永远是 Top-K 候选 + 辨证流程，而非武断结论。**

## 交付制品（SHIP IT）

| 制品 | 文件 | 用途 |
|------|------|------|
| 混合检索策略 skill | `outputs/skill-hybrid-retrieval.md` | 语义/关键词双路决策表 + RRF 融合判读 + 置信度分级，可装入医者 Agent |
| 查询改写提示词 | `outputs/prompt-query-rewrite.md` | 口语主诉 → {语义词, 精确词} 双路查询，最大化召回质量 |

## 习题（60-30-10）

1. **基础**：用自己的话解释倒排索引为什么查询快？「麻黄汤」查询在 6 万条库上的耗时由什么决定？
2. **综合**：用 `python code/main.py --demo --data ../../tcmP/kg/samples` 观察场景 4（AND vs OR），解释为什么 OR 会召回社区获得性肺炎、急性胆囊炎。
3. **拓展**：阅读生产引擎 `tcm_embed.py` 的 `_rrf_fuse` 与 `_vector_rank`，对比本课 `hybrid_search`：为什么生产版取向量 `top_k*3` 作为融合候选，而不是全部文档？（提示：融合复杂度与候选数成正比）

## 术语表

| 术语 | 常见误解 | 实际含义 |
|------|---------|---------|
| 倒排索引 | 一种数据库 | 词 → 文档集合的映射表，查询 O(词条数) 而非 O(N) |
| FTS5 | 中文检索的答案 | SQLite 全文索引（工业倒排）；默认分词器对中文整段切词，短语召回常失效 |
| RRF | 加权平均 | 倒数秩融合：Σ 1/(k+rank)，只看名次不看分数 |
| tiebreaker | 无所谓 | 融合分打平时的破局信号（本课用向量分数，对齐生产引擎） |
| recall / precision | 一回事 | 召回率（该中的都中）vs 精确率（中的都对）；OR 偏 recall，AND 偏 precision |

## 延伸阅读

- `tcmP/scripts/tcm_embed.py`（326 行）——`FTS5Index.search`（L144-155）与 `_rrf_fuse`（L200-213）为生产版对照源码
- Cormen et al. *Introduction to Algorithms* 倒排索引章节（信息检索基础）
- ai-engineering-from-scratch（rohitg00）Phase 5 · Lesson 14 Information Retrieval & Search
- 下一课预告：**「RAG 与病证知识问答」**——混合检索的 Top-K 接上 LLM，形成 `诊断 → 辨证 → 方剂建议` 问答链（对应 `/api/sages/rag`）
