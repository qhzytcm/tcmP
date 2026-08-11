# -*- coding: utf-8 -*-
"""
gen_rl_notes_xlsx.py — 《强化学习的数学基础》读书笔记生成器
==========================================================
参考: 赵世钰(Shiyu Zhao) Mathematical Foundation of Reinforcement Learning
      (Springer, https://github.com/MathFoundationRL/Book-Mathematical-Foundation-of-Reinforcement-Learning)
输出: 桌面《强化学习的数学原理-赵世钰.xlsx》，10 个 sheet（RL01-RL10），每章含:
  Part1 原书读书笔记（核心概念/关键公式/算法/书特色）
  Part2 tcmP 平台适应性改写（hermes-generating-content：平台映射/配置接口/安装依赖/实践）

用法: python scripts/gen_rl_notes_xlsx.py
"""
from __future__ import annotations
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

OUT = Path(r"C:\Users\DELL\Desktop\强化学习的数学原理-赵世钰.xlsx")

# ───────────────── 十章读书笔记数据 ─────────────────
# 每章: {sheet, title, rows: [(模块, 内容), ...]}
# Part1 模块前缀: [原书] ; Part2 模块前缀: [平台改写·hermes-generating-content]
CHAPTERS = [
{
 "sheet": "RL01 基本概念",
 "title": "Chapter 1 Basic Concepts 基本概念",
 "rows": [
  ("[原书] 章节定位", "全书起点：以贯穿全书的『网格世界(grid world)』示例引入强化学习基本概念。网格世界=机器人(agent)在9宫格中移动到达目标格，避开禁忌格。后续所有算法都在这张图上验证。"),
  ("[原书] 核心概念1：状态与动作", "状态 s：智能体相对环境的状态（网格世界=所在格子，s1~s9）。状态空间 S={s1,...,s9}。动作 a：每个状态可选动作（上/右/下/左/静止，a1~a5）。动作空间 A(s)。状态转移：s --a--> s'（撞边界弹回、进禁忌格可进入但受罚）。"),
  ("[原书] 核心概念2：策略与奖励", "策略 π(a|s)：条件概率分布（表格表示，确定性/随机）。奖励 r(s,a)：环境反馈（出界-1、进禁忌-1、到达目标+1、其他0）。奖励是人机接口——用奖励引导智能体行为，但最大即时奖励的动作不一定最优（要看长期回报）。"),
  ("[原书] 核心概念3：轨迹/回报/折扣", "轨迹：状态-动作-奖励链 s1-a2->s2-r0->...->s9-r1。回报(return)=轨迹奖励之和（可评价策略好坏）。无限长轨迹回报发散→引入折扣回报 Σγ^k r_{t+k+1}，γ∈(0,1) 折扣率：γ→0 短视，γ→1 远视。episode(回合)/continuing(持续)任务；吸收态统一两者。"),
  ("[原书] 关键公式", "折扣回报: G_t = R_{t+1} + γR_{t+2} + γ²R_{t+3} + ... ；网格世界例: 最优路径 return = γ³/(1-γ) vs 走禁忌 return = -1+γ/(1-γ)。"),
  ("[原书] MDP 与马尔可夫性质", "强化学习形式化为马尔可夫决策过程(MDP)：S(状态) + A(动作) + P(状态转移概率) + R(奖励) + γ(折扣)。马尔可夫性质：下一状态只依赖当前状态与动作（记忆无关）。"),
  ("[原书] 书特色", "① 网格世界一图贯穿全书（直观可算）；② 每个概念先给动机示例再形式化；③ 强调『模型已知 vs 模型未知』的两阶段路线图（Ch1-4 有模型，Ch5 起无模型）。"),
  ("[平台改写] tcmP 映射", "网格世界 ↔ 医圣成长路径：状态=医师当前水平（住院医-1→学科带头人，掌握病证数 500→60000）；动作=学习/诊疗决策（进修课程、辨证选择、方剂推荐）；奖励=临床反馈（辨证正确+1、误诊-1、考核通过+1）。目标=找到最优成长策略。"),
  ("[平台改写] 平台配置接口", "① 依赖安装：pip install numpy pandas matplotlib（基础）；pip install gymnasium（标准 RL 环境，可选）。② DeepSeek API 配置：设置环境变量 DEEPSEEK_API_KEY（平台 LLM 激活用）。③ 平台数据接口：病证单元库 tcmP/kg/samples/dsu-samples-*.json（可作 MDP 状态/奖励设计的真实数据源）。"),
  ("[平台改写] 实践建议", "把『辨证 → 方剂』建模为网格世界：状态=症状组合（来自真实 DSU 的 key_symptoms），动作=方剂选择（formula 字段），奖励=病证匹配度（检索证据分）。用平台 /semantic-search 的 rrf 分数作奖励信号。"),
 ],
},
{
 "sheet": "RL02 状态价值与贝尔曼方程",
 "title": "Chapter 2 State Values and Bellman Equation 状态价值与贝尔曼方程",
 "rows": [
  ("[原书] 章节定位", "核心概念=状态价值(state value)，重要工具=贝尔曼方程(Bellman equation)。状态价值衡量策略好坏；贝尔曼方程描述所有状态价值之间的关系，解方程=策略评估(policy evaluation)。"),
  ("[原书] 动机示例", "为什么回报重要：同一状态 s1 三种策略，直观好坏 vs 数学（折扣回报比较，return1=γ/(1-γ) > return3=0.5(-1+γ/(1-γ)) > return2=-1+γ/(1-γ)）。怎么算回报：矩阵形式 v = r + γPv，解 v = (I-γP)⁻¹r。"),
  ("[原书] 状态价值定义", "vπ(s) = E[G_t | S_t = s]（从状态 s 出发按策略 π 的折扣回报期望）。性质：依赖 s（条件期望）；依赖 π（轨迹由策略生成）；不依赖 t。确定性系统：return=value；随机系统：value=returns 的均值。"),
  ("[原书] 贝尔曼方程推导", "G_t = R_{t+1} + γG_{t+1}（自举 bootstrap！）→ vπ(s) = E[R_{t+1}|S_t=s] + γE[G_{t+1}|S_t=s] = Σ_a π(a|s)Σ_r p(r|s,a)r + γΣ_a π(a|s)Σ_s' p(s'|s,a)vπ(s')。矩阵形式 v = rπ + γPπv。"),
  ("[原书] 核心定理", "贝尔曼方程三个基本性质（定理2.1-2.3）：① 存在性：v = (I-γPπ)⁻¹rπ 必有解（I-γPπ 可逆，谱半径<1）；② 唯一性：解唯一；③ 迭代收敛：任意初值 v0，vk+1 = rπ + γPπvk 收敛到 vπ。性质③是价值迭代的雏形。"),
  ("[原书] 动作价值", "qπ(s,a)：状态 s 下先采取动作 a、之后遵循 π 的期望回报。与状态价值关系：vπ(s) = Σ_a π(a|s) qπ(s,a)；qπ(s,a) = Σ_r p(r|s,a)r + γΣ_s' p(s'|s,a)vπ(s')。动作价值是策略改进的关键（Ch3 用）。"),
  ("[原书] 书特色", "贝尔曼方程以 4 状态小例子给出完整矩阵形式（v=r+γPv），让『线性方程组』的直觉落地；强调自举思想是后续 TD 的种子。"),
  ("[平台改写] tcmP 映射", "状态价值 ↔ 病证单元的『临床价值』：vπ(症状组合) = 按诊疗路径 π 的期望疗效回报。病证检索引擎(tcm_embed)的 Document 构建=状态的数字化表示。贝尔曼方程的自举 ↔ 辨证的递归结构：当前症状的转归由『当下处理 + 后续状态价值』共同决定。"),
  ("[平台改写] 平台配置接口", "① 数据准备：python 读取 tcmP/kg/samples/dsu-samples-001.json（103+ 真实病证单元，含症状/证候/方剂/证据等级）。② 检索依赖：运行 tcmP/scripts/tcm_embed.py 需 hermes venv python（SQLite FTS5 支持，系统 Anaconda python 会段错误）。③ API 验证：curl https://www.zyyywaccn.com.cn/api/sages/semantic-search?q=失眠&top_k=1。"),
  ("[平台改写] 实践建议", "用真实 DSU 数据构造小规模 MDP：状态=10 个高频症状组合，动作=5 个推荐方剂，转移概率从病证-方剂共现统计估计（P(s'|s,a)），奖励=证据等级映射（A级=1.0，B级=0.7...）。求解 v=(I-γP)⁻¹r 并与检索分数对比。"),
 ],
},
{
 "sheet": "RL03 最优状态价值与贝尔曼最优方程",
 "title": "Chapter 3 Optimal State Values and Bellman Optimality Equation 最优状态价值与贝尔曼最优方程",
 "rows": [
  ("[原书] 章节定位", "终极目标=最优策略。核心概念=最优状态价值 v*(s)；重要工具=贝尔曼最优方程(BOE)。数学密度较高但值得：回答『最优策略存在吗？长什么样？怎么求？』。"),
  ("[原书] 动机示例", "策略改进：s1 处动作 a2(右)不好，直觉应改 a3(下)。数学：先求 vπ（vπ(s1)=8, 其余=10, γ=0.9），再算动作价值 qπ(s1,a3)=9 最大 → 更新策略选 a3。『选最大动作价值的动作』= 许多 RL 算法的基本思想。"),
  ("[原书] 核心定义", "最优状态价值：v*(s) = maxπ vπ(s)，∀s∈S。最优策略 π*：使所有状态价值达到最大的策略（vπ*(s) = v*(s)）。"),
  ("[原书] 贝尔曼最优方程", "v*(s) = max_a Σ_r p(r|s,a)r + γΣ_s' p(s'|s,a)v*(s') = max_a q*(s,a)。即：最优策略的状态价值=每个状态选最优动作的『即时奖励+γ×后继最优价值』。"),
  ("[原书] 核心定理", "定理3.1（贪婪策略最优）：若 v 是给定策略的 Bellman 方程解，且策略 π 在每个状态选最大 qπ(s,a)（贪婪策略），则 v=vπ*=v*，π 是最优策略。定理3.2（BOE 存在性）：最优状态价值存在且唯一。定理3.3（收缩映射）：BOE 解可通过迭代 vk+1 = maxπ(rπ+γPπvk) 逼近——价值迭代的理论基础。"),
  ("[原书] 书特色", "『贪婪即最优』的严格证明（用动作价值比较+逐状态论证）；收缩映射定理把『解方程』转成『迭代逼近』，为 Ch4 算法铺路；例 3.4 演示 v* 与 γ 的关系（γ 小→短视策略）。"),
  ("[平台改写] tcmP 映射", "最优策略 ↔ 最优诊疗方案：v*(症状) = 该症状下选最优辨证-方剂组合的期望疗效。BOE 的 max 结构 ↔ 医圣辨证的『择优』决策（选最优候选，非平均）。与平台 /diag、/bianzheng 的 Top-K 排序对应：检索给候选集，BOE 给『选哪个』的数学依据。"),
  ("[平台改写] 平台配置接口", "① 辨证引擎：curl https://www.zyyywaccn.com.cn/api/sages/bianzheng -X POST -d '{\"symptoms\":[\"恶寒重\",\"发热轻\"],\"top_k\":3}'。② 病证图谱：kg/schema/schema.json 定义 DSU 六段结构（病侧/证侧/桥接/临床）——可作状态特征的本体。③ 六者 Agent：agents/ 六目录 SOUL（医者辨证决策的 actor 角色）。"),
  ("[平台改写] 实践建议", "把 BOE 迭代实现于症状-方剂网格：v0 全零 → 迭代 vk+1(s)=max_a(r(s,a)+γΣv_k(s'))，直到收敛。对比平台 Top-K 排序：BOE 的最优动作 vs 检索 Top1，讨论『检索=近似最优决策』的合理性。"),
 ],
},
{
 "sheet": "RL04 价值迭代与策略迭代",
 "title": "Chapter 4 Value Iteration and Policy Iteration 价值迭代与策略迭代",
 "rows": [
  ("[原书] 章节定位", "第一个能找最优策略的算法章。三个算法：价值迭代(VI)、策略迭代(PI)、截断策略迭代(TPI，统一框架)。都是动态规划算法（需模型），是无模型算法（Ch5 起）的基石。"),
  ("[原书] 价值迭代 VI", "vk+1 = maxπ (rπ + γPπ vk)，两步：①策略更新 πk+1 = argmaxπ(rπ+γPπvk)；②价值更新 vk+1 = r_{πk+1} + γP_{πk+1}vk。由收缩映射定理保证收敛到 v*。元素形式：qk(s,a) = Σ_r p(r|s,a)r + γΣ_s' p(s'|s,a)vk(s')，πk+1 选 argmax qk(s,a)。"),
  ("[原书] 策略迭代 PI", "两步循环：①策略评估（求解给定策略的 Bellman 方程 vπ）；②策略改进（贪婪：πk+1 = argmax_a qπk(s,a)）。定理4.1：改进后策略价值不减（vπk+1 ≥ vπk）；有限 MDP 内有限步收敛到最优。"),
  ("[原书] 截断策略迭代 TPI", "统一框架：每轮先做若干步截断的策略评估（j 步迭代 v），再策略改进。j=1 → VI；j=∞ → PI。VI 与 PI 是 TPI 特例。"),
  ("[原书] 实现要点", "矩阵-向量形式理解思想，元素形式实现。网格世界代码：仓库 Code for grid world/ 提供完整 Python 实现（状态索引、转移表、奖励表、VI/PI 迭代循环）。"),
  ("[原书] 书特色", "三个算法的关系用『截断策略评估步数』统一（图4.6 直观）；强调 VI 的每步其实是『策略更新+价值更新』两步；网格世界 9 状态全手动演算。"),
  ("[平台改写] tcmP 映射", "价值迭代 ↔ 治疗方案优化流水线：v_k(症状) 迭代逼近最优疗效评估，π_k 逐步收敛到最优辨证-方剂策略。平台实践：医圣成长引擎的『成长路径规划』可建模为 VI（从住院医到主任医的最优路径）。"),
  ("[平台改写] 平台配置接口", "① 网格世界代码：参考 aiefs 课程 L1-L4 的检索基础设施（tcm_embed.py 的 TF-IDF+FTS5+RRF 就是『模型化』的检索环境）。② 依赖：pip install numpy（矩阵运算 v=(I-γP)⁻¹r）。③ 数据：kg/samples 病证单元的 clinical.recommended_formula 作动作集。"),
  ("[平台改写] 实践建议", "用 numpy 实现 VI 于 9 状态网格：转移矩阵 P(9×9×5)、奖励 r(9×5)，迭代至 ‖vk+1-vk‖<ε。然后替换为症状-方剂网格（从 DSU 数据构建），对比 VI 最优策略与平台检索 Top1 方剂的一致性。"),
 ],
},
{
 "sheet": "RL05 蒙特卡洛方法",
 "title": "Chapter 5 Monte Carlo Methods 蒙特卡洛方法",
 "rows": [
  ("[原书] 章节定位", "第一个无模型(model-free)算法章。哲学：『没有模型就要有数据；没有数据就要有模型；都没有则无解』。数据=智能体与环境交互的经验。"),
  ("[原书] 动机：均值估计", "状态/动作价值都是回报的均值 → 估计价值=均值估计问题。模型已知：E[X]=Σp(x)x；模型未知：用样本均值 x̄=(1/n)Σxj（大数定律保证收敛）。抛硬币例：X=1(正)/-1(反)，多次采样平均逼近真实期望。"),
  ("[原书] MC Basic 算法", "由策略迭代改造：把『用模型计算 vπ』换成『用采样经验估计 vπ』。流程：①从初态 s 按 π 生成完整 episode；②用 return 均值估计 vπ(s)；③策略改进（贪婪）。估计动作价值 qπ(s,a) 需要每个 (s,a) 都被访问（探索）。"),
  ("[原书] MC Exploring Starts", "MC Basic 的低效改进：不从每个 (s,a) 分别开始（低效），而是从随机状态-动作对开始探索（exploring starts），一条 episode 同时更新沿途所有 (s,a) 的 q 值。访问次数记录 N(s,a)。"),
  ("[原书] 关键结论", "MC 方法无偏估计（sample average 是 return 的无偏估计）；无折扣 episodic 任务用 G_t=ΣR；有折扣用折扣回报。MC 的方差大（整条轨迹的随机性），但不需要模型、不需要自举。"),
  ("[原书] 书特色", "均值估计作为统一动机（Ch5/Ch6 共用）；MC Basic→Exploring Starts 的递进展示『从理论算法到实用算法』的改造过程；明确 MC=策略迭代的『数据化』。"),
  ("[平台改写] tcmP 映射", "MC ↔ 病案数据的统计学习：从历史病案（episode=一次完整诊疗过程：就诊→辨证→方剂→复诊转归）估计『某方剂对某证候的疗效均值』。平台病证库的 evidence_level（A/B/C 级）就是历史样本的『质量标签』。"),
  ("[平台改写] 平台配置接口", "① 病案数据：kg/samples DSU 的 clinical.prognosis/typical_case 字段=单条 episode 数据；teaching.typical_case 含完整医案（症状→方剂→转归）。② 采样工具：python random + pandas 对 103 DSU 构建 episodes。③ 检索对照：/semantic-search 的 score 可作 MC 估计的初值。"),
  ("[平台改写] 实践建议", "从 DSU 的 typical_case 抽取 30 条『症状→方剂→疗效』episode，用 MC 估计 v(症状组合)=平均疗效；对比不同方剂在同一证候下的 MC 价值排序，验证『MC 最优方剂』是否与病证库 recommended_formula 一致。"),
 ],
},
{
 "sheet": "RL06 随机逼近",
 "title": "Chapter 6 Stochastic Approximation 随机逼近",
 "rows": [
  ("[原书] 章节定位", "承上启下的『暂停章』：TD 算法与之前算法不同（增量式），本章填补知识缺口——随机逼近(SA)基础。TD 可看作特殊 SA 算法；SGD 也在此介绍。"),
  ("[原书] 动机：增量均值估计", "非增量：收集全部样本再平均（样本多时等待久）。增量式：wk+1 = wk + (1/k)(xk - wk) —— 每来一个样本就地更新。这是所有增量学习算法的原型。"),
  ("[原书] Robbins-Monro 算法", "求解 g(w) = 0 的无模型方法：wk+1 = wk - ak g̃(wk, ηk)，其中 g̃ 是 g 的噪声观测，ak 步长。RM 定理（收敛条件）：① Σak=∞（步长和不收敛→能走到任意远）；② Σak²<∞（步长平方和收敛→噪声被平均掉）。经典选择 ak=1/k。"),
  ("[原书] Dvoretzky 条件", "更一般的收敛条件：wk+1 = wk - ak(wk - xk)，要求 Σak=∞、Σak²<∞（或 a→0）。这些条件保证噪声平均、估计收敛到真值。"),
  ("[原书] SA 与均值估计/SGD", "均值估计=SA 特例（g(w)=w-E[X]）。随机梯度下降：最小化 J(w)=E[f(w,X)]，梯度用单样本近似 ∇J≈∇f(w,xk)，wk+1=wk-ak∇f(wk,xk)——SA 的 J(w) 最小化版本。"),
  ("[原书] 书特色", "用『均值估计的两种实现』讲清增量/非增量；RM 收敛条件用『步长和发散+平方和收敛』的直觉解释；明确 TD=SA（Ch7 直接复用）。"),
  ("[平台改写] tcmP 映射", "SA ↔ 平台的在线学习：每次问诊/检索都是一次新样本，价值估计就地更新（wk+1=wk+α(error)）。这正是平台『对话=进化信号→Agent 调优』CI/CD 闭环的数学内核：每次人机交互都是增量样本。"),
  ("[平台改写] 平台配置接口", "① 日志数据流：平台每次 /consult、/semantic-search 调用都是样本（记录到日志）。② 增量更新示例：python 实现 wk+1=wk+(1/k)(xk-wk) 估计『某症状组合的平均检索分数』。③ 环境变量：DEEPSEEK_API_KEY（LLM 增强，非必需——增量学习零 token 可跑）。"),
  ("[平台改写] 实践建议", "实现增量均值估计：从 /semantic-search 反复查询『失眠』系列症状，记录每次 Top1 分数，用 SA 增量公式在线估计均值；验证收敛曲线（对比非增量全量均值）。体会『平台在线调优不需要重训』的原理。"),
 ],
},
{
 "sheet": "RL07 时序差分方法",
 "title": "Chapter 7 Temporal-Difference Methods 时序差分方法",
 "rows": [
  ("[原书] 章节定位", "TD 方法家族：TD(状态价值) → Sarsa(动作价值) → n-step Sarsa(泛化) → Q-learning(直接解 BOE)。无模型+增量，可看作求解 Bellman/BOE 的 SA 算法。"),
  ("[原书] TD 状态价值算法", "vt+1(st) = vt(st) - αt(st)[vt(st) - (rt+1 + γvt(st+1))]。只更新访问到的状态。核心：用『即时奖励+γ×后继估计』(TD target) 替代 MC 的完整回报——一个时间步就更新（增量、低方差、有偏）。TD 是求解 Bellman 方程的 SA：把 Bellman 残差当误差信号。"),
  ("[原书] Sarsa 算法", "TD 思想从 v 转到 q：qt+1(st,at) = qt(st,at) - α[qt(st,at) - (rt+1 + γqt(st+1,at+1))]。名字来自 (s,a,r,s',a') 五元组。on-policy：行为策略=目标策略。结合贪婪改进 → 找最优策略。"),
  ("[原书] n-step Sarsa", "中间地带：用 n 步回报替代 1 步（TD）或整条（MC）。n=1→Sarsa，n=∞→MC。"),
  ("[原书] Q-learning", "qt+1(st,at) = qt(st,at) - α[qt(st,at) - (rt+1 + γ max_a' qt(st+1,a'))]。直接解 BOE（max 来自最优方程），off-policy（行为策略可不同）。最经典的 RL 算法之一。"),
  ("[原书] 统一视角", "TD 家族统一为『求解 Bellman 方程(Sarsa) 或 BOE(Q-learning) 的增量算法』；MC/TD/DP 的关系：DP=模型+自举，MC=数据+无自举，TD=数据+自举。"),
  ("[原书] 书特色", "先给算法再给『为什么这么设计』（TD=SA 解方程）；Sarsa 从 TD 的『v→q』替换自然导出；Q-learning 的 max 与 BOE 的联系讲透。"),
  ("[平台改写] tcmP 映射", "Q-learning ↔ 六者 Agent 的在线策略优化：状态=患者症状+上下文，动作=推荐方剂/辨证结论，奖励=用户反馈（采纳/复诊转归），Q 表=『症状→最优动作』的经验积累。平台『对话=进化信号』闭环=Q-learning 的分布式实现：每次对话更新 Q(症状, 动作)。"),
  ("[平台改写] 平台配置接口", "① 交互数据源：/consult/sage-zhang-zhongjing 的问答日志（user_level + 主诉 + 回复）。② 奖励设计：/semantic-search 的 rrf 证据分、药者 /pharmacists/review 的 reject/accept 作即时奖励。③ 依赖：numpy 实现 Q 表；无需 gym（用平台 API 作环境）。"),
  ("[平台改写] 实践建议", "实现 mini Q-learning：状态=3 类症状组合（失眠/感冒/头痛），动作=2 个候选方剂，奖励=检索证据分（平台 API 实查），ε-贪婪探索 100 轮。观察 Q 表收敛到『平台检索 Top1』对应动作——验证 TD 学习能复现检索最优。"),
 ],
},
{
 "sheet": "RL08 价值函数方法",
 "title": "Chapter 8 Value Function Methods 价值函数方法",
 "rows": [
  ("[原书] 章节定位", "从表格到函数：大状态/动作空间下表格低效，用参数化函数近似价值 v̂(s,w)。神经网络进入 RL（DQN）。价值函数思想可延伸到策略函数（Ch9）。"),
  ("[原书] 三个基本问题", "P1 模型未知（无模型）；P2 大状态空间（表格不行）；P3 策略如何表示（表格策略无法泛化）。价值函数方法回应 P2：v̂(s,w)=φT(s)w 线性近似（特征向量 φ(s) 内积参数 w）。"),
  ("[原书] 函数近似的更新", "用 SGD 最小化预测误差：w ← w + α[v_target - v̂(s,w)]∇w v̂(s,w)。v_target 来源：MC（完整回报）或 TD（rt+1+γv̂(st+1,w)）→ TD 有偏但方差小。目标函数 J(w)=E[(vπ(s)-v̂(s,w))²]。"),
  ("[原书] DQN 与三个技巧", "DQN = 深度 Q 网络（神经网络 q(s,a,w)）+ 三个关键技巧：①经验回放（replay buffer 打破样本相关性）；②目标网络（target network 固定目标 q̂，稳定训练）；③双 Q 学习（Double DQN 减少 max 高估偏差）。"),
  ("[原书] 与表格法的对比", "表格：精确、简单、大空间不可行；函数：可泛化、参数少、有逼近误差。线性近似有理论保证（收敛性分析），神经网络靠实践验证。"),
  ("[原书] 书特色", "『表格→函数』的转换用直线拟合 v̂=as+b 讲清特征向量概念；三大问题(P1-P3)贯穿全书组织；DQN 三个技巧逐个解释动机（相关性/目标漂移/最大化偏差）。"),
  ("[平台改写] tcmP 映射", "函数逼近 ↔ 病证向量表示：平台的 TF-IDF 向量(tcm_embed) 与 LLM embedding 就是 φ(s) 特征；用神经网络价值函数近似『症状→疗效价值』可泛化到未见过的症状组合。检索证据分=可作价值函数的监督信号。"),
  ("[平台改写] 平台配置接口", "① embedding 依赖：pip install sentence-transformers（可选 BGE 中文模型，平台预留 _bge 接口）；纯 TF-IDF 则零依赖（tcm_embed.py 现成）。② 特征源：tokenize bigram 输出、/semantic-search 分数。③ 训练框架：torch 可选（CPU 小实验即可）。"),
  ("[平台改写] 实践建议", "用 DSU 数据构建监督集：状态特征=TF-IDF 向量（tcm_embed 生成），标签=证据等级映射分数；训练线性 v̂=φTw 近似『病证价值』；对比表格法（每个 DSU 一个格子）与函数法在新病证上的泛化差异——体会 P2 的解法。"),
 ],
},
{
 "sheet": "RL09 策略梯度方法",
 "title": "Chapter 9 Policy Gradient Methods 策略梯度方法",
 "rows": [
  ("[原书] 章节定位", "从 value-based 转向 policy-based：策略用参数化函数 π(a|s,θ) 表示，最优策略=最大化标量指标 J(θ)。大状态空间高效、泛化强、样本效率高。"),
  ("[原书] 表格→函数策略", "表格策略：逐状态改条目；函数策略：只能改参数 θ。最优定义变化：表格=逐状态价值最大；函数=标量 J(θ) 最大。检索动作概率：表格查表；函数 θ 输入网络。"),
  ("[原书] 策略梯度定理", "∇θJ(θ) = E_{S~η, A~π}[∇θ ln π(A|S,θ) qπ(S,A)]。J(θ) 对 θ 的梯度=『对数策略梯度 × 动作价值』的期望。是 policy gradient 的理论核心（推导用 log-derivative trick）。"),
  ("[原书] REINFORCE", "用随机梯度替代期望：θt+1 = θt + α ∇θ ln π(at|st,θt) qt(st,at)。qt 由 MC 估计（完整 episode return）→ Monte Carlo policy gradient。优点：简单、无偏；缺点：高方差（需要很多 episode）。"),
  ("[原书] 优缺点分析", "优点：①连续/大动作空间天然适用（动作概率函数）；②随机策略可表达最优随机策略（表格法只能确定性）；③策略平滑更新（不跳变）。缺点：收敛到局部最优、样本效率低、高方差。"),
  ("[原书] 书特色", "策略梯度定理的完整推导（含 log-derivative 与期望等价变形）；REINFORCE 与 MC 的关联；明确『基于策略』与『基于价值』的分水岭（全书 Ch1-8 value-based，Ch9 起 policy-based）。"),
  ("[平台改写] tcmP 映射", "策略梯度 ↔ 医者 Agent 的行为策略优化：π(a|s,θ) = 给定症状组合推荐方剂 a 的概率，θ 由医圣 SOUL+平台数据调优。『最优诊疗策略=最大化长期疗效指标 J(θ)』。平台六者 SOUL 的人格约束=策略先验（边界），梯度更新=经验调优。"),
  ("[平台改写] 平台配置接口", "① 策略载体：sages/zhang-zhongjing/SOUL.md 的六经辨证规则=策略先验；agents/healer/SOUL.md=医者角色。② 数据：/consult 日志（主诉→回复→后续反馈）作轨迹。③ 梯度计算：softmax 策略 + 检索分数作 q 估计，纯 numpy 实现（无需 torch）。"),
  ("[平台改写] 实践建议", "实现 REINFORCE mini 版：策略=softmax(θ·φ(症状))，动作=5 个候选方剂，轨迹奖励=药者审方 accept(+1)/reject(-1)（用 /pharmacists/review 实查或规则模拟）。训练 200 episode 后对比策略熵与检索 Top1 一致性。"),
 ],
},
{
 "sheet": "RL10 Actor-Critic 方法",
 "title": "Chapter 10 Actor-Critic Methods Actor-Critic 方法",
 "rows": [
  ("[原书] 章节定位", "Actor-Critic = 结构（policy-based + value-based 结合）+ 视角（策略梯度的延伸）。actor=策略更新步（'行动者'，按策略行动）；critic=价值更新步（'评论家'，评估 actor 的价值）。"),
  ("[原书] QAC（最简 AC）", "θt+1 = θt + αθ ∇θ ln π(at|st,θt) q(st,at,wt)（actor，式10.2）；wt+1 = wt + αw[rt+1+γq(st+1,at+1,wt)-q(st,at,wt)]∇wq(st,at,wt)（critic，Sarsa 更新）。关键：q 由 TD 估计（增量、低方差）→ 比 MC 版(REINFORCE)方差小。"),
  ("[原书] A2C（优势 Actor-Critic）", "用优势函数 A=Q-V 替代 Q：θ ← θ + α∇θ ln π(at|st,θ) A(st,at)。优势=该动作优于平均的程度——降低方差、加速收敛。实际用 TD 误差 δt = rt+1+γv(st+1)-v(st) 作为优势估计（无偏且方差小）。"),
  ("[原书] A3C 与 off-policy AC", "A3C：异步多 worker 并行采样更新（提高样本效率）。off-policy AC：行为策略≠目标策略（如 QAC→IAC），用重要性采样修正偏差；SAC 等现代算法的基础。"),
  ("[原书] 兼容性条件与自然梯度", "兼容性条件：critic 的近似 q̂ 满足特定结构时策略梯度无偏（q̂=优势基线形式）。自然梯度：用 Fisher 信息矩阵修正梯度方向（参数化不变性），收敛更稳。"),
  ("[原书] 书特色", "QAC→A2C→off-policy 的递进展示 AC 家族演化；『actor 想干什么 vs critic 说值不值』的直觉贯穿；兼容性条件给出『什么近似不破坏策略梯度』的理论边界。"),
  ("[平台改写] tcmP 映射", "★全书与平台最贴合的映射：actor=医者 Agent（开方决策，六者核心枢纽），critic=规者 Agent（质控评估/审核——『评论家』评价医者的诊疗质量）。A2C 的优势思想 ↔ 平台质控：奖励『优于平均』的诊疗（质控指标对比基线）。药者审方=critic 的硬校验（十八反=硬约束）。"),
  ("[平台改写] 平台配置接口", "① actor 载体：agents/healer（辨证+方剂推荐）；critic 载体：agents/regulator（质控指标）+ agents/pharmacist（审方 reject/accept）。② 线上端点：/agents/regulator/quality、/pharmacists/review 即 critic 的评估接口。③ 依赖：numpy 实现 AC 更新；无 GPU 需求。"),
  ("[平台改写] 实践建议", "模拟六者 AC 闭环：actor=规则策略（按检索 Top1 开方），critic=规者评分（床位周转/处方合规等指标函数）；每轮门诊用 TD 误差 δ 更新 actor 参数，观察『质控反馈→医者策略改进』的闭环收敛——这就是平台『对话=进化信号→Agent 调优→自动上线』CI/CD 闭环的算法原型。"),
 ],
},
]

# ───────────────── xlsx 生成 ─────────────────
HEADERS = ["序号", "模块", "内容"]
PART1_FILL = PatternFill("solid", fgColor="DDEBF7")     # 原书：浅蓝
PART2_FILL = PatternFill("solid", fgColor="E2EFDA")     # 平台改写：浅绿
HDR_FILL = PatternFill("solid", fgColor="4472C4")


def main():
    wb = Workbook()
    wb.remove(wb.active)

    for ch in CHAPTERS:
        ws = wb.create_sheet(title=ch["sheet"])
        ws.append(HEADERS)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = HDR_FILL
        ws.freeze_panes = "A2"
        ws.append(["章", ch["title"], "《Mathematical Foundation of Reinforcement Learning》赵世钰 (Shiyu Zhao), Springer"])
        for c in ws[2]:
            c.font = Font(bold=True)
        for i, (mod, content) in enumerate(ch["rows"], 1):
            is_p2 = mod.startswith("[平台改写]")
            ws.append([i, mod, content])
            r = ws.max_row
            fill = PART2_FILL if is_p2 else PART1_FILL
            ws.cell(r, 2).fill = fill
            ws.cell(r, 3).alignment = Alignment(wrap_text=True, vertical="top")
        # 列宽
        ws.column_dimensions["A"].width = 6
        ws.column_dimensions["B"].width = 26
        ws.column_dimensions["C"].width = 110

    wb.save(OUT)
    total_rows = sum(3 + len(ch["rows"]) for ch in CHAPTERS)
    p2 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[平台改写]"))
    p1 = sum(1 for ch in CHAPTERS for m, _ in ch["rows"] if m.startswith("[原书]"))
    print(f"✅ 已生成: {OUT}")
    print(f"   Sheets: {len(CHAPTERS)} (RL01-RL10) | 内容行 {p1 + p2} "
          f"(Part1 原书 {p1} + Part2 平台改写 {p2}) | 总行 {total_rows}")


if __name__ == "__main__":
    main()
