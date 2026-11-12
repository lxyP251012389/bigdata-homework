# -*- coding: utf-8 -*-
"""
《大数据与人工智能》作业：类别变量的清理与转化
数据：父母工作单位（自由文本，53 行 × 2 列）
流程：读取 -> 清洗 -> 归一 -> 归大类 -> 编码 -> 导出
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent       # 仓库根目录
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

# 数据位置：优先仓库内 data/，找不到再退回本人的原始存放位置
SRC = DATA_DIR / "类别变量练习数据.csv"
if not SRC.exists():
    SRC = Path(r"D:/类别变量练习数据.csv")
    print(f"[提示] {DATA_DIR / '类别变量练习数据.csv'} 不存在，改用 {SRC}")

# ================================================================ 1. 读取
def read_any(path: Path):
    """依次尝试常见中文编码，返回 (DataFrame, 实际编码)"""
    last = None
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str, keep_default_na=False), enc
        except UnicodeDecodeError as e:
            last = e
    raise last


raw, enc_used = read_any(SRC)
print(f"[1 读取] 编码={enc_used}  形状={raw.shape}  列={list(raw.columns)}")

# ================================================================ 2. 清洗
def clean_text(s) -> str:
    """去内嵌换行/制表符/全角空格，压缩连续空格，去首尾空白"""
    s = str(s).replace("\r", "").replace("\n", "").replace("\t", "")
    s = s.replace("\u3000", " ")
    return re.sub(r"\s+", " ", s).strip()


df = raw.copy()
for col in df.columns:
    before = df[col].tolist()
    df[col] = df[col].map(clean_text)
    for a, b in zip(before, df[col].tolist()):
        if a != b:
            print(f"[2 清洗] 「{col}」{a!r} -> {b!r}")

# 空串 -> 缺失值（与「无」「家庭主妇」区分开：那是信息，这是没填）
for col in df.columns:
    df[col] = df[col].replace("", pd.NA)
    rows = [i + 2 for i in df.index[df[col].isna()]]
    if rows:
        print(f"[2 清洗] 「{col}」真空值 {len(rows)} 个（Excel 行号 {rows}）")

# ================================================================ 3. 归一
# 同一主体的不同写法 / 口语写法，合并到规范名
ALIAS = {
    "公安局": "市公安局",      # 少写"市"，与「市公安局」是同一个单位
    "个体": "个体经营",        # 口语写法
}
for col in df.columns:
    df[col] = df[col].map(lambda v: ALIAS.get(v, v) if pd.notna(v) else v)
if ALIAS:
    print(f"[3 归一] 别名合并 {len(ALIAS)} 条：{ALIAS}")

# ================================================================ 4. 归大类
CAT_ORDER = [
    "党政机关", "事业单位", "国有企业", "金融保险",
    "私营企业", "个体经营", "家庭/未就业", "其他",
]

# 个别名称用白名单直接指定，规则覆盖不到或容易误判的
OVERRIDES = {
    "区建豪汽修中心": "个体经营",          # 「中心」易被当作事业单位
    "万盛体能拓展中心鑫多米便利店": "个体经营",
    "大市场清华电动工具": "个体经营",
    "瑞禾农资": "个体经营",
    "老姐饺子馆": "个体经营",
    "娟红杂粮食府": "个体经营",
    "陇风巢浴": "个体经营",
    "凤巢浴足": "个体经营",
    "北门流觞烟酒": "个体经营",
    "九亩花田蛋糕店": "个体经营",
    "大自然旅行社": "私营企业",
    "长通公司": "私营企业",
    "银光聚银化工有限公司": "私营企业",
    "市政管理处": "事业单位",
    "泰安学校教职工": "事业单位",
    "市广播电视大学": "事业单位",
    "中国兵器工业公司三冶炼": "国有企业",
    "二十一冶": "国有企业",
    "中国平安财险股份有限公司": "金融保险",
    "农行XXX县支行": "金融保险",
    "XX路街道诚信社区": "其他",           # 社区居委会，非党政机关
}

# 规则按优先级从上到下，先匹配先赢。顺序很关键：
# 国企规则必须在党政机关之前，否则「水利水电第三工程局」会被「局$」吃掉
RULES = [
    # 家务劳动/无业：这是有效信息，不是缺失
    ("家庭/未就业", r"家庭主|家庭父|家庭母|^无$|^无业|^失业|^待业|^自由职业"),
    # 金融保险
    ("金融保险", r"银行|农行|工行|建行|中行|交行|信用社|农商|支行|分行|保险|财险|人寿|证券"),
    # 个体经营：店铺类结尾必须先于「学校/医院」判定，
    # 否则「第十一中学北侧校园书店」会被误判成学校
    ("个体经营", r"店$|馆$|食府|菜市场|超市|便利店|药店|商行|门市|浴$|浴足|烟酒|电动工具|^个体"),
    # 教育医疗：事业单位最典型的两类
    ("事业单位", r"学校|中学|小学|大学|学院|教职工|幼儿园|医院|保健|疾控|融媒体|广播电视"),
    # 国有企业：央企/地方国企强标识（含「局」的国企要抢在党政机关前面）
    ("国有企业", r"中铁|铁路建设|水利水电|工程局|中海油|兵器|冶炼|二十一冶|给排水|集团|供电|石油|石化|烟草|邮政|电信|移动|联通"),
    # 党政机关/政法机关
    ("党政机关", r"局$|委$|办$|政府|法院|检察院|纪委|管委会|街道|支队|大队|执法队|监狱|公安|统战|编办|审计|统计|财政"),
    # 其余事业单位（中心/站/处等公共服务机构）
    ("事业单位", r"中心|管理处|站$|所$|馆$|院$|台$"),
    # 私营企业
    ("私营企业", r"有限公司|有限责任公司|股份|公司|厂$|工贸|科技|商贸"),
]


def classify(name):
    """把工作单位名称归到 8 大类之一；缺失返回 NA，无法判断归「其他」"""
    if pd.isna(name):
        return pd.NA
    s = str(name)
    if s in OVERRIDES:
        return OVERRIDES[s]
    for cat, pat in RULES:
        if re.search(pat, s):
            return cat
    return "其他"


for col in df.columns:
    df[col + "_性质"] = df[col].map(classify).astype("string")

# ================================================================ 5. 编码
cat_type = pd.CategoricalDtype(categories=CAT_ORDER, ordered=True)
for col in df.columns[:2]:
    c = col + "_性质"
    df[c] = df[c].astype(cat_type)
    # 序号编码：按 CAT_ORDER 顺序 0..7，缺失留空（-1 转成 NA）
    codes = df[c].cat.codes
    df[c + "_编码"] = codes.where(codes >= 0).astype("Int8")

# 独热编码：每个大类一列 0/1，缺失单独一列标记（不混进任何类别）
for side, col in [("父亲", "父亲工作_性质"), ("母亲", "母亲工作_性质")]:
    for cat in CAT_ORDER:
        df[f"{side}_{cat}"] = (df[col] == cat).astype("int8")
    df[f"{side}_未填写"] = df[col].isna().astype("int8")
dummies = df[[c for c in df.columns if c.startswith(("父亲_", "母亲_"))]]

# 列顺序：父亲原值 -> 性质 -> 编码 -> 独热，母亲同理
order = ["父亲工作", "父亲工作_性质", "父亲工作_性质_编码"]
order += [c for c in df.columns if c.startswith("父亲_") and c not in order]
order += ["母亲工作", "母亲工作_性质", "母亲工作_性质_编码"]
order += [c for c in df.columns if c.startswith("母亲_") and c not in order]
df = df[order]

# ================================================================ 6. 导出
clean_cols = ["父亲工作", "父亲工作_性质", "母亲工作", "母亲工作_性质"]
p1 = OUT_DIR / "类别变量_清洗后.csv"
df[clean_cols].to_csv(p1, index=False, encoding="utf-8-sig")

p2 = OUT_DIR / "类别变量_编码后.csv"
df.to_csv(p2, index=False, encoding="utf-8-sig")

# 汇总表：验证清理效果
summary = pd.DataFrame({
    "父亲人数": df["父亲工作_性质"].value_counts().reindex(CAT_ORDER).fillna(0).astype(int),
    "母亲人数": df["母亲工作_性质"].value_counts().reindex(CAT_ORDER).fillna(0).astype(int),
})
summary["合计"] = summary.sum(axis=1)
summary.loc["缺失(未填写)"] = [int(df["父亲工作"].isna().sum()), int(df["母亲工作"].isna().sum()),
                          int(df["父亲工作"].isna().sum() + df["母亲工作"].isna().sum())]
p3 = OUT_DIR / "类别变量_类别汇总.csv"
summary.to_csv(p3, encoding="utf-8-sig")

# ================================================================ 7. 报告
print("\n[4 归类] 父亲工作性质分布")
print(df["父亲工作_性质"].value_counts(dropna=False).to_string())
print("\n[4 归类] 母亲工作性质分布")
print(df["母亲工作_性质"].value_counts(dropna=False).to_string())
print(f"\n[4 归类] 清洗前唯一值：父亲 {raw['父亲工作'].nunique()} / 母亲 {raw['母亲工作'].nunique()}")
print(f"[4 归类] 归类后唯一值：父亲 {df['父亲工作_性质'].nunique()} / 母亲 {df['母亲工作_性质'].nunique()}")
print(f"\n[5 编码] 编码后形状 = {df.shape}（含 {dummies.shape[1]} 列独热）")
print(f"[5 编码] 列名 = {list(df.columns)}")
print(f"\n[6 导出] {p1}\n[6 导出] {p2}\n[6 导出] {p3}")
print("\n[6 导出] 前 5 行预览：")
print(df[clean_cols + ["父亲工作_性质_编码", "母亲工作_性质_编码"]].head().to_string(index=False))
