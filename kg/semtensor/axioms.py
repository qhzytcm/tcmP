# -*- coding: utf-8 -*-
"""tcmP 语义张量 · 颜色公理与球面变换（单一来源）
对标标准：tcmP-三维极坐标语义张量-可视化标准 v1.0
本模块是标准的**代码本体**：轴端色表、颜色合成公理、球面↔笛卡尔变换、镜像算子。
"""
from __future__ import annotations
import math

VERSION = "1.0"

# ── 可见光谱端色基准（波长序段中位数 nm → 中位能容 eV）──
WAVELENGTH_NM = {"红": 685, "橙": 605, "黄": 578, "绿": 533, "青": 493, "蓝": 458, "紫": 415}
EV_CENTER = {"红": 1.81, "橙": 2.05, "黄": 2.15, "绿": 2.33, "青": 2.52, "蓝": 2.65, "紫": 2.99}
HEX = {"红": "#DB1C1C", "橙": "#FF8C00", "黄": "#F2C200", "绿": "#00B050",
       "青": "#00C7C7", "蓝": "#1F61D9", "紫": "#8A2BE2"}


def hex2rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(c):
    return "#" + "".join("%02X" % max(0, min(255, round(v * 255))) for v in c)


RGB = {k: hex2rgb(v) for k, v in HEX.items()}
C_O = RGB["绿"]                       # O 点基准色 = 绿 #00B050 ≈ (0.000, 0.690, 0.314)
C_O_HEX = HEX["绿"]

# ── 轴端色表（I / O / T），三球（母/子/父）共用同一张表 ──
AXIS_END_COLOR = {"X": ("橙", "绿", "紫"), "Y": ("蓝", "绿", "红"), "Z": ("黄", "绿", "青")}
AXIS_SEMANTICS = {"X": ("阴", "中（阴阳平和）", "阳"),
                  "Y": ("表", "半表半里", "里"),
                  "Z": ("精（形质）", "气（能量）", "神（神志情志）")}
AXIS_NAME = {"X": "阴阳轴（左右）", "Y": "表里轴（前后）", "Z": "精气神轴（足→首）"}

# ── 三球镜像算子（表5）──
MIRROR = {"母": (-1, -1, +1), "子": (+1, +1, +1), "父": (+1, +1, +1)}
SEX = {"母": "女", "子": "男", "父": "男"}
AXIS_FACE_DEG = {"母": (180, 135, 90), "子": (0, 45, 90), "父": (0, 45, 90)}
XY_FACE = {"母": 3 * math.pi / 4, "子": math.pi / 4, "父": math.pi / 4}


def ramp(t: float, axis: str):
    """单轴渐变：在 [−1, 0, +1] 三端色间逐通道线性插值。t 可为标量或序列。"""
    cmap = [RGB[c] for c in AXIS_END_COLOR[axis]]
    if hasattr(t, "__len__"):
        return [ramp(x, axis) for x in t]
    t = max(-1.0, min(1.0, float(t)))
    i, j = (0, 1) if t <= 0 else (1, 2)
    a = (t + 1) if t <= 0 else t
    return tuple(cmap[i][k] + (cmap[j][k] - cmap[i][k]) * a for k in range(3))


def comp(x: float, y: float, z: float):
    """颜色公理：w_i = clip(|v_i|,0,1)；k = max(w_i)；C = (1−k)·绿 + k·(Σw_i·c_i/Σw_i)。"""
    v = (x, y, z)
    w = [min(1.0, abs(t)) for t in v]
    k = max(w)
    if k <= 0:
        return C_O
    ends = [RGB[AXIS_END_COLOR[ax][2 if t > 0 else 0]] for ax, t in zip("XYZ", v)]
    num = [sum(w[i] * ends[i][ch] for i in range(3)) for ch in range(3)]
    den = sum(w) or 1.0
    mix = [n / den for n in num]
    return tuple(C_O[ch] * (1 - k) + mix[ch] * k for ch in range(3))


def sph2cart(r: float, theta_deg: float, phi_deg: float):
    """X = r·cosθ·cosφ ； Y = r·cosθ·sinφ ； Z = r·sinθ（θ=仰角，赤道 0）。"""
    th, ph = math.radians(theta_deg), math.radians(phi_deg)
    return (r * math.cos(th) * math.cos(ph), r * math.cos(th) * math.sin(ph), r * math.sin(th))


def cart2sph(X: float, Y: float, Z: float):
    """r = |v| ； θ = arcsin(Z/r) ； φ = atan2(Y, X)（φ 归一到 [0,360)）。"""
    r = math.sqrt(X * X + Y * Y + Z * Z)
    if r == 0:
        return (0.0, 0.0, 0.0)
    th = math.degrees(math.asin(max(-1.0, min(1.0, Z / r))))
    ph = math.degrees(math.atan2(Y, X)) % 360.0
    return (r, th, ph)


def mirror_point(n, ball="子"):
    """几何位置 = M(sex)·n̂；取色坐标 = M(sex)·(M(sex)·n̂) = n̂（反镜像补偿 ⇒ 三球同色）。"""
    sx, sy, sz = MIRROR[ball]
    return (sx * n[0], sy * n[1], sz * n[2])


def fingerprint() -> dict:
    """公理指纹：跨环境校验一致（st_meta 固化）。"""
    return dict(version=VERSION, coordinate="X=r·cosθ·cosφ; Y=r·cosθ·sinφ; Z=r·sinθ",
                theta_range=[-90, 90], phi_range=[0, 360], r_range=[0.0, 1.0],
                axis_end_color=AXIS_END_COLOR, axis_semantics=AXIS_SEMANTICS,
                C_O=C_O_HEX, wavelength_nm=WAVELENGTH_NM, ev_center=EV_CENTER,
                mirror=MIRROR, xy_face=XY_FACE)