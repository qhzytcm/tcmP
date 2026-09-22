# -*- coding: utf-8 -*-
"""
constitution —— 体质层：阴阳二十五人 参数化生成式模型（tcmP 体质分类模块）
=======================================================================
依据《灵枢·阴阳二十五人》(LS64) + 《灵枢·五音五味》(LS65) + 《素问·上古天真论》(SW01)，
把"五五二十五人"体质分类形式化为参数化生成式模型，与 etiology（病因层）正交耦合。

  ├── 五形 × 五亚型 = 25 型（木/火/土/金/水 × 五音五种变异）
  ├── 参数空间 B = (五形, 五音, 五色, 经络, V_气, V_血, 须髯, 时令)
  ├── 统一标尺：5 区间 L1-L5 + 高斯归一化 g(x)=exp(-(x-μ)²/2σ²) σ=0.42
  └── 性别参数：男（血气均衡·须髯俱备·男八） vs 女（气余血少·无须·女七）

快速开始：
    from constitution.model import ConstitutionModel
    m = ConstitutionModel()
    print(m.generate('木', '上角', sex='female'))
    print(m.report_gender())          # 男女分类参数同异对照表

并列第二分类轴：阴阳之人（太阴/少阴/太阳/少阳/阴阳和平，见《灵枢·通天》LS72）。
"""
from constitution.model import ConstitutionModel  # noqa: F401
from constitution import framework  # noqa: F401

__version__ = '0.1.0'
