# -*- coding: utf-8 -*-
"""TTS 医学多音字注音（SSML phoneme, sapi 音标）
医学确定读法: 脏→zàng(去声)、藏象→zàngxiàng、恶(寒/风/热/湿/燥/所恶)→wù、相傅→xiàng
用法: apply_phoneme(text) -> 含目标词时返回 SSML 字符串, 否则原文本
"""
import html

# 词级注音（长词优先: 替换时先长后短避免半字替换）
PHONEME_RULES = [
    ('藏象', 'zang 4 xiang 4'),          # 藏象 读 zàngxiàng
    ('恶寒', 'wu 4 han 2'), ('恶风', 'wu 4 feng 1'),
    ('恶热', 'wu 4 re 4'), ('恶湿', 'wu 4 shi 1'),
    ('恶燥', 'wu 4 zao 4'), ('所恶', 'wu 4'),
    ('相傅', 'xiang 4 fu 4'),            # 相傅之官
]

PREFIX = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">'
SUFFIX = '</speak>'


def has_target(text):
    if '脏' in text:
        return True
    return any(w in text for w, _ in PHONEME_RULES)


def apply_phoneme(text):
    """TTS 文本注音: 含医学多音字时返回 SSML（脏字全注 zàng, 词级按规则）"""
    if not text or not has_target(text):
        return text
    t = html.escape(text, quote=False)  # XML 转义（&<>）
    # ① 脏 全替换 zàng（医学文本无 zāng 用例, 已扫描 609 处验证）
    if '脏' in t:
        tag = '<phoneme alphabet="sapi" ph="zang 4">脏</phoneme>'
        t = t.replace('脏', tag)
    # ② 词级规则（替换原词为带注音的整词标签）
    for word, ph in PHONEME_RULES:
        if word in t:
            tag = f'<phoneme alphabet="sapi" ph="{ph}">{word}</phoneme>'
            t = t.replace(word, tag)
    return PREFIX + t + SUFFIX
