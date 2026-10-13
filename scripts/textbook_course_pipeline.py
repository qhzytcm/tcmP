# -*- coding: utf-8 -*-
"""textbook_course_pipeline.py — 学科教材(xlsx) → 授课网络视频 + 网页课件

分阶段流水线（每章一个视频 + 一个轻量 HTML 课件；全部章合成课程索引页）：
  xlsx 章 sheet → 解析四级目录正文 → 段落切分(≤13段/章)
  → 浪潮远程 edge-tts（本机 IP 被限流，必须走远程）→ PIL 幻灯页
  → ffmpeg 合成 mp4（静图+音频→段mp4→concat）→ 轻量 HTML 课件 → 课程索引

产出（仓库内，媒体入 .gitignore）：
  docs/教材视频/<slug>/第NN章-<章名>.mp4                 （轻量 HTML 引用）
  docs/教材视频/<slug>/第NN章-<章名>-视频课程.html         （入库）
  docs/教材视频/<slug>/index.html + <slug>-course.json    （入库）
  docs/教材视频/<slug>/chNN/                              （中间件，gitignore）

用法：
  python scripts/textbook_course_pipeline.py --book <xlsx> --slug zhjcl --name 中医基础理论 --parse-only --chapter 1
  python scripts/textbook_course_pipeline.py --book <xlsx> --slug zhjcl --name 中医基础理论 --chapter 1
  python scripts/textbook_course_pipeline.py --book <xlsx> --slug zhjcl --name 中医基础理论 --all
"""
from __future__ import annotations
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs" / "教材视频"
FF = r"C:\Tools\ffmpeg.exe"
REMOTE = dict(hostname="192.168.0.102", port=22, username="administrator",
              password="Cdy123456")
MAX_SEGS = 13          # 每章最多分段数（超出则该章拆分/截断）
SEG_MAXLEN = 520       # 每段讲解文本上限
FONT = r"C:\Windows\Fonts\msyh.ttc"
FB = r"C:\Windows\Fonts\msyhbd.ttc"

# 跳过：表头 / 网络校准注记 / 空行
SKIP_RE = re.compile(r"^【")
HEAD_CODE_RE = re.compile(r"^(第?\d+(\.\d+)*)([\s　·]|$)")
HEAD_CHAPTER_RE = re.compile(r"^第\d+章")


def _is_heading(t: str) -> bool:
    if not t:
        return False
    if HEAD_CHAPTER_RE.match(t):
        return True
    if HEAD_CODE_RE.match(t):
        return True
    # 短文本且不以句末标点结尾 → 视为标题（如 中药学 的“麻黄”“麻黄·来源与性味归经”）
    if len(t) < 40 and not t.endswith(("。", "！", "；", "”")):
        return True
    return False


def parse_chapter(xlsx: Path, sheet: str) -> list[dict]:
    """解析章 sheet（章|节|小节|段|内容）→ 段落列表 [{no,title,text}]"""
    wb = openpyxl.load_workbook(str(xlsx), read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        wb.close()
        raise KeyError(f"sheet 不存在: {sheet}; 现有: {wb.sheetnames}")
    ws = wb[sheet]
    stack: dict[int, str] = {}     # level -> heading text
    buckets: list[dict] = []       # [{title, level, paras:[...]}]
    cur: dict | None = None

    for row in ws.iter_rows(values_only=True):
        cells = [(str(c).strip() if c is not None else "") for c in row]
        if not cells:
            continue
        content = cells[-1]
        if not content or content == "内容" or SKIP_RE.match(content):
            continue
        # 章/节/小节/段 列另有编码——但标题文本总在最后一列
        if _is_heading(content):
            # 级别判定：优先看内容里的编码深度
            m = HEAD_CODE_RE.match(content)
            level = 3
            if HEAD_CHAPTER_RE.match(content):
                level = 1
            elif m:
                depth = m.group(1).count(".")
                level = min(depth + 1, 4)
            # 新段落标题：小节(level>=3) 起新桶；节(2) 也起桶（若无小节则作段标题）
            key = (level, content)
            if buckets and buckets[-1]["level"] == level and buckets[-1]["title"] == content:
                continue
            cur = {"title": content, "level": level, "paras": []}
            buckets.append(cur)
        else:
            if cur is None:
                cur = {"title": "概述", "level": 3, "paras": []}
                buckets.append(cur)
            cur["paras"].append(content)
    wb.close()

    # 合并：以「实际承载正文的桶」为段。若某桶无正文(bodyless 标题桶)，其后的正文归到最近正文桶
    segs = []
    for b in buckets:
        text = " ".join(b["paras"]).strip()
        if text:
            segs.append({"title": b["title"], "text": text})
    # 若正文桶太少（标题多正文少），退化为按 节(level2) 聚合
    if len(segs) == 0:
        return []
    # 合并相邻过短段，直至 ≤ MAX_SEGS
    while len(segs) > MAX_SEGS:
        # 找到最短的相邻对合并
        i = min(range(len(segs) - 1), key=lambda k: len(segs[k]["text"]) + len(segs[k + 1]["text"]))
        merged = {"title": segs[i]["title"], "text": (segs[i]["text"] + " " + segs[i + 1]["text"]).strip()}
        segs[i:i + 2] = [merged]
    out = []
    for i, s in enumerate(segs, 1):
        text = s["text"]
        if len(text) > SEG_MAXLEN:
            cut = text.rfind("。", 150, SEG_MAXLEN)
            text = text[:cut + 1] if cut > 0 else text[:SEG_MAXLEN] + "。"
        out.append({"no": i, "title": s["title"], "text": text})
    return out


def seg_style(i: int, n: int) -> tuple[str, str]:
    if i <= 2:
        return ("-5%", "+0Hz")
    if i >= n:
        return ("-6%", "-1Hz")
    return ("-3%", "+0Hz")


SAPI_PS1 = REPO / "scripts" / "sapi_tts.ps1"
SAPI_VOICE = "Microsoft Huihui Desktop"   # 离线 zh-CN 系统音色


def local_tts(segs: list[dict], workdir: Path, tag: str = "") -> int:
    """离线 Windows SAPI 合成（edge-tts 服务端 403 失效时的可靠替代）。
    产出 pNN.wav（16-bit PCM），ffmpeg 直接消费。"""
    workdir.mkdir(parents=True, exist_ok=True)
    n = 0
    for s in segs:
        i = s["no"]
        wav = workdir / f"p{i:02d}.wav"
        if wav.exists() and wav.stat().st_size > 8000:
            n += 1
            continue
        tf = workdir / f"_t{i:02d}.txt"
        tf.write_text(s["text"], encoding="utf-8")
        rate = -1 if i <= 2 else (-2 if i >= len(segs) else 0)
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", str(SAPI_PS1), "-TextFile", str(tf),
                            "-Out", str(wav), "-Voice", SAPI_VOICE, "-Rate", str(rate)],
                           capture_output=True, text=True, errors="ignore", timeout=180)
        if wav.exists() and wav.stat().st_size > 8000:
            n += 1
            print(f"   p{i:02d} {wav.stat().st_size // 1024}KB")
        else:
            print(f"   ❌ 段 {i} TTS 失败: {(r.stdout or '')[-100:]} {(r.stderr or '')[-100:]}")
    return n


def make_pages(segs, book, chap_title, workdir):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1920, 1080

    def wrap(d, text, font, max_w):
        lines, cur = [], ""
        for ch in text:
            if d.textlength(cur + ch, font=font) > max_w:
                lines.append(cur); cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
        return lines

    for s in segs:
        img = Image.new("RGB", (W, H), "#f7f4ea")
        d = ImageDraw.Draw(img)
        f_t = ImageFont.truetype(FB, 54)
        f_s = ImageFont.truetype(FONT, 36)
        f_k = ImageFont.truetype(FONT, 30)
        d.rectangle([0, 0, W, 14], fill="#1e8449")
        d.text((70, 46), f"{book}  |  {chap_title}", font=f_t, fill="#1e3b2a")
        d.line([70, 132, W - 70, 132], fill="#c9c2b2", width=2)
        d.text((72, 156), f"§{s['no']}  {s['title']}", font=f_s, fill="#b7950b")
        y = 236
        for ln in wrap(d, s["text"], f_k, W - 150)[:16]:
            d.text((80, y), ln, font=f_k, fill="#33332f")
            y += 50
            if y > 1016:
                break
        d.text((80, H - 58), "tcmP 中医药网络教育平台 · 学科教材授课", font=f_k, fill="#9a958a")
        img.save(workdir / f"p{s['no']:02d}.png")


def render(segs, workdir, out_mp4: Path) -> bool:
    seg_mp4s = []
    for s in segs:
        i = s["no"]
        mp3 = workdir / f"p{i:02d}.wav"
        png = workdir / f"p{i:02d}.png"
        seg = workdir / f"seg{i:02d}.mp4"
        if not mp3.exists() or mp3.stat().st_size < 8 * 1024:
            print(f"  ❌ 段 {i} 缺音频"); return False
        r = subprocess.run([FF, "-y", "-loop", "1", "-i", str(png), "-i", str(mp3),
                            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                            "-r", "24", "-c:a", "aac", "-b:a", "128k", "-shortest", str(seg)],
                           capture_output=True, text=True, errors="ignore", timeout=600)
        if not seg.exists() or seg.stat().st_size < 10 * 1024:
            print(f"  ❌ 段 {i} 合成失败: {r.stderr[-200:]}"); return False
        seg_mp4s.append(seg)
    lst = workdir / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in seg_mp4s), encoding="utf-8")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(out_mp4)], capture_output=True, text=True,
                   errors="ignore", timeout=600)
    ok = out_mp4.exists() and out_mp4.stat().st_size > 200 * 1024
    if ok:
        print(f"✅ 成片 {out_mp4.name} ({out_mp4.stat().st_size // 1024}KB)")
    else:
        print("❌ 拼接失败")
    return ok


# ── HTML 课件（轻量版）────────────────────────────────────────────
CSS = """
:root{--primary:#1e8449;--dark:#2c3e50;--gold:#b7950b;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:"Microsoft YaHei","SimHei",sans-serif;background:#f4f1ea;color:#2c3e50;}
.titlebar{background:linear-gradient(135deg,#1e8449,#145a32);color:#fff;text-align:center;padding:30px 18px;}
.titlebar h1{font-size:34px;letter-spacing:4px;}
.titlebar .sub{font-size:15px;opacity:.9;margin-top:8px;}
.container{max-width:1100px;margin:0 auto;padding:22px 18px 60px;}
.player{background:#000;border-radius:12px;overflow:hidden;margin-bottom:24px;box-shadow:0 10px 30px rgba(0,0,0,.3);}
video{width:100%;display:block;aspect-ratio:16/9;}
.sync-caption{background:#0d1b12;padding:12px 20px;min-height:84px;}
.cap-sec{color:#7ee2a8;font-size:14px;font-weight:700;margin-bottom:6px;}
.cap-text{color:#fdf9ef;font-size:16px;line-height:1.75;}
.cap-gone{opacity:.15;}
.sec{background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:18px;border:1px solid #e5e0d6;transition:opacity .6s,box-shadow .6s;}
.sec.now{box-shadow:0 0 0 3px var(--gold);}
.sec.done{opacity:.6;}
.sec-head{display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap;}
.sec-no{background:var(--primary);color:#fff;padding:4px 14px;border-radius:16px;font-size:13px;}
.sec h2{font-size:21px;}
.talk{font-size:16px;line-height:1.9;color:#3a3a3a;text-align:left;}
.footer{text-align:center;color:#999;font-size:13px;padding:18px;}
.breadcrumb{font-size:13px;color:#7a7a7a;margin-bottom:14px;}
.breadcrumb a{color:var(--primary);text-decoration:none;}
"""

JS_TMPL = """
const SUBS = @@SUBS@@;
const v = document.getElementById('v');
const capSec = document.getElementById('capSec');
const capText = document.getElementById('capText');
const SECS = document.querySelectorAll('.sec');
const LEAD = 1.6, DUR = 20;
const total = SUBS.length * DUR;
function setCap(s,on){
  capSec.classList.toggle('cap-gone',!on);
  capText.classList.toggle('cap-gone',!on);
  if(on&&s){capSec.textContent='\\u258d §'+s.no+' '+s.title;capText.textContent=s.text;}
}
function bridge(i){
  const prev=SUBS[i-1],next=SUBS[i];
  capSec.textContent='\\u258d 段间衔接';
  capText.textContent=prev?('…'+(prev.text.slice(-30))+'（下一段：'+(next?next.title:'')+'）'):'';
}
function mark(i){SECS.forEach(function(el,k){const n=k+1;el.classList.toggle('now',n===i);el.classList.toggle('done',n<i);});}
if(v){
 v.addEventListener('timeupdate',function(){
  const frac=(v.currentTime||0)/(v.duration||600);
  const t=frac*total;
  let i=Math.floor(t/DUR); if(i<0)i=0; if(i>=SUBS.length)i=SUBS.length-1;
  const start=i*DUR-LEAD, end=i*DUR+DUR+0.8;
  if(t>=start&&t<=end){setCap(SUBS[i],true);}else{bridge(Math.min(i+(t>end?1:0),SUBS.length-1));}
  mark(i);
 });
 v.muted=true; v.play().catch(function(){});
 const un=function(){v.muted=false;};
 document.addEventListener('click',un,{once:true});
 document.addEventListener('keydown',un,{once:true});
}
"""

CN = "一二三四五六七八九十"


def build_html(book, chap_title, segs, video_src, idx_href):
    secs = []
    for s in segs:
        n = CN[s["no"] - 1] if s["no"] <= 10 else str(s["no"])
        secs.append(f'''  <div class="sec" data-i="{s['no']}">
    <div class="sec-head"><span class="sec-no">第{n}段</span><h2>{s['title']}</h2></div>
    <div class="talk">{s['text']}</div>
  </div>''')
    subs = json.dumps([{"no": s["no"], "title": s["title"], "text": s["text"]} for s in segs], ensure_ascii=False)
    js = JS_TMPL.replace("@@SUBS@@", subs)
    title = f"{book} · {chap_title}"
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 视频课程</title>
<style>{CSS}</style></head>
<body>
<div class="titlebar"><h1>{title}</h1><div class="sub">tcmP 中医药网络教育平台 · 学科教材授课视频</div></div>
<div class="container">
  <div class="breadcrumb"><a href="{idx_href}">← 返回课程目录</a></div>
  <div class="player">
    <video id="v" controls autoplay muted playsinline preload="auto">
      <source src="{video_src}" type="video/mp4">
      您的浏览器不支持 HTML5 视频，请下载后观看：<a href="{video_src}">{video_src}</a>
    </video>
    <div class="sync-caption"><div class="cap-sec" id="capSec">▍ 第 1 段</div><div class="cap-text" id="capText"></div></div>
  </div>
{chr(10).join(secs)}
</div>
<div class="footer">{title} · 知识网络课程教学</div>
<script>{js}</script>
</body></html>
'''


def build_index(book, slug, chapters):
    rows = []
    for c in chapters:
        if c.get("html"):
            rows.append(f'    <li><a href="{c["file"]}">第{c["no"]:02d}章　{c["name"]}</a> '
                        f'<span class="meta">{c.get("segs",0)} 段 · {c.get("size_kb",0)} KB</span></li>')
        else:
            rows.append(f'    <li class="todo">第{c["no"]:02d}章　{c["name"]} <span class="meta">待生成</span></li>')
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{book} · 视频课程</title><style>
body{{font-family:"Microsoft YaHei","SimHei",sans-serif;background:#f4f1ea;color:#2c3e50;margin:0;}}
.titlebar{{background:linear-gradient(135deg,#1e8449,#145a32);color:#fff;text-align:center;padding:44px 18px;}}
.titlebar h1{{font-size:38px;letter-spacing:5px;}} .titlebar .sub{{margin-top:10px;opacity:.92;}}
.container{{max-width:960px;margin:0 auto;padding:26px 18px 70px;}}
ul{{list-style:none;}} li{{background:#fff;border:1px solid #e5e0d6;border-radius:10px;margin-bottom:12px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;}}
li a{{color:#1e8449;text-decoration:none;font-size:18px;}} li.todo{{color:#9a958a;}}
.meta{{color:#9a958a;font-size:13px;}}
.footer{{text-align:center;color:#999;font-size:13px;padding:20px;}}
</style></head><body>
<div class="titlebar"><h1>{book}</h1><div class="sub">tcmP 中医药网络教育平台 · 学科教材授课视频课程</div></div>
<div class="container"><ul>
{chr(10).join(rows)}
</ul></div>
<div class="footer">{book} · 视频课程 · tcmP</div>
</body></html>
'''


def chapter_sheets(xlsx: Path) -> list[tuple[int, str, str]]:
    """返回 [(章号, sheet名, 章名)]，按章号排序；只取正文章（排除 0* 前置与附件 sheet）"""
    wb = openpyxl.load_workbook(str(xlsx), read_only=True, data_only=True)
    names = wb.sheetnames
    wb.close()
    out = []
    for sn in names:
        if sn.startswith("0"):
            continue
        if sn in ("ICD11统一命名", "病证单元库", "多智能体协同", "兼容性思维流",
                  "可复用Skills", "平台建设与依赖"):
            continue
        m = re.match(r"^(\d+)(.*)$", sn)
        if not m:
            continue
        no = int(m.group(1))
        out.append((no, sn, sn))
    out.sort(key=lambda x: x[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--parse-only", action="store_true")
    args = ap.parse_args()

    xlsx = Path(args.book)
    bookdir = DOCS / args.slug
    bookdir.mkdir(parents=True, exist_ok=True)
    chapters = chapter_sheets(xlsx)

    # 已存在的 manifest（增量）
    manifest_p = bookdir / f"{args.slug}-course.json"
    manifest = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.exists() else \
        {"book": args.name, "slug": args.slug, "source": xlsx.name, "chapters": []}
    done = {c["no"]: c for c in manifest["chapters"]}

    todo = chapters if args.all else [c for c in chapters if c[0] == args.chapter]
    if not todo:
        print(f"无待处理章（book={args.book} chapter={args.chapter}）"); return

    for no, sheet, name in todo:
        print(f"\n######## 第{no:02d}章 {sheet} ########")
        segs = parse_chapter(xlsx, sheet)
        print(f"  解析段落 {len(segs)} 段")
        for s in segs:
            print(f"   §{s['no']:02d} {s['title'][:36]:<36} ({len(s['text'])}字)")
        if args.parse_only:
            continue

        tag = f"{args.slug}_ch{no:02d}"
        workdir = bookdir / f"ch{no:02d}"
        print("  → 离线 SAPI TTS ...")
        ntts = local_tts(segs, workdir, tag)
        print(f"  TTS {ntts}/{len(segs)}")
        make_pages(segs, args.name, name, workdir)
        mp4 = bookdir / f"第{no:02d}章-{name}.mp4"
        if not render(segs, workdir, mp4):
            continue
        html_p = bookdir / f"第{no:02d}章-{name}-视频课程.html"
        html_p.write_text(build_html(args.name, f"第{no:02d}章 {name}", segs, mp4.name, "index.html"),
                          encoding="utf-8")
        done[no] = {"no": no, "name": name, "file": html_p.name, "video": mp4.name,
                    "segs": len(segs), "size_kb": mp4.stat().st_size // 1024, "html": True}
        print(f"  ✅ 课件 {html_p.name}")

    # 更新 manifest + 索引（保留未生成章占位）
    allch = []
    for no, sheet, name in chapters:
        if no in done and done[no].get("html"):
            allch.append(done[no])
        else:
            allch.append({"no": no, "name": name, "html": False})
    manifest["chapters"] = allch
    manifest_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    (bookdir / "index.html").write_text(build_index(args.name, args.slug, allch), encoding="utf-8")
    print(f"\n✅ 课程索引: {bookdir / 'index.html'}（已生成 {sum(1 for c in allch if c.get('html'))}/{len(allch)} 章）")


if __name__ == "__main__":
    main()
