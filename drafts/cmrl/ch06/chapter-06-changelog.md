# 第6章 修改说明书（chapter-06-changelog.md）

- 教材：《中医场景强化学习》第6章「信仰的检验：时序差分与在线学习」
- 修订轮次：L3 三审 P0 修订（v1 → v2）
- 修订工程师：章节作者　日期：2026-08-15
- 状态：修订完成，复验通过，待 L3 复审

## 一、修订依据

L3 三审 P0 意见共 2 项：
1. 例6.1 第三回合 v(s3)=0.0261→0.0252（TD 更新式应为 v←v+α×(目标−旧值)，正文 0.0261 系漏减旧值）。
2. 三种最适度英文跨章不一致：ch06 用 personal positioning 等，统一为 ch01 基准 individual positioning / scenario survival optimality / environment co-prosperity optimality。

## 二、逐条回应

### R1 例6.1 第三回合 v(s3) 数值笔误

| 项 | 内容 |
|---|---|
| 意见 | 正文 6.2.2"第三回合后估计为 (0, 0.00081, 0.0261, 0.271)"中 v(s3) 应为 0.0252 |
| 验算 | 第三回合访问 s3：TD目标 = 0 + 0.9×v2(s4) = 0.9×0.19 = 0.171；误差 = 0.009 − 0.171 = −0.162；更新 v(s3) = 0.009 + 0.1×0.162 = **0.0252**。原 0.0261 = 0.009 + 0.1×0.171，系更新式漏减旧值 0.009（误写为 v + α×目标） |
| 改动 | 正文 02-1.2.md 6.2.2 节："第三回合后估计为(0, 0.00081, 0.0261, 0.271)" → "(0, 0.00081, 0.0252, 0.271)"。正文第三回合无逐步演算（仅结果句），无需同步演算；习题集、配图说明、复验脚本、自检清单联动更新（见下） |
| 联动 | 习题集使用说明、配图说明 6-4（两处）、selfcheck 结论概览/B2 验算表/C4 判定/D 部分/附录、check_ch06.py 注释与信息行 |

### R2 三种最适度英文统一

| 位置（修订前 → 修订后） |
|---|
| 正文 07-1.7.md 6.7.1：个人定位（personal positioning）→ 个人定位（individual positioning） |
| 正文 07-1.7.md 6.7.1：场景生存最适度（scenario-optimal fitness）→ 场景生存最适度（scenario survival optimality） |
| 正文 07-1.7.md 6.7.1：环境共荣最适度（mutual flourishing optimum）→ 环境共荣最适度（environment co-prosperity optimality） |
| 配图说明 6-10 内容说明：三处同上 |
| selfcheck B1 英文对照抽查清单、B3 中医映射表（scenario-optimal fitness 行）、B4 三概念：三处同上 |
| 习题集无英文括注，无须改动 |

基准来源：第 1 章 1.7（ch01/07-1.7.md）与第 1 章自检清单 B4，即 individual positioning / scenario survival optimality / environment co-prosperity optimality。

## 三、验证结果

- `python check_ch06.py`：退出码 0；A 结构 8×3×2 全部 PASS；B 字数总字符口径 48/48；C 公式全部 PASS（例6.1 第三回合 s3 输出 0.0252，与修订后正文一致）；D 引用正常。
- 残留检查：ch06 范围内正文无 0.0261、无旧英文（仅 selfcheck 修订记录 R1/R2 中刻意保留对照痕迹）。

## 四、遗留提示（超出本次范围，供 L3 决策）

- 第 4 章 4.7 仍用旧英文（personal positioning / scenario-optimal fitness / mutual flourishing optimum），其 chapter-04-selfcheck.md D2 已标记同型问题，建议按第 1 章基准在后续轮次统一。
- 归档目录 archive_v2/ch03 亦有异形（scenario-specific optimality / environmental co-prosperity optimality），属历史版本，不影响当前草稿。

## 五、G4 排版批修订（v2 → v3，2026-09-03）

修订项：
1. 【图号回写】核查正文图 6-1～图 6-4 引导语均已存在（01-1.1.md"修正链条如图 6-1 所示"、02-1.2.md"图 6-2 把前三回合的手算结果与 60 回合的模拟曲线画在一起"、05-1.5.md"更新路径见图 6-3"、07-1.7.md"自适应闭环如图 6-4 所示"），本轮无新增插入；规划图 6-2/6-3/6-5/6-6/6-8/6-9/6-11（未绘制）无回写对象。
2. 【教学示例标注】02-1.2.md 6.2.2 例6.1（四状态链 TD(0) 手算演示数值）首现处加"（教学示例数据）"括注；概念公式未加。
3. 未动项：ch06 无术语统一任务；例6.1 数值口径沿用 P0 修订值 0.0252，未再改动。
