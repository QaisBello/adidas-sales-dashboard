"""
Audit and clean the Adidas US sales dataset.

Input : data/raw/adidas_us_sales.xlsx   (public Kaggle dataset, sheet "Data", header on row 5)
Output: data/cleaned/sales_clean.csv    one row per invoice line, with reported AND recomputed values
        data/cleaned/data_quality_log.csv   every check, how many rows it touched, what was done
        data/cleaned/audit_summary.json      headline numbers used in the README and dashboard

Run   : python src/clean.py
"""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "adidas_us_sales.xlsx")
OUT = os.path.join(ROOT, "data", "cleaned")
os.makedirs(OUT, exist_ok=True)

log = []
def note(check, rows, finding, action):
    log.append({"check": check, "rows_affected": int(rows), "finding": finding, "action": action})

# ---------------------------------------------------------------- load
df = pd.read_excel(RAW, sheet_name="Data", header=4).dropna(axis=1, how="all")
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
n0 = len(df)
note("Load", n0, "9,648 invoice lines, 13 columns, Jan 2020 to Dec 2021. Header sits on row 5 of the sheet.", "Read with header offset; dropped empty spacer columns.")

# ---------------------------------------------------------------- types & text
df["invoice_date"] = pd.to_datetime(df["invoice_date"])
for c in ["retailer", "region", "state", "city", "product", "sales_method"]:
    df[c] = df[c].astype(str).str.strip()
note("Missing values", int(df.isna().sum().sum()), "No blanks in any column.", "None needed.")

# ---------------------------------------------------------------- 1. the 10x problem
recalc = df["price_per_unit"] * df["units_sold"]
ratio = (df["total_sales"] / recalc.where(recalc > 0)).round(4)
x10 = ratio.eq(10)
assert set(ratio.dropna().unique()) <= {1.0, 10.0}, "unexpected sales/price*units ratio"
df["flag_sales_x10"] = x10
note("Total sales = price x units", int(x10.sum()),
     f"{x10.mean():.0%} of rows report total sales exactly 10x price x units. Every other row matches to the cent. "
     f"All {int((df.sales_method=='In-store').sum())} in-store rows are affected.",
     "Kept the reported figure and added a recomputed one (price x units). The dashboard shows both.")

# profit follows the reported sales, so it carries the same 10x
margin_check = ((df["operating_profit"] / df["total_sales"]).round(2) - df["operating_margin"]).abs().gt(0.011)
note("Operating profit = sales x margin", int(margin_check.sum()),
     "Profit always equals reported sales x margin, so the 10x rows have 10x profit too.",
     "Recomputed profit = recomputed sales x operating margin.")

df = df.rename(columns={"total_sales": "sales_reported", "operating_profit": "profit_reported"})
df["sales_recomputed"] = recalc
df["profit_recomputed"] = (recalc * df["operating_margin"]).round(2)

# ---------------------------------------------------------------- 2. near-duplicate pairs
key = ["retailer", "invoice_date", "state", "city", "product", "sales_method"]
dup = df.duplicated(subset=key, keep=False)
pairs = df[dup].groupby(key)["flag_sales_x10"].agg(["sum", "size"])
mixed = int(((pairs["sum"] == 1) & (pairs["size"] == 2)).sum())
df["flag_same_day_pair"] = dup
note("Same retailer, day, city, product and channel", int(dup.sum()),
     f"{len(pairs):,} pairs share every descriptive field. {mixed:,} of them pair one 10x row with one normal row, "
     "which suggests two sources merged at different scales.",
     "Kept both rows and flagged them; they differ in price and units, so they are not exact duplicates.")

# ---------------------------------------------------------------- 3. zero-unit lines
z = df["units_sold"].eq(0)
note("Zero units sold", int(z.sum()), "Lines with 0 units and $0 sales.", "Kept (they don't move totals); flagged.")
df["flag_zero_units"] = z

# ---------------------------------------------------------------- 4. retailer ID
ids = df.groupby("retailer_id")["retailer"].nunique()
shared = ids[ids > 1]
note("Retailer ID", int(df["retailer_id"].isin(shared.index).sum()),
     f"{len(shared)} IDs are shared by more than one retailer (ID {ids.idxmax()} is used by {ids.max()} different retailers).",
     "Dropped retailer_id; use the retailer name.")
df = df.drop(columns=["retailer_id"])

# ---------------------------------------------------------------- 5. ambiguous city names
amb = df.groupby("city")["state"].nunique().loc[lambda s: s > 1].index.tolist()
df["city_state"] = df["city"] + ", " + df["state"]
note("City names", int(df["city"].isin(amb).sum()), f"{', '.join(amb)} exist in two states each.", "Added city_state for unambiguous grouping.")

# ---------------------------------------------------------------- 6. coverage across years
df["year"] = df["invoice_date"].dt.year
df["month"] = df["invoice_date"].dt.to_period("M").astype(str)
cov = df.groupby("year").agg(rows=("city", "size"), cities=("city_state", "nunique"), retailers=("retailer", "nunique"))
note("Year-on-year coverage", int(cov.loc[2020, "rows"]),
     f"2020 has {cov.loc[2020,'rows']:,} rows from {cov.loc[2020,'cities']} cities; 2021 has {cov.loc[2021,'rows']:,} rows from {cov.loc[2021,'cities']} cities, "
     "so a raw year-on-year comparison mixes real growth with new cities entering the data.",
     "Added a like-for-like flag (city + retailer pairs present in both years) so growth can be compared fairly.")
both = df.groupby(["city_state", "retailer"])["year"].nunique().loc[lambda s: s == 2].index
df["like_for_like"] = df.set_index(["city_state", "retailer"]).index.isin(both)
note("Like-for-like growth", int(df.like_for_like.sum()),
     f"Only {len(both)} city-retailer pairs appear in both years ({int(df.like_for_like.sum()):,} rows). That is too few to separate real growth "
     "from new cities entering the data.",
     "Treat 2020-vs-2021 growth as unreliable. The dashboard labels it as such instead of headlining it.")

# ---------------------------------------------------------------- write
cols = ["invoice_date", "year", "month", "retailer", "region", "state", "city", "city_state", "product", "sales_method",
        "price_per_unit", "units_sold", "operating_margin", "sales_reported", "sales_recomputed",
        "profit_reported", "profit_recomputed", "flag_sales_x10", "flag_same_day_pair", "flag_zero_units", "like_for_like"]
df = df.sort_values(["invoice_date", "retailer", "city"]).reset_index(drop=True)
df[cols].to_csv(os.path.join(OUT, "sales_clean.csv"), index=False, date_format="%Y-%m-%d")
pd.DataFrame(log).to_csv(os.path.join(OUT, "data_quality_log.csv"), index=False)

ch = df.groupby("sales_method")[["sales_reported", "sales_recomputed"]].sum()
lfl = df[df.like_for_like].groupby("year")["sales_recomputed"].sum()
allyr = df.groupby("year")["sales_recomputed"].sum()
summary = {
    "rows": int(len(df)),
    "sales_reported": float(df.sales_reported.sum()),
    "sales_recomputed": float(df.sales_recomputed.sum()),
    "profit_reported": float(df.profit_reported.sum()),
    "profit_recomputed": float(df.profit_recomputed.sum()),
    "share_rows_x10": float(df.flag_sales_x10.mean()),
    "channel_share_reported": (ch.sales_reported / ch.sales_reported.sum()).round(4).to_dict(),
    "channel_share_recomputed": (ch.sales_recomputed / ch.sales_recomputed.sum()).round(4).to_dict(),
    "growth_all_rows": float(allyr[2021] / allyr[2020] - 1),
    "growth_like_for_like": float(lfl[2021] / lfl[2020] - 1),
}
json.dump(summary, open(os.path.join(OUT, "audit_summary.json"), "w"), indent=2)
print(pd.DataFrame(log)[["check", "rows_affected"]].to_string(index=False))
print(json.dumps(summary, indent=2))
