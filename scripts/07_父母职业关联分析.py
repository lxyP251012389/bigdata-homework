# -*- coding: utf-8 -*-
"""
《大数据与人工智能》作业：父母职业（单位性质）之间是否存在关联
方法：列联表 + 卡方独立性检验 + Cramér's V + 置换检验（应对小样本稀疏）
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent       # 仓库根目录
OUT_DIR = ROOT / "output"                            # 与 06 脚本共用的输出目录
if not (OUT_DIR / "类别变量_清洗后.csv").exists():
    raise SystemExit("找不到 output/类别变量_清洗后.csv，请先运行 scripts/06_类别变量清洗.py")
CAT_ORDER = ["党政机关", "事业单位", "国有企业", "金融保险",
             "私营企业", "个体经营", "家庭/未就业", "其他"]

df = pd.read_csv(OUT_DIR / "类别变量_清洗后.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
df = df.replace("", pd.NA)

# 分析前剔除母亲未填写的 1 行（缺失无法参与配对比较）
n_all = len(df)
d = df.dropna(subset=["父亲工作_性质", "母亲工作_性质"]).copy()
n = len(d)
print(f"[样本] 总记录 {n_all} 行，剔除母亲未填写 1 行后参与配对分析 n = {n}")

# ============================================================ 工具函数
def gammaincc(a: float, x: float) -> float:
    """正则化上不完全伽马函数 Q(a,x)，用于手算卡方分布 p 值（Numerical Recipes）"""
    if x <= 0:
        return 1.0
    if x < a + 1.0:                      # 级数展开算 P，再取 1-P
        ap, s, delta = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1.0
            delta *= x / ap
            s += delta
            if abs(delta) < abs(s) * 1e-15:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    tiny = 1e-300                        # 连分数算 Q
    b, c, dd, h = x + 1.0 - a, 1.0 / tiny, 1.0 / (x + 1.0 - a), 1.0 / (x + 1.0 - a)
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        dd = an * dd + b
        if abs(dd) < tiny:
            dd = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        delta = dd * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(x: float, k: int) -> float:
    return gammaincc(k / 2.0, x / 2.0)


def cramers_v(obs: np.ndarray, chi2: float) -> float:
    n = obs.sum()
    r, c = obs.shape
    return math.sqrt(chi2 / (n * (min(r, c) - 1))) if n and min(r, c) > 1 else float("nan")


def chi2_stat(obs: np.ndarray):
    """返回 (卡方值, 自由度, 期望频数矩阵)"""
    exp = np.outer(obs.sum(1), obs.sum(0)) / obs.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        term = np.where(exp > 0, (obs - exp) ** 2 / exp, 0.0)
    dfree = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    return float(term.sum()), dfree, exp


def permutation_p(obs: np.ndarray, chi2_obs: float, n_perm: int = 20000, seed: int = 42):
    """打乱其中一列，构造卡方统计量的零分布，得到不受稀疏影响的 p 值"""
    rng = np.random.default_rng(seed)
    y = np.repeat(np.arange(obs.shape[1]), obs.sum(0))
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(y)
        tab = np.zeros_like(obs)
        np.add.at(tab, (np.repeat(np.arange(obs.shape[0]), obs.sum(1)), y), 1)
        c, _, _ = chi2_stat(tab)
        if c >= chi2_obs - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def report(title, obs, cats_r, cats_c):
    obs = np.asarray(obs)
    # 剔除全零行/列：空行空列不贡献卡方值，却会让自由度虚高、p 值偏大
    keep_r, keep_c = obs.sum(1) > 0, obs.sum(0) > 0
    if not keep_r.all() or not keep_c.all():
        dropped = [cats_r[i] for i in range(len(cats_r)) if not keep_r[i]]
        dropped += [cats_c[j] for j in range(len(cats_c)) if not keep_c[j]]
        print(f"  · 剔除全零行/列（该样本中无人属于）：{dropped}")
        print(f"  · 剔除后表尺寸 {keep_r.sum()}×{keep_c.sum()}，自由度相应减少")
    obs = obs[np.ix_(keep_r, keep_c)]
    chi2, dfree, exp = chi2_stat(obs)
    p_asym = chi2_sf(chi2, dfree)
    v = cramers_v(obs, chi2)
    small = float((exp < 5).mean())
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")
    print(f"卡方值 χ² = {chi2:.3f}   自由度 df = {dfree}   有效 n = {int(obs.sum())}")
    print(f"渐近 p 值  = {p_asym:.4f}")
    print(f"Cramér's V = {v:.3f}   （0=完全无关，1=完全相关；0.1 弱 / 0.3 中 / 0.5 强）")
    print(f"期望频数 <5 的格子占比 = {small:.0%}"
          f"  {'→ 卡方近似不可靠，需看置换检验' if small > 0.2 else '→ 卡方近似可用'}")
    p_perm = permutation_p(obs, chi2)
    print(f"置换检验 p = {p_perm:.4f}   （打乱 20000 次，不依赖期望频数假设，小样本下更可信）")
    return chi2, dfree, p_asym, v, p_perm


# ============================================================ 分析一：8×8 完整列联表
print("\n【分析一】父亲单位性质 × 母亲单位性质（8 类完整表，含「其他」）")
tab8 = pd.crosstab(d["父亲工作_性质"], d["母亲工作_性质"]).reindex(
    index=CAT_ORDER, columns=CAT_ORDER, fill_value=0)
print("\n实际频数：")
print(tab8.to_string())
r1 = report("8×8 列联表独立性检验", tab8.values, CAT_ORDER, CAT_ORDER)

# ============================================================ 分析二：合并为三类的 3×3 表
# 体制内 / 体制外 / 家庭·未就业。「其他」只有 1 例（社区），剔除以免把 1 例当一类
GROUP = {
    "党政机关": "体制内", "事业单位": "体制内", "国有企业": "体制内", "金融保险": "体制内",
    "私营企业": "体制外", "个体经营": "体制外",
    "家庭/未就业": "家庭·未就业",
}
g = d[d["父亲工作_性质"].isin(GROUP) & d["母亲工作_性质"].isin(GROUP)].copy()
g["父亲组"] = g["父亲工作_性质"].map(GROUP)
g["母亲组"] = g["母亲工作_性质"].map(GROUP)
order3 = ["体制内", "体制外", "家庭·未就业"]
tab3 = pd.crosstab(g["父亲组"], g["母亲组"]).reindex(index=order3, columns=order3, fill_value=0)
print("\n\n【分析二】合并为 3 类（体制内 / 体制外 / 家庭·未就业）")
print(f"（剔除「其他」1 例，n = {len(g)}）")
print("\n实际频数：")
print(tab3.to_string())
r2 = report("3×3 列联表独立性检验", tab3.values, order3, order3)

# ============================================================ 分析三：对角线（父母同类）
print("\n\n【分析三】父母是否「同类」——最直观的关联证据")
same = int(np.trace(tab3.values))
tot = int(tab3.values.sum())
exp_same = float((tab3.values.sum(1) * tab3.values.sum(0) / tot ** 2).sum() * tot)
print(f"实际父母同类 {same}/{tot} = {same / tot:.1%}")
print(f"若完全独立，期望同类约 {exp_same:.1f}/{tot} = {exp_same / tot:.1%}")
print(f"差值 {same / tot - exp_same / tot:+.1%}"
      f"  → {'高于独立假设，存在聚集倾向' if same > exp_same else '不高于独立假设，未见聚集'}")
print("\n对角线逐类：")
for c in order3:
    act = int(tab3.loc[c, c])
    row_n = int(tab3.loc[c].sum())
    exp = tab3.loc[c].sum() * tab3[c].sum() / tot
    print(f"  {c:<8} 同类 {act:>2} 人 / 该行 {row_n:>2} 人（{act / row_n:>4.0%}）  独立期望 {exp:>4.1f} 人")

# ============================================================ 分析四：条件分布
print("\n\n【分析四】给定父亲的职业，母亲的职业分布（行百分比）")
pct_row = (tab3.div(tab3.sum(1), axis=0) * 100).round(1)
print(pct_row.to_string())
print("\n【分析四补】给定母亲的职业，父亲的职业分布（列百分比）")
pct_col = (tab3.div(tab3.sum(0), axis=1) * 100).round(1)
print(pct_col.to_string())

print("\n母亲「家庭·未就业」12 人的父亲职业构成：")
sub = d[d["母亲工作_性质"] == "家庭/未就业"]["父亲工作_性质"].value_counts()
print(sub.to_string())

print("\n父亲为党政机关的 21 人，母亲职业构成：")
sub2 = d[d["父亲工作_性质"] == "党政机关"]["母亲工作_性质"].value_counts()
print(sub2.to_string())
print("（其中「体制内」占 "
      f"{sub2.reindex([c for c in sub2.index if GROUP.get(c) == '体制内']).sum() / sub2.sum():.0%}，"
      "体制外占 "
      f"{sub2.reindex([c for c in sub2.index if GROUP.get(c) == '体制外']).sum() / sub2.sum():.0%}）")

# ============================================================ 分析五：谁撑起了这个关联
print("\n\n【分析五】单元格贡献与调整标准化残差（3×3 表，n=51）")
# 调整标准化残差：|值|>2 说明该格显著偏离「独立」时的期望，是关联的实际来源
N = tab3.values.sum()
exp3 = np.outer(tab3.sum(1), tab3.sum(0)) / N
contrib = (tab3.values - exp3) ** 2 / exp3
denom = np.sqrt(exp3 * np.outer(1 - tab3.sum(1) / N, 1 - tab3.sum(0) / N))
adj = (tab3.values - exp3) / denom
contrib_df = pd.DataFrame(contrib / chi2_stat(tab3.values)[0] * 100,
                          index=order3, columns=order3).round(1)
adj_df = pd.DataFrame(adj, index=order3, columns=order3).round(2)
print("\n各格对 χ² 的贡献占比（%）：")
print(contrib_df.to_string())
print("\n调整标准化残差（|>2 视为显著偏离）：")
print(adj_df.to_string())
print("\n偏离最大的格子：")
flat = [(order3[i], order3[j], tab3.values[i, j], exp3[i, j], adj[i, j],
         contrib[i, j] / chi2_stat(tab3.values)[0] * 100)
        for i in range(3) for j in range(3)]
for fr, mr, o, e, a, c in sorted(flat, key=lambda x: -abs(x[4]))[:4]:
    tag = "偏多" if o > e else "偏少"
    print(f"  父亲{fr} × 母亲{mr}：实际 {o} 人，期望 {e:.1f} 人 → {tag}，"
          f"调整残差 {a:+.2f}，贡献 {c:.0f}% 的 χ²")

# ============================================================ 分析六：母亲是否就业
print("\n\n【分析六】父亲是否体制内 × 母亲是否就业")
# 只比较父亲有工作的家庭：父亲的「家庭·未就业」只有 3 人，
# 既不属于体制内也不属于体制外，强行并入任一组都会扭曲结论
wf = g[g["父亲组"] != "家庭·未就业"].copy()
wf["母亲就业"] = np.where(wf["母亲组"] == "家庭·未就业", "不就业", "就业")
t22 = pd.crosstab(wf["父亲组"], wf["母亲就业"]).reindex(
    index=["体制内", "体制外"], columns=["就业", "不就业"], fill_value=0)
print(f"（只取父亲有工作的 {len(wf)} 户）")
print(t22.to_string())
a = int(t22.loc["体制内", "就业"])
b = int(t22.loc["体制内", "不就业"])
c_ = int(t22.loc["体制外", "就业"])
dd = int(t22.loc["体制外", "不就业"])
odds_in, odds_out = b / a, dd / c_
print(f"\n母亲不就业比例：父亲体制内 {b}/{a + b} = {b / (a + b):.1%}；"
      f"父亲体制外 {dd}/{c_ + dd} = {dd / (c_ + dd):.1%}")
print(f"不就业几率(odds)：体制内 {odds_in:.3f}  体制外 {odds_out:.3f}")
orr = odds_out / odds_in
print(f"优势比 OR = {orr:.2f}  → 父亲在体制外时，母亲不就业的几率是体制内的 {orr:.1f} 倍")
from scipy.stats import fisher_exact

_, p_fisher = fisher_exact([[c_, dd], [a, b]])   # 2×2 且有 2 人的小格，用精确检验
print(f"Fisher 精确检验 p = {p_fisher:.4f}")

# 敏感性检查：把父亲未就业的 3 户也并进「体制外」会怎样
gan = g.copy()
gan["父亲二组"] = np.where(gan["父亲组"] == "体制内", "体制内", "体制外（含家庭）")
gan["母亲就业"] = np.where(gan["母亲组"] == "家庭·未就业", "不就业", "就业")
t2b = pd.crosstab(gan["父亲二组"], gan["母亲就业"])
_, p2b = fisher_exact(t2b.values[:, ::-1])
orr2 = (t2b.loc["体制外（含家庭）", "不就业"] / t2b.loc["体制外（含家庭）", "就业"]) / \
       (t2b.loc["体制内", "不就业"] / t2b.loc["体制内", "就业"])
print(f"敏感性检查（并入父亲未就业 3 户，n={len(gan)}）：OR = {orr2:.2f}，Fisher p = {p2b:.4f}"
      f"  → 结论{'不变' if p2b < 0.05 else '改变，需谨慎'}")

# ============================================================ 分析七：同一单位/都不工作
print("\n\n【分析七】父母「完全同类」的极端个案（原文层面）")
same_unit = d[d["父亲工作"] == d["母亲工作"]]
shop = same_unit[~same_unit["父亲工作"].str.contains("家庭")]
none = same_unit[same_unit["父亲工作"].str.contains("家庭")]
print(f"夫妻在同一个店/单位的 {len(shop)} 户（真正意义上的同单位）：")
for v in shop["父亲工作"]:
    print(f"    · {v}")
print(f"父母都填「家庭主妇 / 家庭父母」的 {len(none)} 户（都不就业，不是共同经营）：")
for v in none["父亲工作"]:
    print(f"    · {v}")

print("\n父亲为党政机关的 21 人，其母亲具体职业：")
print(sub2.head(3).to_string())

# ============================================================ 导出
tab8.to_csv(OUT_DIR / "父母职业_列联表_8类.csv", encoding="utf-8-sig")
tab3.to_csv(OUT_DIR / "父母职业_列联表_3类.csv", encoding="utf-8-sig")
pct_row.to_csv(OUT_DIR / "父母职业_母亲分布_行百分比.csv", encoding="utf-8-sig")
contrib_df.to_csv(OUT_DIR / "父母职业_单元格贡献与残差.csv", encoding="utf-8-sig")

res = pd.DataFrame([
    {"分析": "8类完整表", "n": int(tab8.values.sum()), "χ²": round(r1[0], 3), "df": r1[1],
     "渐近p": round(r1[2], 4), "置换p": round(r1[4], 4), "Cramér's V": round(r1[3], 3)},
    {"分析": "3类合并表", "n": int(tab3.values.sum()), "χ²": round(r2[0], 3), "df": r2[1],
     "渐近p": round(r2[2], 4), "置换p": round(r2[4], 4), "Cramér's V": round(r2[3], 3)},
])
res.to_csv(OUT_DIR / "父母职业_检验结果.csv", index=False, encoding="utf-8-sig")
print("\n\n[导出] 父母职业_列联表_8类.csv / 父母职业_列联表_3类.csv / "
      "父母职业_母亲分布_行百分比.csv / 父母职业_检验结果.csv / 父母职业_单元格贡献与残差.csv")
print("\n[检验汇总]")
print(res.to_string(index=False))
