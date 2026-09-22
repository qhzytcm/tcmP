# 📚 教材项目周进度报告

**报告周期：** 2026-07-11 ~ 2026-07-18  
**生成时间：** 2026-07-18  
**项目名称：** 中医药系列教材编写项目（120学科·8领域·134种教材）

---

## 一、项目全局概览

| 指标 | 数值 |
|:-----|:----:|
| 项目文件总数 | 223 |
| 活跃看板数 | 11 |
| 看板卡片总数 | 97 |
| 完成卡片数 | 23 |
| 进行/待办卡片数 | 74 |
| 本周文件变更数 | 12 |

---

## 二、各目录文件统计

| 目录 | 文件数 | 说明 |
|:-----|:-----:|:-----|
| `drafts/` | **46** | 章节草稿（含 27 篇顶层章稿 + 12 篇 D01-S01 章稿 + 5 篇 D22 内容稿 + 1 篇网络工程 + 目录） |
| `reviews/` | **0** | ⚠️ 评阅报告目录为空（L2-reviews、L3-reviews 为空目录） |
| `feedback/` | **1** | 使用反馈 1 份（chapter1-trial-feedback.md） |
| `domain-specs/` | **8** | 8 个领域规范文件（D01–D08 全部完成） |
| `assets/` | **2** | 配图素材 |
| `scripts/` | **5** | 部署/归档脚本 |
| `dashboard/` | **1** | 三方共享看板 HTML |
| `.github/workflows/` | **2** | CI/CD 工作流配置 |
| `archive/` | **0** | 归档目录（尚无归档） |
| 项目根目录 | 14 | README、PROJECT、FOUR_TIER_SYSTEM_DESIGN、课表 Excel 等 |

### 本周新增/变更文件（12 件）

| 文件 | 变更类型 |
|:-----|:--------:|
| `drafts/D01-S01/chapter-02-yinyang-v2.md` | 修订（阴阳学说 v2） |
| `drafts/D01-S01/chapter-changelog-02-v2.md` | 新增（修改日志） |
| `drafts/D01-S01/chapter-exercises-02-v2.md` | 修订（习题 v2） |
| `drafts/D01-S01/chapter-figures-02-v2.md` | 修订（配图说明 v2） |
| `drafts/D01-S01/chapter-selfcheck-02-v2.md` | 修订（自检清单 v2） |
| `.github/workflows/tcm-ci-cd.yml` | 新增（CI/CD 流水线） |
| `.github/workflows/tcm-human-review.yml` | 新增（人机评审工作流） |
| `ontology-agent-soul-architecture.md` | 新增（本体论灵魂架构） |
| `TCM-AI-Engineering-from-Scratch.md` | 新增（AI 工程计划） |
| `PROJECT.md` | 更新 |
| `README.md` | 更新 |
| `docs/cloud-server-deployment-guide.md` | 新增（云服务器部署指南） |

---

## 三、Kanban 看板状态

### 3.1 `textbook` 看板（三角色协作—单本教材模式）

| 状态 | 数量 | 说明 |
|:----|:----:|:-----|
| ✅ **done** | **10** | 已完成章节（含第3章、第6章、第7章等） |
| 🚫 **blocked** | **16** | 阻塞中—需解决前置依赖或人工干预 |
| 合计 | 26 | |

🔴 **阻塞注释：** `textbook` 看板 16 张卡片处于 blocked 状态，建议优先排查 gateway dispatcher 是否正常运行。

### 3.2 `tcm-epic` 总控看板（L1 里程碑）

| 卡片标题 | 轮次 | 优先级 | 状态 |
|:---------|:----:|:------:|:----:|
| [Epic] 轮次1：核心基础与文化通识编写 | 1 | P1 | ready |
| [Epic] 轮次2：经典基础与进阶编写 | 1 | P1 | ready |
| [Epic] 轮次3：临床各科与专科编写 | 1 | P1 | ready |
| [Epic] 轮次4：临床深化与交叉学科编写 | 2 | P2 | ready |
| [Epic] 轮次5：硕士深化与交叉学科编写 | 2 | P2 | ready |
| [Epic] 轮次6：博士前沿与产业管理编写 | 3 | P3 | ready |
| [Epic] 质量体系与编写规范 | all | P1 | ready |
| [Epic] 终验发布与项目归档 | final | P2 | ready |

**状态：** 8 张 Epic 卡片全部为 ready，尚未进入编写执行阶段。

### 3.3 8 领域看板

| 看板 | 完成 | 就绪(ready) | 待办(todo) | 合计 | 核心进度 |
|:----|:---:|:-----------:|:----------:|:----:|:---------|
| **D01 中医学院** | 4 | 5 | 2 | 11 | ✅ 第1章已完成；第2-3章待编写；5张Story就绪 |
| **D02 中药学院** | 3 | 7 | 0 | 10 | ✅ 第1-2章已完成；7张Story就绪 |
| **D03 针灸学院** | 1 | 3 | 0 | 4 | 1张Story就绪 |
| **D04 推拿学院** | 0 | 4 | 0 | 4 | 全部ready |
| **D05 骨伤学院** | 0 | 6 | 0 | 6 | 全部ready |
| **D06 五官口腔** | 0 | 3 | 0 | 3 | 全部ready |
| **D07 智能学院** | 0 | 4 | 0 | 4 | 全部ready |
| **D08 管理学院** | 0 | 6 | 0 | 6 | 全部ready |
| **合计** | **8** | **38** | **2** | **48** | |

📊 **领域完成率：** 8/48 = **16.7%**（D01/D02 领先，D04–D08 尚未启动编写）

### 3.4 `network-service-engineering` 看板

| 状态 | 数量 |
|:----|:----:|
| done | 5 |
| blocked | 10 |
| 合计 | 15 |

---

## 四、领域规范文件状态

| 文件 | 状态 |
|:-----|:----:|
| `DOMAIN_SPEC_D01.md`（中医学院） | ✅ 已生成 |
| `DOMAIN_SPEC_D02.md`（中药学院） | ✅ 已生成 |
| `DOMAIN_SPEC_D03.md`（针灸学院） | ✅ 已生成 |
| `DOMAIN_SPEC_D04.md`（推拿学院） | ✅ 已生成 |
| `DOMAIN_SPEC_D05.md`（骨伤学院） | ✅ 已生成 |
| `DOMAIN_SPEC_D06.md`（五官口腔） | ✅ 已生成 |
| `DOMAIN_SPEC_D07.md`（智能学院） | ✅ 已生成 |
| `DOMAIN_SPEC_D08.md`（管理学院） | ✅ 已生成 |

**8/8 领域规范文件就绪 ✅**

---

## 五、草稿章节详情

### 5.1 D01-S01 中医基础理论（核心学科）

| 章节 | 版本 | 文件 | 状态 |
|:----|:----:|:-----|:----:|
| 第1章 导论 | — | 含在 D01-S01 目录外 | 看板标记 done |
| 第2章 阴阳学说 | v2 | chapter-02-yinyang-v2.md (32KB) | ✅ v2 修订完成 |
| 第3章 五行学说 | — | chapter-03-wuxing.md | ✅ 看板标记 done |
| 第4章 藏象（五脏） | v1 | chapter-04-zangxiang-wuzang-v1.md (32KB) | 待修订 |
| 第5章 藏象（六腑） | — | chapter-05-zangxiang-fu-organs.md | ✅ |
| 第6章 精气血津液 | — | chapter-06-精气血液.md | ✅ |
| 第7章 经络（十二经脉） | v1 | chapter-07-jingluo-twelve-meridians.md | ✅ |
| 第8章 经络（奇经八脉） | v1 | chapter-08-jingluo-2-v1.md (28KB) | 待修订 |
| 第9章 病因病机 | v1 | chapter-09-bingyin-v1.md (33KB) | 待修订 |
| 第10章 病机 | v1 | chapter-10-病机-v1.md | ✅ |
| 第11章 望诊 | — | chapter-11-wangzhen.md | ✅ |
| 第12章 闻诊与问诊 | — | chapter-12-闻诊与问诊.md | ✅ |
| 第13章 切诊 | — | chapter-13-qiezhen-maizhen.md | ✅ |
| 第15章 治则与治法 | — | chapter-15-治则与治法.md | ✅ |
| 第20章 内科常见病证治 | — | chapter-20-内科常见病证治.md | ✅ |
| 第23章 杂病 | — | chapter-23-draft.md | ✅ |

### 5.2 D02-S01 临床中药学

| 章节 | 文件 | 状态 |
|:----|:-----|:----:|
| 第1章 中药学导论 | — | 看板标记 done |
| 第2章 中药的性能 | — | 看板标记 done |
| 常用中药分类 | ch17_常用中药_按功效分类_初稿.md | 初稿 |

### 5.3 网络服务工程（跨领域平台）

| 章节 | 文件 | 状态 |
|:-----|:-----|:----:|
| 第1章 概论 | chapter-01-网络软件服务概论.md | ✅ |
| 第2章 面向服务思维 | ch02-service-oriented-thinking.md | ✅ |
| 第3章 API 设计 | chapter-03-api-first-design.md | ✅ |
| 第4章 同步通信 | ch04-sync-communication-rest-grpc.md | ✅ |
| 第5章 异步通信 | ch05-async-communication.md | ✅ |
| 第6章 服务通信模式 | chapter-06-service-communication-patterns.md | ✅ |
| 第7章 容器化 | chapter-07-containerization.md | ✅ |
| 第8章 K8s | chapter-08-kubernetes-intro.md | ✅ |
| 第9章 服务网格 | chapter-09-service-mesh-gateway.md | ✅ |
| 第10章 可观测性 | chapter-10-observability.md | ✅ |
| 第13章 CI/CD | chapter-13-cicd.md | ✅ |
| 第14章 云原生 | ch14-云原生生态概览.md | ✅ |

---

## 六、本周工作亮点

1. **D01-S01 第2章阴阳学说完成 v2 修订**（含习题、配图、自检清单全套）
2. **CI/CD 流水线配置完成**（`tcm-ci-cd.yml` + `tcm-human-review.yml`）
3. **本体论四层灵魂架构文档发布**（`ontology-agent-soul-architecture.md`）
4. **8 领域规范文件全部生成**，覆盖 8 院系 × 15学科 = 120 学科蓝图
5. **云服务器部署指南完成**（`docs/cloud-server-deployment-guide.md` + `scripts/deploy-centos7.sh`）
6. **Epic 卡片全部创建**（6 编写轮次 + 质量体系 + 终验归档）

---

## 七、需关注的问题

| # | 问题 | 影响范围 | 建议措施 |
|:--|:-----|:---------|:---------|
| 1 | 🔴 `textbook` 看板 16 张卡片处于 **blocked** | 三角色协作流 | 检查 gateway dispatcher 状态；确认 textbook-writer/reviewer/user profile 存在 |
| 2 | 🔴 **评阅目录为空** (`reviews/`) | 质量门禁 | 无任何章节通过评阅环节。建议创建 textbook-reviewer 的评阅卡片 |
| 3 | 🟡 **D04–D08 领域尚未产出一章草稿** | 38 张 Story 卡片 ready 未动 | 建议启动 gateway dispatcher 自动调度，或人工触发首批编写任务 |
| 4 | 🟡 **archive/ 目录仍为空** | 版本管理 | 已完成章节应归档至 archive/ |
| 5 | 🟢 **D01-S01 第4/8/9章有 v1 草稿但无 v2** | 持续修订 | 可安排下一轮修订迭代 |

---

## 八、下周建议

1. **恢复 triangle 看板工作流**：解除 `textbook` 看板 16 张 blocked 卡片
2. **启动 D01/D02 领域 gateway 调度**：让 D01-S01～D01-S04、D02-S01～D02-S04 的 Story 卡片进入 running 状态
3. **创建首批评阅任务**：对已完成章节（第3章五行、第6章精气血津液等）启动 L3 初审
4. **配置 Cron 定时任务**：按 skills 模板设置每周反馈聚合和待评阅提醒
5. **部署 Dashboard**：配置 API Server，使三方共享看板可公网访问

---

*本报告由 Hermes Agent 自动生成 | 项目：中医药系列教材（120学科·8领域·134种教材）*
