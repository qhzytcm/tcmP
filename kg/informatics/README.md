# 中医信息学 · TCM Informatics

> **tcmP 中医药网络教育平台的「信息结构」层** —— 把中医药知识变得**可编码、可检索、可挖掘、可装配**。
> `v1.0.0` · S 信息标准 × A 数据资产 × M 信息挖掘算子 · 覆盖 103 病证单元 / 31,838 ICD-11 实体 / 120 学科 / 84 技能

---

## 一、为什么中医需要「信息学」，而它不止于「信息检索」

中医药知识要进医院、进医保、进教材、进 AI，必须先解决三件事：**统一编码**（病历/医保能对上号）、**结构化表示**（机器能读）、**可挖掘**（能从数据里发现规律）。这三件事合起来就是中医信息学。

它不是「把书扫描成 PDF」，也不是「做个全文搜索」。中医信息学 = **信息标准 × 数据资产 × 信息挖掘算子**：

| 层 | 内容 | 平台落地 |
| --- | --- | --- |
| **S 信息标准** | ICD-11 TM1/MMS、GB/T 病证分类、ISO/TC 215 术语、DSU 六段式 Schema | `icd11_mms.db` + `/icd/*` 三端点；`kg/schema/schema.json` |
| **A 数据资产** | 病证单元语料、编码库、学科目录、技能目录 | `kg/samples/*`(103) · `icd11_mms.db`(31,838) · `tcmP-subjects.json`(120) · `catalog.json`(84) |
| **M 信息挖掘** | 频次分布 · 关联规则 · 证候聚类 · 编码覆盖 · 数据质量 · 检索 · 上下文装配 | `kg/informatics/tcm_mining.py` |

> **与「知识树」的分工**：`kg/tree`（中医知识树）回答「知识怎么组织、谁从哪里来」；`kg/informatics`（中医信息学）回答「数据怎么编码、怎么检索、怎么挖出规律」。前者是**结构**，后者是**运算**。

---

## 二、真实挖掘结果（本仓库现算，可复现）

构建器 `scripts/build_informatics.py` 直接读平台语料现算，**确定性**（无 `hash()` 随机，两次构建字节一致）。

| 指标 | 值 |
| --- | --- |
| 病证单元（DSU） | **103** |
| 不同证候 / 西医病 / 主方 / 症状 | 96 / 99 / 96 / **396** |
| ICD-11 编码覆盖 | **74 / 103（71.8%）** |
| 关联规则（3 类） | **45** 条 |
| 证候聚类（重叠系数 ≥0.5） | 1 族 |
| 数据质量问题 | **36** 项 |

### 2.1 频次分布（M1）

| 维度 | Top |
| --- | --- |
| 六经 | 少阴病 24 · 太阴病 20 · 不适用 16 · 少阳病 15 · 太阳病 9 |
| 证据等级 | B级 40 · C级 31 · A级 26 · D级 4 |
| 桥接类型 | 机制对应 51 · 间接对应 30 · 直接对应 14 · 阶段对应 8 |
| 西医分类 | 消化 15 · 循环 13 · 神经 11 · 呼吸 10 |
| 主症 | 神疲乏力 5 · 胸闷胸痛 4 · 腰膝酸软 3 · 心悸气短 3 |

### 2.2 关联规则（M2，support/confidence/lift）

| 规则 | support | confidence | lift |
| --- | :-: | :-: | :-: |
| PSA升高 → 肾虚瘀毒证(癃闭/积证) | 0.0097 | 1.0 | 103.0 |
| 一侧三叉神经分布区疼痛 → 肝火上炎、风火上扰证 | 0.0097 | 1.0 | 103.0 |
| 一侧腰臀至下肢后外侧放射性疼痛 → 寒湿阻络、气滞血瘀证 | 0.0097 | 1.0 | 103.0 |

> ⚠️ **教学要点**：lift=103 并非强关联，而是 `1/(1/103)` 的数学必然——小语料里**每个症状只出现一次**，support 极低。**必须先用 support 阈值过滤，再看 lift**，否则会被「虚假高提升度」误导。这正是信息挖掘最经典的陷阱。

### 2.3 证候聚类（M3）

症状集稀疏（396 症状 / 103 单元），Jaccard 过低；改用**重叠系数** Overlap = |A∩B| / min(|A|,|B|) ≥ 0.5 后得到：

- `气阴两虚证（消渴）` × `阴虚燥热证` —— 同为消渴（糖尿病）证候族，临床可互参。

### 2.4 编码覆盖与数据质量（M4/M5）

| 问题字段 | 数量 | 说明 |
| --- | :-: | --- |
| `icd11_code` 缺失 | 29 | 覆盖率 71.8%，需补编码（内网 API 或本地 db） |
| `six_channels` 越界 | 6 | 合病/过渡变体（如「太阳病 — 阳明病（过渡）」）不在七值枚举 |
| `evidence_level` 越界 | 1 | 出现 `I级-专家共识`，应为 `E级-专家共识`（**枚举错别字**） |

> 数据质量门禁（M5）把「I级→E级」这类**人工录入错误**自动暴露——这是信息学在教材生产中的直接价值。

---

## 三、信息挖掘引擎（`tcm_mining.py`，零依赖）

```bash
python kg/informatics/tcm_mining.py summary                 # 统计
python kg/informatics/tcm_mining.py standards | assets | operators
python kg/informatics/tcm_mining.py dist six_channel        # 任一维度分布
python kg/informatics/tcm_mining.py rules symptom_to_syndrome
python kg/informatics/tcm_mining.py clusters | coverage | quality
python kg/informatics/tcm_mining.py retrieve "失眠 多梦"      # 向量 + FTS5 + RRF
```

检索实现「embedding code」三件套：

| 组件 | 实现 | 说明 |
| --- | --- | --- |
| 向量化 | 字符 bigram **TF-IDF**（纯 stdlib） | 内网零 token；升级路径 BGE 语义向量 |
| 全文召回 | 词集重叠（对标 SQLite **FTS5**） | 线上由 `tcm_embed.py` 用真 FTS5 |
| 融合 | **RRF**（倒数排序，k=60） | 向量 Top-K ∪ FTS Top-K |

---

## 四、平台 API（挂载于 sage-api）

| 端点 | 作用 |
| --- | --- |
| `GET /informatics/stats` | 统计概览 |
| `GET /informatics/standards` `/assets` `/operators` | 标准 / 资产 / 算子 |
| `GET /informatics/dist/{key}` | 任一维度频次分布 |
| `GET /informatics/rules/{kind}` | 关联规则（3 类） |
| `GET /informatics/clusters` `/coverage` `/quality` | 聚类 / 覆盖 / 质量 |
| `GET /informatics/retrieve?q=` | TF-IDF+FTS5+RRF 检索 |

线上：`https://www.zyyywaccn.com.cn/api/sages/informatics/*`

---

## 五、构建与部署

```bash
python scripts/build_informatics.py        # 单一构建点（读 DSU 语料现算）
python scripts/verify_informatics.py        # 自检
python -m pytest tests/test_informatics.py  # 契约测试
powershell -File scripts/deploy-informatics.ps1   # 华为云 sage-api（幂等挂载 /informatics/*）
```

---

## 六、与 tcmP 其他层的关系

| 层 | 路径 | 关系 |
| --- | --- | --- |
| 病证知识图谱 | `kg/samples` | 本层的**数据资产**（DSU 语料） |
| 中医知识树 | `kg/tree` | 姊妹结构：树管**组织**，信息学管**运算** |
| Embedding 引擎 | `scripts/tcm_embed.py` | 线上检索实现（FTS5+RRF 真身） |
| ICD-11 桥接 | `/icd/*` · `icd11_mms.db` | 本层 M4 编码覆盖的**标准源** |
| 教材 120 学科 | `data/tcmP-subjects.json` | D07-S02《中医信息学》即本层对应课程 |

---

## 七、里程碑

| 阶段 | 版本 | 目标 | 状态 |
| :-: | :-: | --- | :-: |
| I1 | v1.0.0 | S×A×M 三层 + 挖掘引擎 + `/informatics/*`（103 语料现算） | ✅ 本次 |
| I2 | v1.1.0 | ICD-11 覆盖补齐至 ≥95%；合病/过渡变体枚举扩展 | 规划 |
| I3 | v1.2.0 | 纳入教材与技能数据资产；跨语料（方剂/中药）挖掘 | 规划 |
| I4 | v2.0.0 | 与知识树双向绑定；挖掘结果回流教学内容 | 规划 |

<p align="center"><sub>本 README 与 <code>kg/informatics/</code> 全部产物由 <code>scripts/build_informatics.py</code> 驱动 —— 单一构建点，可复现，可校验。</sub></p>