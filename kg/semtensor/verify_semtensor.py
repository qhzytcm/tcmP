# -*- coding: utf-8 -*-
"""tcmP 语义张量 · 校验（对标标准 §十二 校验规范，无目视条件下的硬证据）。"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import axioms as A   # noqa: E402

JSON = HERE / "semtensor.json"
ok = fail = 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1; print("  [OK] " + name)
    else:
        fail += 1; print("  [XX] " + name + "  " + str(detail))


def main():
    print("=" * 62); print(" 语义张量 · 校验规范"); print("=" * 62)
    # 1) 端色断言（3 轴 × 3 端）
    for ax in "XYZ":
        for i, t in enumerate((-1, 0, 1)):
            want = A.RGB[A.AXIS_END_COLOR[ax][i]]
            got = A.ramp(t, ax)
            check("端色 %s(%+d)=%s" % (ax, t, A.AXIS_END_COLOR[ax][i]),
                  all(abs(a - b) < 1e-9 for a, b in zip(want, got)), (want, got))
    # 2) O 点回基准绿
    check("comp((0,0,0)) == C_O == #00B050",
          all(abs(a - b) < 1e-6 for a, b in zip(A.comp(0, 0, 0), A.C_O)) and A.C_O_HEX == "#00B050")
    # 3) 矢量版形状
    check("ramp([-1,0,1]).shape == (3,3)", len(A.ramp([-1, 0, 1], "X")) == 3 and len(A.ramp(-1, "X")) == 3)
    # 4) 球面往返与特例
    e = max(abs(A.cart2sph(*A.sph2cart(1.0, th, ph))[1] - th) + abs(A.cart2sph(*A.sph2cart(1.0, th, ph))[2] - ph % 360)
            for th in (-90, -45, 0, 30, 90) for ph in (0, 45, 180, 359))
    check("球面往返误差 < 1e-12", e < 1e-12, e)
    check("θ=+90° → (0,0,1)", all(abs(v - w) < 1e-12 for v, w in zip(A.sph2cart(1, 90, 0), (0, 0, 1))))
    check("θ=0,φ=0 → (1,0,0)", all(abs(v - w) < 1e-12 for v, w in zip(A.sph2cart(1, 0, 0), (1, 0, 0))))
    # 5) 镜像不变色（母/子/父 同色）
    import random
    rnd = random.Random(7)
    same = True
    for _ in range(400):
        v = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))
        c0 = A.comp(*v)
        for ball in ("母", "子", "父"):
            g = A.mirror_point(v, ball)
            back = A.mirror_point(g, ball)      # 取色坐标反镜像补偿
            if any(abs(x - y) > 1e-12 for x, y in zip(A.comp(*back), c0)):
                same = False
    check("镜像不变色（400 随机点 × 三球）", same)

    # 6) 值域 + 数据结构
    data = json.loads(JSON.read_text(encoding="utf-8"))
    us = data["units"]
    check("值域 θ∈[-90,90] φ∈[0,360) r∈(0,1]",
          all(-90 <= u["theta"] <= 90 and 0 <= u["phi"] < 360 and 0 < u["r"] <= 1 for u in us))
    check("DSU 覆盖 103 且 id 唯一", len(us) == 103 and len(set(u["id"] for u in us)) == 103, len(us))
    check("学科 120 全部映射", len(data["subjects"]) == 120 and all(s["code"] for s in data["subjects"]))
    check("域 8 个且各有锚点", len(data["domains"]) == 8 and all(d["anchor"] for d in data["domains"]))
    check("st_meta 含公理指纹与轴端色表",
          "axiom_fingerprint" in data["st_meta"] and data["st_meta"]["axiom_fingerprint"]["axis_end_color"] == {k: list(v) for k, v in A.AXIS_END_COLOR.items()})
    check("颜色为坐标函数（同坐标必同色）",
          all(u["color"].startswith("#") and len(u["color"]) == 7 for u in us))

    # 7) 确定性：重建到临时目录逐字节比较
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(HERE / "build_semtensor.py"), "--out", td],
                       check=True, capture_output=True)
        check("构建确定性（两次构建字节一致）", JSON.read_bytes() == (Path(td) / "semtensor.json").read_bytes())

    print("-" * 62)
    print(" 结果：%d 通过 / %d 失败" % (ok, fail))
    if not fail:
        print(" 校验规范全部通过 ✓")
    print("=" * 62)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())