# 中医知识树 · TCM Knowledge Tree

> **tcmP 中医药网络教育平台的统一知识结构 —— 树图一体**
> 把「教材（120 门学科）、病证知识图谱、ICD-11 编码、六者 Agent、医圣成长」编织成**一棵可导航的树**，同时保留**一张可推理的图**。
> `v1.0.0` · 3063 节点 · 3370 边 · 8 域 / 120 学科 / 2489 章节叶 / 103 病证单元 / 84 技能挂点

---

## 一、为什么要「知识树」，而不止「知识图谱」

tcmP 平台已有的知识资产是**网络形态**的：病证知识图谱（DSU）、ICD-11 编码桥、Embedding 检索。
但中医药知识天然有**两层结构**，缺一不可：

| 维度 | 中医药知识的本相 | 单一「知识图谱」的缺口 | 「中医知识树」的补位 |
| --- | --- | --- | --- |
| **层次** | 阴阳 → 五行 → 藏象 → 经络 → 证候 → 方药（正统的从属与递进） | 图谱是扁平的节点-边，**看不出层级与教学先后** | 须—根—干—枝—叶 **五级骨架**，天然承载「从属 / 递进 / 教学顺序」 |
| **关系** | 生克、乘侮、方证对应、君臣佐使、引经报使、六经传变（跨域织网） | 只有图谱能表达 | 树之外再挂**跨枝经脉图边**，保留全部网络推理 |
| **教学** | 一门课 = 一条枝；一章 = 一片叶；一病证 = 一叶 | 图谱节点无法直接映射「学科 / 章节 / 学分 / 前置」 | 枝 = 学科（120），叶 = 章节 + 病证单元，**直接对接 120 门教材与考核** |
| **编码** | 教材四级编码（篇·章·节·目） | 无 | 五级点分编码 **须.根.干.枝.叶**，横向读即完整编码 |

一句话：**知识图谱回答「谁和谁有关系」，知识树回答「谁从哪里来、该先学谁、在哪门课里」——两者合起来才是中医药知识的完整结构。**
中医知识树 = **知识图谱（图）× 教材目录（树）× 学科体系（干枝）= 树图一体**。

---

## 二、模型：须—根—干—枝—叶 × 跨枝经脉

```
                       叶冠  (L4 · 2592)   章节知识点 2489 ｜ 病证单元 103
                        │
             ┌──────────┼──────────┐
   枝(L3·120) D01 中医学院 … D07 中医智能学院 … D08 中医管理学院    ← 120 门学科
             │           │
   干(L2·8)   干1 中医  干2 中药  … 干7 智能  干8 管理                ← 8 院系域（= tcmP 八域）
             │
   根(L1·4)   整体观念 · 辨证论治 · 恒动平衡 · 治未病                 ← 核心公理
             │
   须(L0·6)   象数阴阳 五行生克 精气神形 天人相应 藏象经络 恒动整体      ← 哲学根基（吸养层）

   ── 跨枝经脉（图边，非层级）────────────────────────────────
   五行生克 · 十二经脉流注/表里 · 六经传变 · 学科前置 · 技能挂点 ·
   病证桥接 · ICD-11 映射  （共 635 条跨枝图边）
```

### 2.1 五级骨架（树）

| 级 | 键 | 名称 | 语义 | 规模 | tcmP 对应 |
| :-: | --- | --- | --- | :-: | --- |
| L0 | `hair` | 须 | 哲学根基（根须吸养） | 6 | 中基「哲学基础」章节 |
| L1 | `root` | 根 | 核心公理 | 4 | 中基三大特点 + 治未病 |
| L2 | `trunk` | 干 | 院系域主干 | 8 | D01–D08 八域 |
| L3 | `branch` | 枝 | 学科分枝 | 120 | 120 门学科（CM/MM/AT/TU/OR/ENT/AI/MG） |
| L4 | `leaf` | 叶 | 终末知识点 / 病证单元 | 2592 | 课题章节 2489 + DSU 103 |
| — | `concept` | 概念丛 | 五行/经脉/六经/证候/西医病/ICD-11/技能（挂点，非树内层级） | 333 | 图谱节点 |

### 2.2 跨枝经脉（图）

| 边型 | 方向 | 语义 | 条数 | 数据来源 |
| --- | --- | --- | :-: | --- |
| `hierarchy` | 父→子 | 树骨架从属 | 2735 | 构建器生成 |
| `prerequisite` | 前置→后置 | 学科先修依赖 | 152 | domain-specs「前置」 |
| `manifests_as` | DSU→证候 | 病证单元体现为某证 | 103 | kg/samples 证侧 |
| `disease_is` | DSU→西医病 | 病证单元锚定西医病 | 103 | kg/samples 病侧 |
| `bridge` | DSU→六经 | 病证桥接（证侧→六经） | 81 | kg/samples 六经定位 |
| `icd11_map` | DSU→ICD-11 | 标准编码映射 | 74 | kg/samples ICD-11 标注 |
| `skill_bind` | 技能→学科 | 教育技能挂点 | 47 | agent-tcmedu-skills |
| `spine` | 公理→域 | 公理支撑各域 | 32 | 语义认定 |
| `meridian_liuzhu` | 经脉→经脉 | 十二经脉流注 | 12 | 内嵌（藏象经络根基） |
| `nourish` | 须→根 | 根须滋养公理 | 10 | 语义认定 |
| `meridian_biaoli` | 经脉↔经脉 | 表里相合 | 6 | 内嵌 |
| `wuxing_sheng` | 五行→五行 | 相生 | 5 | 内嵌 |
| `wuxing_ke` | 五行→五行 | 相克 | 5 | 内嵌 |
| `six_chuanbian` | 六经→六经 | 传变 | 5 | 内嵌 |

> **树 × 图如何「一体」**：树的**叶**就是图的**节点**；树的**枝干路径**就是图的**分层聚类**；图边只在「同一层级内的叶之间」或「叶与概念丛之间」建立——于是「层级」与「关系」互不干扰、又互相索引。

### 2.3 五级点分编码

```
须 . 根 . 干 . 枝 . 叶
 1    0    0    0    0          →  X1 象数阴阳
 0    1    0    0    0          →  G1 整体观念
 0    0    7    0    0          →  D07 中医智能学院
 0    0    7   04    0          →  D07-S04 中医知识图谱（教材 AI-04）
 0    0    7   04   03          →  《中医知识图谱》第 3 章
 0    0    1   13   D00001      →  DSU-00001（挂在 D01-S13 中医内科学（上）枝上）
```

---

## 三、构建管线（单一事实源 → 生成物 → 校验）

```
scripts/build_knowledge_tree.py                     ★ 单一构建点
   ├── data/tcmP-subjects.json          8 域 / 120 学科（tcmP 主仓 domain-specs 同步抽取）
   ├── domain-specs/DOMAIN_SPEC_D0*.md  章节目录（叶）+ 前置依赖（图边）  ← 容错解析 4 种异构排版
   ├── kg/samples/dsu-samples-*.json    103 病证单元 / 病证桥接 / ICD-11
   ├── agent-tcmedu-skills/catalog.json 84 教育技能（挂点边）
   └── 内嵌中医哲学根基                  须 6 / 根 4 / 五行 / 十二经脉 / 六经
                 │
                 ▼  python scripts/build_knowledge_tree.py
   kg/tree/tcm-knowledge-tree.json   （1.1 MB：meta + stats + nodes + edges）
   kg/tree/schema.json               （结构定义，draft-07）
                 │
                 ▼  python scripts/verify_knowledge_tree.py
   24 项端到端自检（结构完整性 / 树导航 / 图邻接 / 检索 / API 路由）
```

**构建幂等**：任意源更新后重跑一次即可，`verify` 全绿即代表「无重复 id / 无孤儿 / 无悬空边 / 章节覆盖 = 120/120」。

### 3.1 教材素材：GitBook → Excel（技能 `gitbook-to-excel`）

本知识树驱动的教材《中医知识树》以 **GitBook 书稿**为单一事实源，经转换器落为 Excel 工作簿：

```
kg/tree/book/                     ← GitBook 书稿（4 篇 · 10 章 · 49 节）
  SUMMARY.md  README.md  ch01..ch10.md
        │  python scripts/gitbook_to_excel.py --book kg/tree/book --out book.xlsx
        ▼
scripts/gen_knowledge_tree_xlsx.py   ← 书稿页 + 平台数据页 + embedding-code
        ▼
<桌面>/中医知识树.xlsx                 ← 18 sheet 交付物（替代 AI-04《中医知识图谱》）
```

| sheet | 内容 |
| --- | --- |
| `0封面` `0目录` | 教材元数据卡 / 替代说明 / 篇·章目录结构 |
| `0正文总表` | 章 ｜ 节 ｜ 类型（标题/正文/代码/表格）｜ 内容（**原子行**，供管线/评阅/LLM） |
| `第一章` … `第十章` | 各章正文（节标题 / 正文 / 代码 / 表格） |
| `D07-S04 中医知识树` | 四级目录（篇·章·节·目）5 列范式，可直接替换原表 |
| `知识树总览` `图谱接口` | 五级骨架与边型统计、DSU 样例（取自真实构建产物） |
| `embedding-code` | ICD-11 / TF-IDF / FTS5 / RRF / 上下文工程 真实代码 + 线上实测 |
| `构建与部署` | 构建·校验·部署·应用的可复现命令 |

> 转换器已固化为技能 **`gitbook-to-excel`**（含陷阱：openpyxl 超长多行单元格截断 → 逐行原子化）。

---

## 四、运行时与应用（把知识树用起来）

### 4.1 查询引擎 `kg/tree/tcm_tree.py`（零依赖）

```bash
python kg/tree/tcm_tree.py stats                  # 结构统计
python kg/tree/tcm_tree.py node D07-S04           # 节点详情（含五级编码）
python kg/tree/tcm_tree.py path DSU-00001         # 根→域→学科→单元 祖先链
python kg/tree/tcm_tree.py neighbors DSU-00001    # 图邻接（bridge/icd11_map/…）
python kg/tree/tcm_tree.py search 桂枝汤           # 叶级检索
python kg/tree/tcm_tree.py subtree D07            # 子树
```

### 4.2 平台 API `api/tree_router.py`（挂载于 sage-api）

| 端点 | 作用 |
| --- | --- |
| `GET /tree/stats` `/tree/meta` `/tree/levels` | 结构统计 / 元信息 / 层级刻度 |
| `GET /tree/node/{id}` | 节点详情（含 `code5` 编码与属性） |
| `GET /tree/children/{id}` | 子节点（展开某枝/某域） |
| `GET /tree/path/{id}` | 根→节点 祖先链（**定位任一知识点的来源学科与章节**） |
| `GET /tree/neighbors/{id}?rel=` | 图邻接（按边型过滤：`bridge` / `icd11_map` / `wuxing_sheng` …） |
| `GET /tree/search?q=&level=&kind=` | 全文检索（可按层级/类型过滤） |

线上路径：`https://www.zyyywaccn.com.cn/api/sages/tree/*`（Nginx `location /api/sages/` → sage-api:8300）。

### 4.3 五类应用场景

| 场景 | 用法 | 动作 |
| --- | --- | --- |
| **教材编排** | `path(叶)` 反查学科/章节 | 教材目录自动对齐 120 学科骨架，缺章即报警 |
| **技能路由** | `neighbors(学科, skill_bind)` | 任一学科挂到哪些教育技能，反向补齐未覆盖学科 |
| **病证检索** | `neighbors(DSU, bridge/icd11_map)` | 以病索证 / 以证溯病 / 一键取 ICD-11 编码 |
| **六者 Agent** | `path(DSU)` | 医者/患者/药者按「域→学科→病证」加载知识边界 |
| **医圣成长** | `subtree(域)` 计数 | 病证数门槛 ⇄ 职称映射，成长路径可量化 |

---

## 五、与既有平台资产的关系

| 平台资产 | 中医知识树的定位 | 互操作 |
| --- | --- | --- |
| **病证知识图谱**（DSU · 103→60,000） | 是知识树的**叶丛**之一（`kind=dsu`） | `manifests_as`/`disease_is`/`bridge`/`icd11_map` 四边接入 |
| **ICD-11 编码桥**（内网镜像 + `icd11_mms.db`） | 是知识树的**编码叶**（`kind=icd11`） | `icd11_map` 边；与 `/icd/*` 端点同源 |
| **教材 120 门 / 8 域** | 是知识树的**干枝与章节叶** | 由 `data/tcmP-subjects.json` + domain-specs 直出 |
| **agent-tcmedu-skills**（84 技能） | 是知识树的**技能挂点**（`kind=skill`） | `skill_bind` 边；技能声明 `textbookCodes` 即可挂树 |
| **sage-api**（六者 / 医圣 / Embedding） | 是知识树的**消费方** | `/tree/*` 端点复用既有部署与鉴权链路 |
| **Embedding 引擎**（TF-IDF+FTS5+RRF） | 与知识树**互补**：树给结构，向量给语义 | 叶节点文本（`name`+`attrs`）可直接喂入向量库 |

> **收敛原则**：知识树**不复制**任何数据，只把平台既有资源「引用 + 编址 + 加边」；源变更 → 重跑构建器 → 树自动跟上。

---

## 六、分布式编程资源（本平台）

中医知识树构建与运行所依托的 tcmP 分布式资源：

| 节点 / 资源 | 地址 | 角色 | 与知识树的关系 |
| --- | --- | --- | --- |
| 华为云（公网） | `114.115.211.254` · Nginx :80/443 | www.zyyywaccn.com.cn；sage-api `:8300`（uv py3.11）；Embedding v3.0 | **知识树线上落点**：`/var/www/tcm-dashboard/kg/tree` + `/api/sages/tree/*` |
| 内网 ICD-11 | `192.168.0.111:8080` | whoicd/icd-api 容器（MMS en+zh） | `icd11_map` 边的外网编码来源（公网降级本地 db） |
| 本地开发机 | `192.168.0.105`（Windows） | 开发 / Hermes Gateway / 构建 | **知识树构建器运行处** |
| 浪潮硬服务器 | `192.168.0.102`（Windows Server） | GPU 推理节点（教材执行 / 医圣推理） | 未来：知识树驱动的批量教材与推理任务 |
| 构建器 / 引擎 / 路由 | `scripts/build_knowledge_tree.py` · `kg/tree/tcm_tree.py` · `api/tree_router.py` | 构建 · 查询 · 服务 | 本知识树的全部代码资产 |
| 数据源 | `kg/samples/*` · `data/tcmP-subjects.json` · domain-specs · `catalog.json` | 病证 / 学科 / 章节 / 技能 | 树的**输入** |

部署（在开发机运行，需 SSH 免密到华为云）：

```powershell
cd C:\Users\DELL\tcmP
powershell -ExecutionPolicy Bypass -File scripts\deploy-knowledge-tree.ps1
# 流程：本地重建 → 上传数据/引擎/路由 → 服务器注入挂载块并重启 sage-api → HTTPS 验收
```

---

## 七、Schema 摘要

```jsonc
// 节点
{ "id": "DSU-00001", "code5": "0.0.1.13.D00001",
  "level": "leaf", "level_index": 4,
  "name": "普通感冒（上呼吸道感染） × 风寒束表证",
  "parent": "D01-S13", "kind": "dsu",
  "attrs": { "disease": "普通感冒（上呼吸道感染）", "syndrome": "风寒束表证",
             "six_channel": "太阳病", "mapping_type": "直接对应",
             "evidence": "A级-多中心RCT", "icd11": "CA00", "icd": "J06.9" } }

// 边
{ "source": "DSU-00001", "target": "ICD-CA00", "type": "icd11_map" }
```

`level ∈ {hair, root, trunk, branch, leaf, concept}`；`kind` 与边型枚举见 `kg/tree/schema.json`。

---

## 八、治理与演进

| 事项 | 约定 |
| --- | --- |
| 新增学科 | 改 domain-specs → `data/tcmP-subjects.json` 重抽 → 重跑构建器 |
| 新增病证单元 | 落 `kg/samples/*.json` → 重跑构建器（自动加叶 + 编址 + 加边） |
| 新增技能 | catalog 声明 `subjects`/`textbookCodes` → 自动生成 `skill_bind` 边 |
| 概念丛扩展 | 在构建器常量区扩 五行/经脉/六经，或引入 OWL 本体（Protégé）文件 |
| 质量门禁 | `python scripts/verify_knowledge_tree.py` 全绿方可发布 |
| **离线降级** | 平台不可达时，凡依赖 `/tree/*` 的结论一律标注「未能核实」，不得凭记忆补齐 |

---

## 九、里程碑

| 阶段 | 版本 | 目标 | 状态 |
| :-: | :-: | --- | :-: |
| K1 | v1.0.0 | 五级骨架 + 跨枝图边 + 查询引擎 + `/tree/*` 端点（3063 节点） | ✅ 本次 |
| K2 | v1.1.0 | 补全 45 门暂无技能覆盖学科的 `skill_bind`；章节叶粒度下钻到「节」 | 规划 |
| K3 | v1.2.0 | 知识树 ⇄ Embedding 引擎双向绑定（叶文本入向量库，语义检索回挂叶） | 规划 |
| K4 | v2.0.0 | 本体化（OWL/Protégé）+ 树图对齐校验 + 六者 Agent 知识边界自动生成 | 规划 |

---

<p align="center"><sub>本 README 与 <code>kg/tree/</code> 全部生成物均由 <code>scripts/build_knowledge_tree.py</code> 驱动 —— 单一事实源，可复现，可校验。</sub></p>
