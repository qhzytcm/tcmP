# -*- coding: utf-8 -*-
"""为缺 changelog 的章节补建简版修改说明书（G4 E 项门禁）"""
from pathlib import Path

D = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl')

# 各章修订记录（ch03/ch06 已有完整 changelog；其余按 L3 复审结论补建）
RECORDS = {
    1: ('无 P0 修订项', 'L3 初审通过（94/90 分）；三种最适度英文为全书基准（individual positioning 等），无修订'),
    2: ('无 P0 修订项', 'L3 初审通过（93/92 分）；无严重问题，无修订'),
    4: ('P0-5 辨证示例、P0-6 英文统一', '4.3.1 辨证示例修正（风热证×麻黄汤矛盾解除）；三种最适度英文统一为 ch01 基准；修订记录详见 chapter-04-selfcheck.md D2'),
    5: ('P0-1 例5.6、P0-6 英文统一、P0-7 s6 方向、方名', '例5.6 乙回报 1.71→1.9；三种最适度英文统一（mutual flourishing→environment co-prosperity，6 处）；例5.4 s6 方向改向下；清心泻火方→黄连解毒汤；修订记录详见 selfcheck D4/D5 与复审意见'),
    7: ('P0-3 失眠加权', '失眠加权总分 0.78→0.76（正文/习题/配图三处一致）；修订记录详见 chapter-07-selfcheck.md D1'),
    8: ('无 P0 修订项', 'L3 初审通过（93/90 分）；无严重问题；tcmP 提及频次建议级，无修订'),
    9: ('P0-9 梯度口径', '9.2.2 统一为 qπ 口径并标注：状态分布 0.726/0.274、梯度 0.495/−0.495；习题同步；修订记录详见 chapter-09-selfcheck.md D4/D5'),
    10: ('无 P0 修订项', 'L3 初审通过（95/88 分）；收官章无 P0 问题；importance ratio 英文对照为建议级，无修订'),
}

for ch, (items, note) in RECORDS.items():
    d = D / f'ch{ch:02d}'
    f = d / f'chapter-{ch:02d}-changelog.md'
    if f.exists():
        print(f'[skip] ch{ch:02d} 已有 changelog')
        continue
    content = f"""# 第{ch}章 修改说明书（changelog）

| 项目 | 内容 |
|------|------|
| 教材 | 《中医场景强化学习》第{ch}章 |
| 版本 | v1 → v2（L3 三审修订后） |
| 修订日期 | 2026-08-15 |
| 修订项 | {items} |

## 修订说明

{note}

## 复审状态

L3 三审复审：{items if items != '无 P0 修订项' else '无修订项，复审通过'}。
"""
    f.write_text(content, encoding='utf-8')
    print(f'[write] ch{ch:02d}/chapter-{ch:02d}-changelog.md')

# 验证: 10 章 changelog 齐备
missing = [ch for ch in range(1, 11)
           if not (D / f'ch{ch:02d}' / f'chapter-{ch:02d}-changelog.md').exists()]
print(f'[check] 缺 changelog: {missing if missing else "无（10/10 齐备）"}')
