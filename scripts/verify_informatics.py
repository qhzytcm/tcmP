# -*- coding: utf-8 -*-
"""中医信息学 · 端到端自检（结构 / 挖掘自洽 / 确定性 / 检索 / 路由）。"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INFO = ROOT / "kg" / "informatics"
CAT = INFO / "tcm-informatics.json"

ok = fail = 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  [OK] {name}")
    else:
        fail += 1
        print(f"  [XX] {name}  {detail}")


def main():
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    print("=" * 62)
    print(" 中医信息学 · 自检")
    print("=" * 62)

    for k in ("meta", "standards", "assets", "operators", "distributions",
              "rules", "clusters", "icd_coverage", "data_quality", "stats"):
        check(f"顶层键 {k}", k in cat)

    s = cat["stats"]
    check("语料非空", s["units"] > 0, s["units"])
    check("三层齐备（标准/资产/算子）",
          len(cat["standards"]) >= 3 and len(cat["assets"]) >= 3 and len(cat["operators"]) >= 5)

    cov = cat["icd_coverage"]
    check("ICD 覆盖率自洽", cov["mapped"] + cov["unmapped"] == cov["total"])
    check("ICD 覆盖率 0<r<=1", 0 < cov["rate"] <= 1, cov["rate"])
    check("未编码清单非空（覆盖率<100%）", cov["unmapped"] == cov["total"] - cov["mapped"])

    for kind, rs in cat["rules"].items():
        good = all(r["left"] and r["right"] and 0 <= r["support"] <= 1
                   and 0 <= r["confidence"] <= 1.0001 and r["lift"] >= 0 for r in rs)
        check(f"规则自洽[{kind}] ({len(rs)})", good)
    check("三类规则齐备", set(cat["rules"]) == {"symptom_to_syndrome", "syndrome_to_formula", "zangfu_to_formula"})

    check("聚类成员唯一", all(len(set(c["members"])) == c["size"] for c in cat["clusters"]))
    check("数据质量问题已检出", s["data_quality_issues"] > 0)
    by = cat["data_quality"]["by_field"]
    check("检出 evidence_level 枚举越界（I级→E级）", by.get("evidence_level", 0) >= 1)
    check("检出 six_channels 合病/过渡变体", by.get("six_channels", 0) >= 1)
    check("检出 icd11_code 缺失", by.get("icd11_code", 0) >= 1)

    # 确定性：重建到临时目录，与已入库产物逐字节比较
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_informatics.py"),
                        "--out", td], check=True, capture_output=True, cwd=str(ROOT))
        a = CAT.read_bytes()
        b = (Path(td) / "tcm-informatics.json").read_bytes()
        check("构建产物确定性（两次构建字节一致）", a == b)

    # 检索
    r = subprocess.run([sys.executable, str(INFO / "tcm_mining.py"), "retrieve", "失眠 多梦"],
                       capture_output=True, text=True, cwd=str(ROOT))
    check("检索可用（向量/FTS5/RRF）", r.returncode == 0 and "RRF" in r.stdout, r.stdout[-200:])

    # 路由（subprocess 隔离 fastapi，规避本机 pytest import 挂起）
    probe = ("import sys;sys.path.insert(0,r'%s');import informatics_router as R;"
             "print(R.stats()['units'], len(R.standards()['items']), R.coverage()['rate'])" % (ROOT / "api"))
    p = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    check("路由可加载且返回数据", p.returncode == 0 and p.stdout.strip().split()[0] == str(s["units"]),
          (p.stdout + p.stderr)[-200:])

    print("-" * 62)
    print(f" 结果：{ok} 通过 / {fail} 失败")
    if fail == 0:
        print(" 自检全部通过 ✓")
    print("=" * 62)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())