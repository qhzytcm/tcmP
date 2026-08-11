# 病证检索与文本表示：手写 TF-IDF

> **药有君臣佐使，词有权重高低。**
> 检索的本质不是"找相同的字"，而是"知道哪些词更值得信"——正如方剂中并非每味药等量。

**类型:** Build
**语言:** Python（纯标准库，零依赖）
**前置:** 轮次1「Python 与数据基础 / 中医数据形态」，或具备基础 Python 能力
**学时:** ~90 分钟
**关联:** tcmP `/api/sages/semantic-search` · `tcmP/scripts/tcm_embed.py` · 病证单元库 `tcmP/kg/samples/`（103+ 病证单元）

## 学习目标

- 解释 TF-IDF 三要素（分词 / 词频 / 逆文档频率）的直觉与公式
- 用纯标准库实现中文 bigram 分词 + TF-IDF 向量 + 余弦相似度检索
- 在真实病证数据上验证检索效果（「恶寒重发热轻无汗」→ 普通感冒 Top1）
- 对照生产引擎与线上端点，说清 FTS5 全文召回 + RRF 融合的动机
- 理解检索的局限：词面重叠导致跨病种干扰（失眠 vs 高血压）

## 问题（The Problem）

门诊带教场景：老师让学生从既往病案库检索"与本案相似"的病案。学生用关键词 **「难以入睡」** 去搜，却搜不到内容为 **「失眠多梦」** 的病案——**字面匹配失效**。

这不是搜索框的错，而是检索模型的问题：

| 现象 | 根因 |
|------|------|
| 「难以入睡」搜不到「失眠多梦」 | 患者表述千变万化，字面不重叠但语义相关 |
| 搜「痛」返回上千条 | 单字/泛词没有判别力，无法区分病种 |
| 长病案 vs 短病案排序混乱 | 没有统一的"文本 → 数值"度量，无法比较 |

不解决"文本怎么变成可比较的数值"，平台的辨证、导诊、鉴别诊断就都是空中楼阁——**检索是平台一切智能问答的地基**。

## 概念（The Concept）

### 三步：把文本变成向量

```
文本 → ① 分词（切成检索原子） → ② 加权（TF × IDF） → ③ 向量化（归一化）
                                                          ↓
                         查询文本同样处理 → 余弦相似度排序 → Top-K
```

### ① 分词：检索的最小单位

中文没有天然空格。零依赖的最简可工作方案是**字符 bigram**（相邻两字）：

```
「心烦不安」 → [心烦, 烦不, 不安]
```

牺牲一点精确性，换取：未登录词也切得开、实现 5 行、与生产引擎 `tcm_embed.tokenize` 完全同算法。

### ② 加权：TF × IDF——君臣佐使的直觉

| 概念 | 公式 | 直觉（方剂类比） |
|------|------|-----------------|
| **TF** 词频 | 词在本文档出现次数 | 一味药在方中反复出现，说明它是主药 |
| **DF** 文档频率 | 词出现在多少篇文档 | 多少张方子都用了这味药 |
| **IDF** 逆文档频率 | `log((N+1)/(df+1)) + 1` | 稀有药（专病专药）判别力强；广谱药谁都认识，不能用来定位 |
| **TF-IDF** | `TF × IDF` | 主药 × 专病专药 → 这篇文章真正"在说什么" |

关键直觉：**「症状」「患者」这类所有文档都有的词，IDF 趋近 1（约等于没权重）；「哮鸣」「五心烦热」这类专病词，IDF 高达 2+（强判别力）**。检索不是找字，而是找"谁更独特地属于你"。

### ③ 相似度：余弦

两篇文档的向量夹角越小越相似：

```
cosine(a, b) = dot(a, b) / (||a|| × ||b||)
```

向量先做 L2 归一化，余弦就退化为点积——代码里省一步。

## 从零实现（BUILD IT）

> 完整可运行代码：`code/main.py`（约 200 行）。以下为关键切片。

### 步骤 1：分词

```python
def tokenize(text):
    """英文整词；中文连续段拆字符 bigram"""
    text = (text or "").lower()
    toks = []
    for w in re.findall(r"[a-z0-9]{2,}", text):
        toks.append(w)
    for seg in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(seg) == 1:
            toks.append(seg)
        else:
            toks += [seg[i:i + 2] for i in range(len(seg) - 1)]
    return toks
```

### 步骤 2：文档频率 → IDF

```python
# 文档频率：词出现在多少篇文档（按文档去重）
for toks in doc_tokens:
    for t in toks:
        self.df[t] = self.df.get(t, 0) + 1
# 逆文档频率：+1 平滑防除零；df=N（人人都有）→ idf=1；df=1 → ≈ log(N)+1
self.idf = {t: math.log((self.n_docs + 1) / (f + 1)) + 1
            for t, f in self.df.items()}
```

### 步骤 3：TF-IDF 向量 + 归一化

```python
def _vector_of(self, toks):
    tf = {}
    for t in toks:
        tf[t] = tf.get(t, 0) + 1
    norm = math.sqrt(sum((v * self.idf[t]) ** 2 for t, v in tf.items())) or 1
    return {t: v * self.idf[t] / norm for t, v in tf.items()}
```

### 步骤 4：余弦相似度（稀疏向量技巧）

```python
def cosine(self, a, b):
    if not a or not b:
        return 0.0
    small, large = (a, b) if len(a) < len(b) else (b, a)  # 遍历短的一侧
    return sum(small[t] * large[t] for t in small if t in large)
```

### 步骤 5：检索

```python
def search(query, idx, docs, top_k=3):
    qv = idx.vectorize(query)
    scored = [(idx.cosine(qv, dv), i) for i, dv in enumerate(idx.vectors)
              if idx.cosine(qv, dv) > 0]
    scored.sort(reverse=True)
    return [docs[i] for _, i in scored[:top_k]]
```

### 运行与自检

```bash
python code/main.py --self-test      # ✅ 5 项断言：分词/IDF排序/感冒Top1/失眠Top1/余弦性质
python code/tests.py                 # ✅ 6/6 确定性测试
```

## 平台实现（USE IT）

同一件事，看平台的生产版本怎么跑。**以下全部为本课实测输出。**

### 对照 1：手写版 × 内置 5 条 mini 语料

```console
$ python code/main.py "难以入睡 多梦易醒 心烦不安" --top-k 3
═══ 手写 TF-IDF 检索「难以入睡 多梦易醒 心烦不安」═══
  1. [0.4720] 原发性失眠（慢性失眠障碍） (7A00) — 心肾不交证 → 黄连阿胶汤合交泰丸
  2. [0.0892] 原发性高血压 (BA00) — 肝阳上亢证 → 天麻钩藤饮
```

**注意 Top2**：高血压（肝阳上亢证）的症状里恰好也有「失眠多梦」——**词面重叠导致跨病种干扰**。这正是本课要建立的"检索局限"意识。

### 对照 2：手写版 × 全量 103 病证语料

```console
$ python code/main.py "难以入睡 多梦易醒 心烦不安" --top-k 3 --data ../../tcmP/kg/samples
📚 全量语料：103 个病证单元
  1. [0.5883] 原发性失眠（慢性失眠障碍） (7A00) — 心肾不交证 → 黄连阿胶汤合交泰丸
  2. [0.1156] 原发性高血压 (BA00) — 肝阳上亢证 → 天麻钩藤饮
  3. [0.0571] 心律失常 (MC81) — 心脾两虚证 → 炙甘草汤
```

语料从 5 扩到 103，Top1 分数 0.4720 → **0.5883**：IDF 在更大语料上统计更准，相似度对比更锐利。

### 对照 3：生产引擎 tcm_embed.py（同算法 + FTS5 + RRF）

```console
$ python tcmP/scripts/tcm_embed.py 难以入睡 多梦易醒 心烦 --mode diagnose --top-k 3
═══ 疾病诊断「难以入睡，多梦易醒，心烦」═══
  1. 原发性失眠（慢性失眠障碍） [7A00] — 向量 0.488 + FTS 0
  2. 原发性高血压 [BA00] — 向量 0.122 + FTS 0
  3. 心律失常 [MC81] — 向量 0.060 + FTS 0
```

> ⚠️ 注意：tcm_embed.py 必须用 **hermes venv python**（`C:\Users\DELL\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`）运行——系统 Anaconda Python 的 SQLite 缺 FTS5 支持，会段错误崩溃（退出码 0xC0000005）。

### 对照 4：线上端点（六者平台）

```bash
curl 'https://www.zyyywaccn.com.cn/api/sages/semantic-search?q=失眠多梦&top_k=2'
```

```json
{"mode":"semantic_search","symptoms":["失眠多梦"],
 "results":[
   {"dsu_id":"DSU-00035","disease":"心律失常","icd11_code":"MC81",
    "syndrome":"心脾两虚证","formula":"炙甘草汤","score":0.3043,
    "evidence":"向量 0.304 + FTS 0"},
   {"dsu_id":"DSU-00008","disease":"原发性高血压","icd11_code":"BA00",
    "syndrome":"肝阳上亢证","formula":"天麻钩藤饮","score":0.2871,
    "evidence":"向量 0.287 + FTS 0"}]}
```

### 四表合一：你学到了什么

| 版本 | 语料 | Top1 | Top1 分数 | 额外机制 |
|------|------|------|:---------:|---------|
| 手写版 | 5 条 mini | 原发性失眠 | 0.4720 | 无 |
| 手写版 | 103 条全量 | 原发性失眠 | 0.5883 | 无（IDF 更准） |
| 生产引擎 | 103 条全量 | 原发性失眠 | 0.4880 | FTS5 召回 + RRF 融合 |
| 线上端点 | 线上库（规模≥本地） | 心律失常 | 0.3043 | 同上（查询词不同） |

**两个真实观察：**

1. **排序会随语料规模与查询表达漂移**——线上查「失眠多梦」Top1 是心律失常，本地查「难以入睡 多梦易醒 心烦不安」Top1 是失眠。检索结果从来不是"唯一正确答案"，而是"候选集"。这就是为什么平台的输出始终是 Top-K 候选 + 辨证流程，而不是武断结论。
2. **`FTS 0` 是真实的产品观察**：FTS5 默认 unicode61 分词器把整段中文当一个 token，「失眠」这类内部子串短语匹配不到，所以关键词召回经常空手而归。中文检索没有银弹——向量语义 + 关键词召回互补，正是生产引擎引入 **RRF 融合（倒数秩融合）** 的原因。

## 交付制品（SHIP IT）

| 制品 | 文件 | 用途 |
|------|------|------|
| 病证检索助手 skill | `outputs/skill-dsu-retrieval.md` | 封装 `/semantic-search` 标准调用，可装入医者/患者 Agent |
| 鉴别诊断提示词 | `outputs/prompt-differential-diagnosis.md` | 检索 Top-K → LLM 综合 → 规范化鉴别诊断报告 |

## 习题（60-30-10）

1. **基础**：用自己的话解释 IDF 为什么给罕见词更高权重？「患者」「症状」的 IDF 应该高还是低？
2. **综合**：用 `code/main.py --data ../../tcmP/kg/samples` 检索「胸闷 心悸 气短」，对比结果与「难以入睡」的 Top3，说明哪些词贡献了区分度。
3. **拓展**：阅读 `tcmP/scripts/tcm_embed.py` 的 `_rrf_fuse`（约 14 行），解释为什么 `1/(k+rank+1)` 的融合公式能让"向量第 1 名 + FTS 第 8 名"胜过"向量第 5 名 + FTS 未命中"。

## 术语表

| 术语 | 常见误解 | 实际含义 |
|------|---------|---------|
| TF-IDF | 一种神经网络模型 | 词频 × 逆文档频率的统计加权，衡量词对文档的代表性 |
| IDF | 词越少见越重要 | 稀有度代表判别力；但"少见"指在**语料**中少见，非直觉上的生僻 |
| 语义检索 | 检索能理解意思 | 本质仍是词面统计相似度；"语义"来自相似症状共享高频词 |
| FTS5 | 中文检索的答案 | SQLite 全文索引；默认分词器对中文整段成一个 token，短语召回常失效 |
| RRF | 排序后重打分 | 倒数秩融合：把多路排序（向量 + 关键词）按名次合并，不依赖分数可比 |

## 延伸阅读

- `tcmP/scripts/tcm_embed.py`（326 行）——生产引擎全源码：`build_document` → `TfidfIndex` → `FTS5Index` → `_rrf_fuse` → `diagnose/bianzheng/rag`
- Cremaschi et al., *Decoding the mind: A RAG-LLM on ICD-11* (ESWA 2025)——本引擎的范式源头：文档构建 → embedding → 余弦 Top-K → 决策输出
- ai-engineering-from-scratch（rohitg00）Phase 11 · Lesson 06 RAG——同一教学法（先手写 TF-IDF，再上生产框架）的英文完整版
- 下一课预告：**「RAG 与病证知识问答」**——本课的 Top-K 检索将接上 LLM，形成完整的 `诊断 → 辨证 → 方剂建议` 问答链（对应 `/api/sages/rag`）
