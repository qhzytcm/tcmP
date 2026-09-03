# Canonical Test / Lint / Build — cmrl 教材项目规范命令

项目级规范验证入口（解决 ad-hoc 验证状态机问题）。全部用 **Anaconda python**（含 openpyxl/matplotlib）运行。

## 命令

```powershell
# 语法/规范检查（215 脚本 py_compile + 图注行数=图数 + 图题黑体）
python C:\Users\DELL\tcmP\scripts\canonical_lint.py

# 交付产物完整性（45 幅 PNG + 知识树 + Excel 图片 46 + 章节 sheet）
python C:\Users\DELL\tcmP\scripts\canonical_build.py

# 全书统一验证（终检 3/3 + 正文 verify + 图注 45 同步/e引导/字数 + 字号 + 树形 + 封面页）
python C:\Users\DELL\tcmP\scripts\canonical_test.py
```

退出码：0 = 全绿；1 = 有失败。三件套可组合：

```powershell
python scripts\canonical_lint.py; if ($LASTEXITCODE -eq 0) { python scripts\canonical_build.py }; if ($LASTEXITCODE -eq 0) { python scripts\canonical_test.py }
```

## 覆盖断言

| 入口 | 检查项 |
|---|---|
| **lint** (3) | L1 py_compile 215 脚本 / L2 各章图注行数=图数 / L3 图题行黑体 |
| **build** (4) | B1 章节 PNG 45 幅非空 / B2 知识树树形版 / B3 Excel 图片 46（45+封面） / B4 章节 sheet 齐全 |
| **test** (8) | T1 图表终检 3/3（45/45 哈希）/ T2 正文 verify / T3 图注 45 同步 / T4 e.阅读引导 / T5 字数 ≤650 / T6 字号 ≥9 / T7 知识树树形 / T8 封面页锚 R40+自下而上 |

## 验证记录（2026-08-20）

- CANONICAL LINT: **ALL PASS (3/3)**
- CANONICAL BUILD: **ALL PASS (4/4)**
- CANONICAL TEST: **ALL PASS (8/8)**

## 已知环境说明

- 依赖：Anaconda python（openpyxl、matplotlib、PIL）；Graphviz 16.0.0（C:\Tools\graphviz\Graphviz-16.0.0-win64\bin，可选）
- 桌面 Excel 被 Excel/WPS 占用时写入类操作会 PermissionError（读取不受影响）；运行 canonical_test 前请关闭
- openpyxl 长文本偶发截断（R8/R16/R18/R22 等稳定位置）——图注写入后必须回读校验，截断用索引赋值 `ws['C'+str(row)]=None` 后重写
