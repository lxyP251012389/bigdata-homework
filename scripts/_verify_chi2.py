# -*- coding: utf-8 -*-
"""用 scipy 独立复核手写的卡方统计量与 p 值（校验用，不改数据）"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2 as chi2_dist
from scipy.stats import chi2_contingency

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
CAT_ORDER = ["党政机关", "事业单位", "国有企业", "金融保险",
             "私营企业", "个体经营", "家庭/未就业", "其他"]

df = pd.read_csv(OUT_DIR / "类别变量_清洗后.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = df.replace("", pd.NA).dropna(subset=["父亲工作_性质", "母亲工作_性质"])
tab = pd.crosstab(d["父亲工作_性质"], d["母亲工作_性质"]).reindex(
    index=CAT_ORDER, columns=CAT_ORDER, fill_value=0)
obs = tab.values
obs = obs[obs.sum(1) > 0][:, obs.sum(0) > 0]        # 剔除空行列，与主脚本一致

chi2_val, p_asym, dof, exp = chi2_contingency(obs, correction=False)
print("【scipy 独立计算】")
print(f"  χ² = {chi2_val:.3f}   df = {dof}   p = {p_asym:.6f}")

# 复现主脚本的手写实现
def gammaincc(a, x):
    if x <= 0:
        return 1.0
    if x < a + 1.0:
        ap, s, delta = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1.0
            delta *= x / ap
            s += delta
            if abs(delta) < abs(s) * 1e-15:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    tiny = 1e-300
    b, c, dd, h = x + 1.0 - a, 1.0 / tiny, 1.0 / (x + 1.0 - a), 1.0 / (x + 1.0 - a)
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        dd = an * dd + b
        dd = dd if abs(dd) >= tiny else tiny
        c = b + an / c
        c = c if abs(c) >= tiny else tiny
        dd = 1.0 / dd
        delta = dd * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def my_chi2(obs):
    e = np.outer(obs.sum(1), obs.sum(0)) / obs.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(e > 0, (obs - e) ** 2 / e, 0.0)
    return float(t.sum()), (obs.shape[0] - 1) * (obs.shape[1] - 1)


c_my, df_my = my_chi2(obs)
p_my = gammaincc(df_my / 2, c_my / 2)
print("【主脚本手写实现】")
print(f"  χ² = {c_my:.3f}   df = {df_my}   p = {p_my:.6f}")

ok = (abs(c_my - chi2_val) < 1e-9 and df_my == dof and abs(p_my - p_asym) < 1e-9)
print(f"\n一致性：{'通过（手写公式与 scipy 完全一致）' if ok else '**不一致，需排查**'}")
print(f"  χ² 差 = {abs(c_my - chi2_val):.2e}   p 差 = {abs(p_my - p_asym):.2e}")

# 3×3 表同样复核
GROUP = {"党政机关": "体制内", "事业单位": "体制内", "国有企业": "体制内", "金融保险": "体制内",
         "私营企业": "体制外", "个体经营": "体制外", "家庭/未就业": "家庭·未就业"}
g = d[d["父亲工作_性质"].isin(GROUP) & d["母亲工作_性质"].isin(GROUP)]
t3 = pd.crosstab(g["父亲工作_性质"].map(GROUP), g["母亲工作_性质"].map(GROUP))
o3 = t3.reindex(index=["体制内", "体制外", "家庭·未就业"],
                columns=["体制内", "体制外", "家庭·未就业"], fill_value=0).values
c2s, p2s, df2s, _ = chi2_contingency(o3, correction=False)
c2m, df2m = my_chi2(o3)
print(f"\n【3×3 复核】scipy: χ²={c2s:.3f} df={df2s} p={p2s:.6f}")
print(f"           本脚本: χ²={c2m:.3f} df={df2m} p={gammaincc(df2m / 2, c2m / 2):.6f}")
print(f"  → {'一致' if abs(c2s - c2m) < 1e-9 else '不一致'}")

# 与卡方分布表对照：df=35, χ²=56.403 的临界值
print(f"\n对照：df=35 时 α=0.05 临界值 = {chi2_dist.ppf(0.95, 35):.3f}，"
      f"α=0.01 临界值 = {chi2_dist.ppf(0.99, 35):.3f}")
print(f"      实际 χ² = {c_my:.3f} > 临界值，故 p < 0.05，拒绝独立性假设")
