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

api(后端) · agents(六者SOUL) · sages(医圣) · kg(图谱 & **知识树** & **信息学** & **语义张量** & **器械**) · mobile-app(PWA) · docs(架构) · .github(CI/CD)

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

## 语义张量 · 三维极坐标（v1.0）

> 标准本体：`tcmP-三维极坐标语义张量-可视化标准 v1.0`；代码单一来源：`kg/semtensor/axioms.py`、`kg/semtensor/encoder.py`。

**方向承载语义，r 承载尺度，颜色是坐标的函数**（读色即读义）：

```
X = r·cosθ·cosφ ; Y = r·cosθ·sinφ ; Z = r·sinθ
x = 0.60·阴阳 + 0.40·寒热 ；y = 0.70·表里 + 0.30·虚实 ；z = (神分−精分)/(精分+气分+神分+1)
r = clip(0.35·证据 + 0.35·症状密度 + 0.30·桥接完备, 0.20, 1.00)
```

| 轴 | I(−1) | O(0) | T(+1) |
| --- | --- | --- | --- |
| X 阴阳 | 橙 `#FF8C00` | 绿 `#00B050` | 紫 `#8A2BE2` |
| Y 表里 | 蓝 `#1F61D9` | 绿 `#00B050` | 红 `#DB1C1C` |
| Z 精气神 | 黄 `#F2C200` | 绿 `#00B050` | 青 `#00C7C7` |

- 覆盖：**DSU 103 · 学科 120（8 域）· 域 8**；`kg/semtensor/semtensor.json`
- 契约（冻结）：`GET /api/sages/semtensor/spec`（机器可读标准镜像）· `/semtensor/health`（口径与公理指纹）
- 校验：`python kg/semtensor/verify_semtensor.py`（22 项，含三球镜像不变色、球面往返 <1e-12）
- 论文/教材：《中医信息学》v2.0 以「公理层 → 语义张量层 → 学科映射层」重构（10 篇 34 章）

## 中医智能仪器与可穿戴设备 · D07-S11（v1.0.0）

> 平台的「器械与感知」层：让中医四诊可被**仪器采集**、被**算法分析**、被**网络流通**。
> 单一来源：`kg/device/holter.py`（算法）· `kg/device/build_device.py`（构建）· `kg/device/tcm-device.json`（产物）。

**六类器械 × 六种可穿戴形态 × 六条信号通道 × 数据标准 × 六 AI 算子 × 中医药关联**

| 重点能力 | 实测（`python kg/device/build_device.py`） |
| --- | --- |
| Holter 心律检测 | 六场景：正常/心动过速(107bpm)/过缓(50bpm)/**停搏(danger)**/早搏/**房颤提示** |
| 时域 HRV | HR · SDNN · RMSSD · pNN50 · CV |
| 中医药关联 | 房颤提示→心悸怔忡（脉结代/促/涩）；SDNN<30→心气虚/心脉瘀阻（**仅提示，不构成诊断**） |

- 接口：`GET /api/sages/device/{schema,classes,forms,signals,operators,stats}` · `POST /api/sages/device/holter/analyze`
- 平台既有 **械者 6 端点**：`/devices/{maintenance,imaging,procurement,qc,trace,emergency}`
- 自检：`python kg/device/verify_device.py`（19 项，含输入鲁棒性与确定性）
- 教材素材：桌面 `中医智能仪器与可穿戴设备.xlsx`（21 sheet · D07-S11）

> ⚠️ 边界声明：算法输出仅供教学/研究参考，**不构成医学诊断**；验证序列为**标注的仿真数据**（非临床）。

### 扩展层（v1.1）：可感测捕获 · 六快 · 健康自动评价 · 光遗传学

| 模块 | 内容 |
| --- | --- |
| **可感测四元** | 光子(P) · 电子/电压(E) · 质量(M) · 运动(K) —— 一切可穿戴传感的物理归并 |
| **中医药通用六快** | 吃 / 喝 / 拉 / 撒 / 睡 / 警觉安全（不预设病种的问诊骨架，天然适合连续监测） |
| **健康自动评价** | `kg/device/sensing.py`：多源记录 → 六快分维评分 → 总分分级（确定性；缺数据不猜，报 coverage） |
| **光遗传学** | 2026 诺贝尔生理学或医学奖（Deisseroth·Hegemann·Nagel，光门控离子通道与光遗传学）· **含边界声明** |
| **参考实现** | `pkpio/fitbit-googlefit`（518★）：Fitbit API → convertors 换算 → Google Fit（纳秒/meters/kg） |

接口新增：`/device/{sensing,six-quick,optogenetics}` · `POST /device/health-score`
自检：`python kg/device/verify_device.py` **32 项** 全绿；教材：桌面 `中医智能仪器与可穿戴设备.xlsx`（**31 sheet**，5 篇 15 章）