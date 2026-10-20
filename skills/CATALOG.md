# 学科配套技能目录（Subject Skill Catalog）

> 用途：登记"学科 → 配套技能"映射，是 `docs/06-学科覆盖矩阵.md` 中 `covered` 状态的第二判据（第一判据是学科大纲签发）。
> 维护：各领域主编（L2）签发大纲时同步登记。
> 最近更新：2026-10-20（D01 / CM-05）

## 一、技能来源（双份存放约定）

| 位置 | 角色 | 说明 |
|---|---|---|
| `skills/<skill-name>/SKILL.md` | **仓库权威副本** | 随项目 git 版本管理，任何 agent 可直接读取；技能变更须改此处并发 PR |
| `~/AppData/.../profiles/<profile>/skills/textbook/<skill-name>/SKILL.md` | **运行时副本** | 技能被 Hermes 加载处；须与仓库副本 MD5 一致 |

部署状态说明：

- `repo-only` = 仅仓库副本存在，运行该学科的 profile 尚未装载（需 L1 授权跨 profile 部署）
- `deployed:<profile>` = 已装载到该 profile
- 校验命令：`md5sum skills/<name>/SKILL.md <profile>/skills/textbook/<name>/SKILL.md`

---

## 二、已登记技能

| 学科 | 教材 | 技能名 | 版本 | 仓库副本 | 部署状态 | 签发日 |
|:-:|:-:|---|:-:|:-:|---|:-:|
| D01-S05 | CM-05 | `tcm-thinking-methodology` | 1.0.0 | `skills/tcm-thinking-methodology/SKILL.md` | `deployed:tcm-domain-d01`；`repo-only` for tcm-author（待 L1 授权部署） | 2026-10-20 |

### `tcm-thinking-methodology` 技能摘要

- **作用**：CM-05《中医思维方法论》编写/复审的执行规范
- **含**：12 章知识点基线（学时/字数/核心命题）、36 条强制术语表、古籍溯源三要素、四件套交付规范、五条编写红线、G1/G2 评分表、6 条跨域接口、交付前自检命令
- **触发**：看板 `tcm-domain-D01` 中 `subject: S05` 的任何编写/复审卡
- **权威来源**：`subject-outlines/D01/CM-05_中医思维方法论_教材大纲-v1.0.md`（冲突以大纲为准）

---

## 三、规划中技能（占位，未创建）

> 命名遵循 `tcm-<学科拼音/英文>` 约定。占位不代表已开发，仅为避免命名冲突。

| 学科 | 规划技能名 | 优先级 |
|:-:|---|:-:|
| D01-S01 | `tcm-basic-theory` | P1 |
| D01-S02 | `tcm-diagnostics` | P0 |
| D01-S06 | `tcm-bibliography` | P1 |
| D01-S09 | `neijing-readings` | P0 |
| D02-* | `tcm-materia-medica` 等 | 待 D02 主编登记 |

---

## 四、新增技能登记流程（L2 操作）

1. 学科大纲签发（`subject-outlines/<D>/<CM-xx>_..._教材大纲-vX.md`）
2. `skill_manage(action='create', category='textbook', name='<skill-name>')` 生成本 profile 运行时副本
3. `cp` 至仓库 `skills/<skill-name>/SKILL.md`（权威副本）
4. `md5sum` 校验两份一致
5. 更新本表 §二
6. 更新 `docs/06-学科覆盖矩阵.md` 对应行状态为 `covered`
7. 跨 profile 部署需 L1 明确授权（cross_profile 写保护）
