# -*- coding: utf-8 -*-
'''第7章自检复跑脚本（对应 chapter-07-selfcheck.md）
用法：python check_ch07.py
产出：A2 段落字数实测、B2 公式验算、C1 节引用、C3 章引用。'''

import re, os, glob, math, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = sorted(glob.glob(os.path.join(BASE, '0*-*.md')))

def hanzi(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def total_chars(text):
    return len(re.sub(r'\s', '', text))

def load_all():
    all_text = ''
    for f in FILES:
        with open(f, encoding='utf-8') as fh:
            all_text += fh.read()
    return all_text

def section_A2():
    '''分小节统计每段 [汉字, 总字符]。'''
    print('== A2 段落字数（[汉字, 总字符]）==')
    below400 = []
    tmin = (10 ** 9, None)
    for f in FILES:
        name = os.path.basename(f)[:2]
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        parts = re.split(r'(?=^### 7\.\d\.\d )', text, flags=re.M)
        for p in parts:
            m = re.match(r'### (7\.\d\.\d) ', p)
            if not m:
                continue
            sub = m.group(1)
            body = p.split('\n', 1)[1]
            # 图块行（图题/图片引用/图注，由图表工程师插入）不计入正文段落
            paras = [ln.strip() for ln in body.split('\n')
                     if ln.strip() and not ln.strip().startswith('#')
                     and not ln.strip().startswith('**图')
                     and not ln.strip().startswith('![')
                     and not ln.strip().startswith('图注：')]
            vals = []
            for par in paras:
                h, t = hanzi(par), total_chars(par)
                vals.append('[h%d, t%d]' % (h, t))
                if h < 400:
                    below400.append((sub, h))
                if t < tmin[0]:
                    tmin = (t, sub)
            print('  %s %s: %s' % (name, sub, ' | '.join(vals)))
    print('  纯汉字 < 400 的段落: %s' % below400)
    print('  总字符最小: t=%d @ %s' % (tmin[0], tmin[1]))

def formula_checks():
    '''复算正文全部数值算例。'''
    print('== B2 公式验算 ==')
    rows = [
        ('失眠加权 0.4*0.8+0.2*0.7+0.2*0.6+0.2*0.9', 0.4 * 0.8 + 0.2 * 0.7 + 0.2 * 0.6 + 0.2 * 0.9,
         '正文 v2 已修订为 0.76，实算一致'),
        ('四维(0.4,0.3,0.2,0.1)', 0.4 * 0.9 + 0.3 * 0.6 + 0.2 * 0.5 + 0.1 * 0.7, '正文 0.71'),
        ('四维(0.2,0.5,0.2,0.1)', 0.2 * 0.9 + 0.5 * 0.6 + 0.2 * 0.5 + 0.1 * 0.7, '正文 0.65'),
        ('惩罚 10*(3.5-3)', 10 * (3.5 - 3), '正文 5'),
        ('运动处方 0.3*0.6+0.3*0.4+0.2*0.8+0.2*0.7', 0.3 * 0.6 + 0.3 * 0.4 + 0.2 * 0.8 + 0.2 * 0.7, '正文 0.60'),
        ('熵(0.5,0.5)', -(0.5 * math.log(0.5) + 0.5 * math.log(0.5)), '正文约 0.693'),
        ('熵(0.9,0.1)', -(0.9 * math.log(0.9) + 0.1 * math.log(0.1)), '正文约 0.325'),
        ('熵(0.5,0.3,0.2)', -(0.5 * math.log(0.5) + 0.3 * math.log(0.3) + 0.2 * math.log(0.2)), '习题约 1.03'),
    ]
    for name, val, note in rows:
        print('  %-34s = %.4f  (%s)' % (name, val, note))
    weights = [(0.4, 0.3, 0.2, 0.2), (0.4, 0.3, 0.2, 0.1), (0.2, 0.5, 0.2, 0.1), (0.3, 0.3, 0.2, 0.2)]
    print('  权重归一: %s' % [sum(w) for w in weights])

def cross_refs():
    print('== C1 节引用 / C3 章引用 ==')
    for f in FILES:
        name = os.path.basename(f)[:2]
        with open(f, encoding='utf-8') as fh:
            txt = fh.read()
        secs = sorted(set(int(x) for x in re.findall(r'7\.(\d) 节', txt)))
        chaps = sorted(set(int(x) for x in re.findall(r'第\s*(\d{1,2})\s*章', txt)))
        print('  %s: 引用 7.%s | 第 %s 章' % (name, secs, chaps))

def term_check():
    print('== B1 关键术语英文对照 ==')
    text_all = load_all()
    terms = ['reward function', 'reward engineering', 'reward shaping', 'optimization', 'moderation',
             'scale extension', 'Pareto optimality', 'constraint', 'reward hacking', 'regularization',
             'information entropy', 'entropy bonus', 'system']
    for t in terms:
        print('  %-20s %s' % (t, '出现' if t.lower() in text_all.lower() else '缺失'))

if __name__ == '__main__':
    if len(FILES) != 8:
        sys.exit('未找到 8 个节文件，请确认目录: %s' % BASE)
    section_A2()
    print()
    formula_checks()
    print()
    cross_refs()
    print()
    term_check()
