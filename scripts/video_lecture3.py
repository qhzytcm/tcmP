# -*- coding: utf-8 -*-
"""video_lecture3.py — 课件视频 v3（十段 PPT 内容 · 10-15 分钟 · 无平台/全书导论）
每段: 原文朗读 + 注释简读 + 讲解（PPT 同步要点）→ TTS 配音 + PPT 画面页
女子/男子段: 三线表全屏页
输出: 素问01-上古天真论.mp4/.video
"""
import asyncio
import shutil
import sys
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(r'C:\Users\DELL\textbook-project\drafts\cmrl\figures\book\video')
TABLES = OUT_DIR / 'tables'
FONT = r'C:\Windows\Fonts\msyh.ttc'
FONT_B = r'C:\Windows\Fonts\msyhbd.ttc'
W, H = 1920, 1080

# ===== 十段内容（原文朗读 + 注释 + 讲解）=====
SEGS = [
    ('第一段 · 开篇', '#c0392b', 'plain',
     '昔在黄帝，生而神灵，弱而能言，幼而徇齐，长而敦敏，成而登天。',
     '注释：生而神灵，先天禀赋聪慧；弱而能言，幼年善言；徇齐，敏慧；敦敏，敦厚聪敏。',
     '开篇立人：黄帝，生而神灵的圣人，向天师岐伯请教生命的根本问题。八句交代提问者，正文由此展开。'),
    ('第二段 · 发问', '#c0392b', 'plain',
     '乃问于天师曰：余闻上古之人，春秋皆度百岁，而动作不衰；今时之人，年半百而动作皆衰者，时世异耶？人将失之耶？',
     '注释：春秋，年龄；度百岁，活过百岁；时世异，时代不同；人将失，人自失养生之道。',
     '黄帝一问双问：今人半寿早衰，是时代变了，还是人自己失了道？岐伯全篇只答内因——养生成败，操之在己，不归咎时代。'),
    ('第三段 · 总答：四个基本盘', '#1e8449', 'plain',
     '岐伯对曰：上古之人，其知道者，法于阴阳，和于术数，食饮有节，起居有常，不妄作劳，故能形与神俱，而尽终其天年，度百岁乃去。',
     '注释：知道，懂得养生之道；法于阴阳，效法天地节律；和于术数，调和导引吐纳；不妄作劳，不过度劳累。',
     '长寿四个基本盘：法于阴阳，和于术数，食饮有节，起居有常，不妄作劳。守住四盘，形与神俱，尽终天年，度百岁乃去。'),
    ('第四段 · 论上古人与论今人', '#c0392b', 'plain',
     '今时之人不然也，以酒为浆，以妄为常，醉以入房，以欲竭其精，以耗散其真，不知持满，不时御神，务快其心，逆于生乐，起居无节，故半百而衰也。',
     '注释：以酒为浆，把酒当水；以妄为常，把妄乱当常态；竭其精，耗竭肾精；散其真，耗散真元；不时御神，不按时驾驭精神。',
     '从精气神三个维度对比分析：精，物质结构——上古人不妄作劳以守精，今人醉以入房以竭精；气，能量信息——上古人法于阴阳以顺气，今人以妄为常以乱气；神，适应储备潜能——上古人形与神俱以全神，今人不时御神以耗神。原文、注释、语音，视频过程同步对应。'),
    ('第五段 · 圣人教下：恬惔循到', '#1e8449', 'quote',
     '夫上古圣人之教下也，皆谓之虚邪贼风，避之有时，恬惔虚无，真气从之，精神内守，病安从来。',
     '注释：虚邪贼风，四时不正之气；恬惔虚无，内心清静淡泊；真气从之，正气顺从；精神内守，神不外驰。',
     '精气神，等于物质结构、能量信息、适应储备潜能的最适化：恬惔虚无，神归其位；真气从之，气顺其道；精神内守，精守其本。三者和合，病安从来。这里衬托出我们时代的储备潜能最适化：生理状态，心理状态，人机关系，生态协同，四类潜能。不是最优，而是最适——确保从容长寿的全生命周期质量。'),
    ('第六段 · 德全不危：深思远虑', '#1e8449', 'quote',
     '是以志闲而少欲，心安而不惧，形劳而不倦，气从以顺，各从其欲，皆得所愿。故美其食，任其服，乐其俗，高下不相慕，其民故曰朴。是以嗜欲不能劳其目，淫邪不能惑其心，愚智贤不肖，不惧于物，故合于道。所以能年皆度百岁，而动作不衰者，以其德全不危也。',
     '注释：志闲，心志闲适；少欲，欲望减少；心安不惧，内心安定无所恐惧；德全不危，道德全备则神全形不敝。',
     '德全不危，是深思远虑的生命战略：志闲而少欲，神不外驰；心安而不惧，气定神闲；形劳而不倦，精不妄耗。德全，是精气神三者和合的修养总纲——深思远虑，不为外物所惧，方得百岁而动作不衰。'),
    ('第七段 · 女子七纪：一七至七七', '#1a5276', 'table',
     '女子七岁，肾气盛，齿更发长；二七而天癸至，任脉通，太冲脉盛，月事以时下，故有子；三七肾气平均，故真牙生而长极；四七筋骨坚，发长极，身体盛壮；五七阳明脉衰，面始焦，发始堕；六七三阳脉衰于上，面皆焦，发始白；七七任脉虚，太冲脉衰少，天癸竭，地道不通，故形坏而无子。',
     '注释：天癸，肾精所化生殖之精；任通冲盛，任脉通、冲脉盛则月事按时；地道不通，绝经。以七为纪，女子应月。',
     '请看女子生命周期三线表。女子以七为纪，七个阶段：七岁肾气盛，齿更发长；十四岁天癸至，初潮，有子；二十一岁肾气平均，真牙生；二十八岁筋骨坚，身体盛壮，生理巅峰；三十五岁阳明脉衰，面始焦；四十二岁三阳脉衰，发始白；四十九岁天癸竭，绝经，形坏无子。引导观看者观察、思考、行动，多循环迭代式自主成长：观察每个年龄段的生理信号，思考肾气天癸的盛衰规律，行动对应阶段的养护策略。'),
    ('第八段 · 男子八纪：一八至八八', '#1a5276', 'table',
     '丈夫八岁，肾气实，发长齿更；二八肾气盛，天癸至，精气溢泻，阴阳和，故能有子；三八肾气平均，筋骨劲强，故真牙生而长极；四八筋骨隆盛，肌肉满壮；五八肾气衰，发堕齿槁；六八阳气衰竭于上，面焦，发鬓颁白；七八肝气衰，筋不能动，天癸竭，精少，肾藏衰，形体皆极；八八则齿发去。',
     '注释：精气溢泻，精液溢泻；肝气衰则筋不能动；天癸竭精少。以八为纪，男子应风。',
     '再看男子生命周期三线表。男子以八为纪，八个阶段：八岁肾气实，发长齿更；十六岁天癸至，精气溢泻，能有子；二十四岁肾气平均，真牙生；三十二岁筋骨隆盛，肌肉满壮，生理巅峰；四十岁肾气衰，发堕齿槁；四十八岁阳气衰竭，面焦鬓白；五十六岁肝气衰，筋不能动，天癸竭；六十四岁，齿发去。引导观看者观察、思考、行动，多循环迭代式自主成长：观察每个年龄段的生理信号，思考肾气天癸的盛衰规律，行动对应阶段的养护策略——一八养先天，二八节欲保精，三八强筋健骨，四八固肾精，五八补肾填精，六八温阳益气，七八养肝柔筋，八八颐养天年。'),
    ('第九段 · 四境界一二：贤人 · 圣人', '#5d4037', 'plain',
     '其次有贤人者，法则天地，象似日月，辨列星辰，逆从阴阳，分别四时，将从上古合同于道，亦可使益寿而有极时。其次有圣人者，处天地之和，从八风之理，适嗜欲于世俗之间，无恚嗔之心，行不欲离于世，被服章，举不欲观于俗，外不劳形于事，内无思想之患，以恬愉为务，以自得为功，形体不敝，精神不散，亦可以百数。',
     '注释：贤人，法则天地、辨列星辰、逆从阴阳；圣人，处天地之和、从八风之理、恬愉自得。四境界由低到高：贤人、圣人、至人、真人。',
     '先讲贤人：四类储备潜能最适化的跳跃式设计——法则天地，象似日月，辨列星辰，主动建模天地规律；逆从阴阳，分别四时，大胆应用。引导观看者人生规划的跳跃式设计：不拘条件，主动创造，观察、思考、行动，不顾条件而行，亦可使益寿而有极时。再讲圣人：四类储备潜能最适化的随遇而安式设计——处天地之和，生态协同；适嗜欲于世俗，生理状态融入日常；无恚嗔之心，心理状态平和；以恬愉为务，与生活工具和乐相处。引导观看者人生规划的随遇而安式设计：外不劳形，内无思想之患，形体不敝，精神不散，亦可以百数。由贤人至圣人，认知逐步提高。'),
    ('第十段 · 四境界三四：至人 · 真人', '#5d4037', 'plain',
     '中古之时，有至人者，淳德全道，和于阴阳，调于四时，去世离俗，积精全神，游行天地之间，视听八达之外，此盖益其寿命而强者也，亦归于真人。黄帝曰：余闻上古有真人者，提挈天地，把握阴阳，呼吸精气，独立守神，肌肉若一，故能寿敝天地，无有终时，此其道生。',
     '注释：至人，淳德全道、和于阴阳、调于四时、积精全神；真人，提挈天地、把握阴阳、呼吸精气、独立守神。',
     '先讲至人：四类储备潜能最适化的适应式设计——淳德全道，生理；积精全神，心理；调于四时，生态；和于阴阳，协同。引导观看者人生规划的适应式设计：随境调整，顺势而为，观察、思考、行动，追求循环，益寿而强，亦归于真人。再讲真人：生命全过程每阶段四类储备潜能最适化的完美实现——提挈天地，肌肉若一，生理状态；独立守神，无有终时，心理状态；呼吸精气，以道御身，人机关系；把握阴阳，与天地合，生态协同。引导观看者人生规划的塔顶式设计：以最高标准确立人生目标，自上而下规划，观察、思考、行动，完美闭环，寿敝天地，无有终时。由至人至真人，认知登顶。四境界由低到高：贤人、圣人、至人、真人——逐步提高认知的适应过程，精气神最适化，不是最优，而是最适。'),
]


def wrap(d, text, font, max_w):
    lines, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=font) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def make_ppt_page(seg, idx):
    title, color, kind, orig, note, talk = seg
    img = Image.new('RGB', (W, H), '#faf8f2')
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(FONT_B, 56)
    f_orig = ImageFont.truetype(FONT_B, 40)
    f_note = ImageFont.truetype(FONT, 26)
    f_talk = ImageFont.truetype(FONT, 32)
    f_foot = ImageFont.truetype(FONT, 24)

    d.rectangle([0, 0, W, 14], fill=color)
    d.text((70, 50), f'黄帝内经·素问01·上古天真论  |  {title}', font=f_title, fill='#2c3e50')
    d.line([70, 140, W - 70, 140], fill='#bdc3c7', width=2)
    # 原文（大字, 换行）
    y = 190
    for ln in wrap(d, orig, f_orig, W - 160):
        d.text((80, y), ln, font=f_orig, fill='#5d4037')
        y += 62
    # 注释
    y += 14
    d.text((80, y), '【注释】', font=f_note, fill='#7f8c8d')
    y += 40
    for ln in wrap(d, note, f_note, W - 160)[:3]:
        d.text((80, y), ln, font=f_note, fill='#95a5a6')
        y += 40
    # 讲解要点
    y += 16
    d.text((80, y), '【讲解】', font=f_talk, fill=color)
    y += 52
    for ln in wrap(d, talk, f_talk, W - 160)[:8]:
        d.text((80, y), ln, font=f_talk, fill='#34495e')
        y += 56
        if y > 1000:
            break
    d.text((80, 1030), f'第 {idx}/10 段  |  原文不变 · 注释可调 · 发挥讲解', font=f_foot, fill='#95a5a6')
    return img


def make_table_page(png_src, out_png):
    img = Image.open(png_src)
    w, h = img.size
    scale = min((W - 160) / w, (H - 140) / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGB', (W, H), '#ffffff')
    canvas.paste(img, ((W - nw) // 2, (H - nh) // 2 + 20))
    canvas.save(out_png)


async def tts_one(voice, text, out_mp3, retries=5):
    for attempt in range(retries):
        try:
            await edge_tts.Communicate(text, voice, rate='-3%').save(str(out_mp3))
            # 有效性校验: MP3 头 + 最小大小
            if out_mp3.exists() and out_mp3.stat().st_size > 8 * 1024:
                head = out_mp3.read_bytes()[:3]
                if head == b'ID3' or head[:2] == b'\xff\xfb':
                    return out_mp3
            print(f'    TTS 产物异常({out_mp3.stat().st_size if out_mp3.exists() else 0}B), 重试')
            out_mp3.unlink(missing_ok=True)
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 3 * (2 ** attempt)  # 指数退避: 3,6,12,24,48s（微软限流窗口）
            print(f'    TTS 重试 {attempt + 1}: {type(e).__name__} (等{wait}s)')
            await asyncio.sleep(wait)
    raise RuntimeError(f'TTS 失败: {out_mp3.name}')


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = OUT_DIR / 'v3'
    work.mkdir(exist_ok=True)
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
    from moviepy.audio.io.AudioFileClip import AudioFileClip as _AFC

    total_chars = sum(len(s[5]) + len(s[3]) + len(s[4]) for s in SEGS)
    print(f'十段总字数: {total_chars}（预期 10-15 分钟 ≈ 2000-2800 字）')

    clips = []
    for i, seg in enumerate(SEGS, 1):
        title, color, kind, orig, note, talk = seg
        tts_text = orig + '。' + talk   # 只朗读 原文+讲解（不发声注释）
        mp3 = work / f'p{i:02d}.mp3'
        if not mp3.exists():
            import time
            time.sleep(6)  # 段间间隔, 规避微软 TTS 连续调用限流
            voice = 'zh-CN-YunxiNeural' if i in (3, 5, 6, 9, 10) else 'zh-CN-XiaoxiaoNeural'
            asyncio.run(tts_one(voice, tts_text, mp3))
        # 画面: 段标题卡 + （三线表段附加表格页）
        pages = []
        ppt = work / f'p{i:02d}_ppt.png'
        make_ppt_page(seg, i).save(str(ppt))
        pages.append(ppt)
        if kind == 'table':
            tname = '表1-女子生命周期.png' if i == 7 else '表2-男子生命周期.png'
            tp = work / f'p{i:02d}_table.png'
            make_table_page(TABLES / tname, tp)
            pages.append(tp)
        audio = _AFC(str(mp3))
        seg_dur = audio.duration
        per = seg_dur / len(pages)
        for j, pg in enumerate(pages):
            clips.append(ImageClip(str(pg), duration=per + 0.3).with_audio(
                audio.subclipped(j * per, min((j + 1) * per + 0.3, seg_dur)) if False else audio
                if len(pages) == 1 else
                _AFC(str(mp3)).subclipped(j * per, min((j + 1) * per + 0.3, seg_dur))))
        print(f'  段 {i}/10 [{title}] {seg_dur:.0f}秒 {"+表格页" if kind == "table" else ""}')

    final = concatenate_videoclips(clips, method='compose')
    out = OUT_DIR / '素问01-上古天真论.mp4'
    final.write_videofile(str(out), fps=24, codec='libx264', audio_codec='aac',
                          temp_audiofile=str(work / 't.m4a'), logger=None)
    shutil.copy2(out, OUT_DIR / '素问01-上古天真论.video')
    mins = final.duration / 60
    print(f'✅ 课件视频 v3: {out.name} ({out.stat().st_size // (1024*1024)}MB, {mins:.1f} 分钟, {len(SEGS)} 段)')
    print(f'   时长目标 10-15 分钟: {"✅达标" if 10 <= mins <= 15 else "⚠需调整"}')


if __name__ == '__main__':
    main()
