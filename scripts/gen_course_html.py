# -*- coding: utf-8 -*-
"""为素问篇生成 HTML 视频课程（轻量 + 单文件内嵌）
模板: 标题 / 视频(autoplay) / 同步字幕(原文-讲解-图表, 文字先于语音1.8s, 语义结束撤退) / 十段正文(当前高亮+已讲撤退)
用法: python gen_course_html.py [篇列表,逗号分隔|缺省=全部有segs的]
"""
import base64
import json
from pathlib import Path

DOCS = Path(r'C:\Users\DELL\tcmP\docs\视频')

CSS = """
  :root { --primary: #1e8449; --dark: #2c3e50; --gold: #b7950b; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Microsoft YaHei", "SimHei", sans-serif; background: #f4f1ea; }
  .titlebar { background: linear-gradient(135deg, #1e8449, #145a32); color: #fff;
              text-align: center; padding: 34px 20px; }
  .titlebar h1 { font-size: 38px; letter-spacing: 6px; }
  .container { max-width: 1100px; margin: 0 auto; padding: 24px 20px 60px; }
  .player { background: #000; border-radius: 12px; overflow: hidden; margin-bottom: 26px;
            box-shadow: 0 10px 34px rgba(0,0,0,.35); }
  video { width: 100%; display: block; aspect-ratio: 16/9; }
  .sync-caption { background: #0d1b12; padding: 14px 22px; min-height: 108px; }
  .cap-sec { color: #7ee2a8; font-size: 14px; font-weight: 700; margin-bottom: 6px;
             transition: opacity .6s; }
  .cap-orig { color: #fdf9ef; font-size: 17px; line-height: 1.8; text-align: left;
              transition: opacity .6s; }
  .cap-talk { color: #9fc7ae; font-size: 15px; line-height: 1.7; margin-top: 4px; text-align: left;
              transition: opacity .6s; }
  .cap-chart { margin-top: 8px; border-top: 1px solid #1e3b2a; padding-top: 8px; }
  .cap-chart .lbl { color: #7ee2a8; font-size: 13px; margin-bottom: 4px; text-align: left; }
  .cap-gone { opacity: 0; }
  .sec { background: #fff; border-radius: 12px; padding: 22px 26px; margin-bottom: 22px;
         border: 1px solid #e5e0d6; transition: opacity .8s, box-shadow .8s; }
  .sec.now { box-shadow: 0 0 0 3px var(--gold); }
  .sec.done { opacity: .65; }   /* 已讲段弱化但可读（上下文保留, 防误解） */
  .sec-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
  .sec-no { background: var(--primary); color: #fff; padding: 5px 16px; border-radius: 18px; font-size: 14px; }
  .sec h2 { color: var(--dark); font-size: 23px; }
  .orig { font-size: 17px; line-height: 1.9; color: #2c3e50; text-align: left;
          background: #fdf9ef; border-left: 5px solid var(--gold); padding: 14px 20px;
          border-radius: 0 8px 8px 0; }
  .talk { font-size: 16px; line-height: 1.9; color: #4a4a4a; text-align: left; margin-top: 10px; }
  .talk b { color: var(--primary); }
  .footer { text-align: center; color: #999; font-size: 13px; padding: 20px; }
"""

JS_TMPL = """
const SUBS = @@SUBS@@;
const v = document.getElementById('v');
const capSec = document.getElementById('capSec');
const capOrig = document.getElementById('capOrig');
const capTalk = document.getElementById('capTalk');
const SECS = document.querySelectorAll('.sec');
const CAP_LEAD = 1.8;   // 文字先于语音出现(≤2s, 视觉比听觉敏感)
const SEG_DUR = 20;     // 段参考时长(比例)
const totalRef = SUBS.length * SEG_DUR;

function setCap(s, on) {
  capSec.classList.toggle('cap-gone', !on);
  capOrig.classList.toggle('cap-gone', !on);
  capTalk.classList.toggle('cap-gone', !on);
  if (on && s) {
    capSec.textContent = '\\u258d' + s.title;
    capOrig.textContent = s.orig;            // 原文全文
    capTalk.textContent = s.talk;            // 讲解全文（不截断: 上下文完整防误解）
    const cc = document.getElementById('capChart');
    cc.innerHTML = s.chart
      ? '<div class="lbl">📊 图表</div><img src="' + s.chart + '" style="max-height:130px;border-radius:6px;" alt="图表">'
      : '<div class="lbl">📊 图表</div><span style="color:#5a7d6a;font-size:13px;">（本段无图表）</span>';
  }
}

// 段间衔接: 上段已讲完→撤退并显示衔接上下文（防断章误解）
function showBridge(idx) {
  const prev = SUBS[idx - 1];
  const next = SUBS[idx];
  if (prev) {
    const tail = prev.talk.length > 40 ? prev.talk.slice(-40) : prev.talk;
    capSec.textContent = '\\u258d第' + '一二三四五六七八九十'[idx - 1] + '段已讲完';
    capOrig.textContent = '…' + tail;
    capTalk.textContent = '（片刻思考——下一段开讲：' + next.title + '）';
    const cc = document.getElementById('capChart');
    cc.innerHTML = '<div class="lbl">📊 图表</div><span style="color:#5a7d6a;font-size:13px;">（衔接中）</span>';
  }
}

function markSec(idx) {
  SECS.forEach(function (el, k) {
    const n = k + 1;
    el.classList.toggle('now', n === idx);
    el.classList.toggle('done', n < idx);   // 已讲完: 弱化保留(上下文可回看)
  });
}

v.addEventListener('timeupdate', function () {
  const frac = (v.currentTime || 0) / (v.duration || 600);
  const tRef = frac * totalRef;
  // 语音所在段（文字窗口: 领先 CAP_LEAD 出现, 段尾+0.8s 撤退）
  let idx = Math.floor(tRef / SEG_DUR);
  if (idx < 0) idx = 0;
  if (idx >= SUBS.length) idx = SUBS.length - 1;
  const showStart = idx * SEG_DUR - CAP_LEAD;          // 文字早于语音 1.8s
  const retreat = idx * SEG_DUR + SEG_DUR + 0.8;       // 语义结束(段尾+0.8s)撤退
  if (tRef >= showStart && tRef <= retreat) {
    setCap(SUBS[idx], true);
  } else if (tRef < showStart) {
    showBridge(idx);                                   // 衔接期: 上段尾句+下段预告
  } else {
    showBridge(Math.min(idx + 1, SUBS.length - 1));    // 撤退期: 衔接上下文
  }
  markSec(idx);
});
// 自动播放（静音起步, 交互开声）
v.muted = true; v.play().catch(function () {});
const _un = function () { v.muted = false; };
document.addEventListener('click', _un, { once: true });
document.addEventListener('keydown', _un, { once: true });
"""

CN_NUM = '一二三四五六七八九十'


def build_html(ch, name, video_src, subs_js):
    title = f'黄帝内经·素问{ch}·{name}'
    secs = []
    for i, s in enumerate(subs_js, 1):
        secs.append(f'''  <div class="sec" data-i="{i}">
    <div class="sec-head"><span class="sec-no">第{CN_NUM[i-1]}段</span><h2>{s['title']}</h2></div>
    <div class="orig">{s['orig']}</div>
    <div class="talk">{s['talk']}</div>
  </div>''')
    subs_json = json.dumps(subs_js, ensure_ascii=False)
    js = JS_TMPL.replace('@@SUBS@@', subs_json)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>

<div class="titlebar"><h1>{title}</h1></div>

<div class="container">
  <div class="player">
    <video id="v" controls autoplay muted playsinline preload="auto">
      <source src="{video_src}" type="video/mp4">
      您的浏览器不支持 HTML5 视频播放，请下载后观看：<a href="{video_src}">{video_src}</a>
    </video>
    <div class="sync-caption" id="capBox">
      <div class="cap-sec" id="capSec">▍第 1 段</div>
      <div class="cap-orig" id="capOrig"></div>
      <div class="cap-talk" id="capTalk"></div>
      <div class="cap-chart" id="capChart"></div>
    </div>
  </div>
{chr(10).join(secs)}
</div>

<div class="footer">{title} · 知识网络课程教学</div>

<script>{js}</script>
</body>
</html>
'''


CH_NAMES = {'1': '上古天真论', '2': '四气调神大论', '3': '生气通天论', '4': '金匮真言论', '5': '阴阳应象大论',
            '6': '阴阳离合论', '7': '阴阳别论', '8': '灵兰秘典论', '9': '六节藏象论', '10': '五藏生成篇',
            '11': '五藏别论', '12': '异法方宜论', '13': '移精变气论',
            '14': '汤液醪醴论', '15': '玉版论要'}
CH_NAMES.update({str(i): f'SW{i}' for i in range(16, 82)})


def main():
    import sys
    chs = sys.argv[1].split(',') if len(sys.argv) > 1 else list(CH_NAMES.keys())
    for ch in chs:
        name = CH_NAMES.get(ch, f'SW{ch}')
        segs_file = DOCS / f'segs_suwen{ch}.json'
        if not segs_file.exists():
            print(f'跳过 素问{ch}（无 segs）')
            continue
        segs = json.loads(segs_file.read_text(encoding='utf-8'))
        subs = [{'title': s['title'], 'orig': s['orig'], 'talk': s['talk'], 'chart': None}
                for s in segs]
        mp4_name = f'素问01-{name}.mp4' if ch == '1' else f'素问{ch}-{name}.mp4'
        # 轻量版
        light = DOCS / f'素问{ch}-{name}-视频课程.html'
        light.write_text(build_html(ch, name, mp4_name, subs), encoding='utf-8')
        # 单文件版（视频内嵌）
        mp4 = DOCS / mp4_name
        b64 = base64.b64encode(mp4.read_bytes()).decode('ascii')
        single = DOCS / f'素问{ch}-{name}-视频授课.html'
        data_src = f'data:video/mp4;base64,{b64}'
        single.write_text(
            build_html(ch, name, data_src, subs).replace(
                f'<source src="{data_src}" type="video/mp4">',
                f'<source src="{data_src}" type="video/mp4">\n'
                f'      <source src="{mp4_name}" type="video/mp4">'),
            encoding='utf-8')
        print(f'✅ 素问{ch}: 轻量({light.stat().st_size//1024}KB) + 单文件({single.stat().st_size//(1024*1024)}MB)')


if __name__ == '__main__':
    main()
