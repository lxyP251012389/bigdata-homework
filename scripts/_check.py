# -*- coding: utf-8 -*-
"""对导出结果做一致性校验（只读，不改数据）"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
SRC_DIR = ROOT / "data"                              # 原始数据：优先仓库内 data/，否则退回原始位置
if not (SRC_DIR / "类别变量练习数据.csv").exists():
    SRC_DIR = Path(r"D:/")
CAT_ORDER = ["党政机关", "事业单位", "国有企业", "金融保险",
             "私营企业", "个体经营", "家庭/未就业", "其他"]

clean = pd.read_csv(OUT_DIR / "类别变量_清洗后.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
enc = pd.read_csv(OUT_DIR / "类别变量_编码后.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
src = pd.read_csv(SRC_DIR / "类别变量练习数据.csv", encoding="gb18030", dtype=str, keep_default_na=False)

ok = lambda b: "通过" if b else "**不通过**"
print(f"1. 行数：源 {len(src)} / 清洗后 {len(clean)} / 编码后 {len(enc)}  -> {ok(len(clean) == len(enc) == len(src))}")

# 2 残留脏字符
dirty = []
for df, name in ((clean, "清洗后"), (enc, "编码后")):
    for col in ("父亲工作", "母亲工作"):
        for i, v in df[col].items():
            if "\n" in v or "\r" in v or v != v.strip():
                dirty.append((name, i + 2, col, repr(v)))
print(f"2. 残留换行/首尾空格：{len(dirty)} 处  -> {ok(not dirty)}")
for d in dirty:
    print("     ", d)

# 3 类别取值合法性
bad = []
for col in ("父亲工作_性质", "母亲工作_性质"):
    vals = set(clean[col]) - {""}
    extra = vals - set(CAT_ORDER)
    if extra:
        bad.append((col, extra))
print(f"3. 类别取值都在 8 类内：{ok(not bad)} {bad if bad else ''}")

# 4 编码列与类别列一一对应（同一类别必须始终对应同一编码）
mismatch = []
for side in ("父亲", "母亲"):
    m = {}
    for cls, code in zip(clean[f"{side}工作_性质"], enc[f"{side}工作_性质_编码"]):
        if cls == "":
            if code != "":
                mismatch.append((side, "缺失但编码非空", code))
            continue
        if code == "":
            mismatch.append((side, "有类别但编码为空", cls))
            continue
        if m.setdefault(cls, code) != code:
            mismatch.append((side, cls, m[cls], code))
print(f"4. 编码与类别一一对应：{ok(not mismatch)} {mismatch[:5] if mismatch else ''}")

# 5 独热：每行父母各自恰好一个 1
hot_bad = []
for side in ("父亲", "母亲"):
    cols = [c for c in enc.columns if c.startswith(side + "_")]
    s = enc[cols].astype(int).sum(axis=1)
    bad_rows = [i + 2 for i, v in s.items() if v != 1]
    if bad_rows:
        hot_bad.append((side, bad_rows))
print(f"5. 独热每行恰好一个 1（各 {len([c for c in enc.columns if c.startswith('父亲_')])} 列）：{ok(not hot_bad)} {hot_bad if hot_bad else ''}")

# 6 没有原始值漏判
import re


def clean_text(s):
    """与清洗脚本同一套规则，用于公平比对"""
    s = str(s).replace("\r", "").replace("\n", "").replace("\t", "").replace("\u3000", " ")
    return re.sub(r"\s+", " ", s).strip()


raw_vals = {clean_text(v) for v in set(src["父亲工作"]).union(set(src["母亲工作"]))} - {""}
got = set(clean["父亲工作"]).union(set(clean["母亲工作"])) - {""}
lost = raw_vals - got - {"公安局", "个体"}   # 这两个已按设计归一
print(f"6. 原始取值无丢失（归一的 2 条除外）：{ok(not lost)} {sorted(lost) if lost else ''}")

# 7 逐行等长核对（防止清洗时错行；比对时套用同一套别名归一）
ALIAS = {"公安局": "市公安局", "个体": "个体经营"}
diff = [(i + 2, a, b) for i, (a, b) in
        enumerate(zip(src["父亲工作"].map(lambda v: ALIAS.get(clean_text(v), clean_text(v))), clean["父亲工作"]))
        if a != b]
print(f"7. 行对齐（父亲列逐行比对）：{ok(not diff)} {diff[:3] if diff else ''}")
