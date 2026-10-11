"""What the Power BI report should show, recomputed in pandas and checked against data/cleaned/audit_summary.json.
Run from powerbi/:  python tools/expected.py   (writes docs/expected_values.md; exit code 1 on any disagreement)"""
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(os.path.dirname(ROOT), "data", "cleaned")
A = json.load(open(os.path.join(CLEAN, "audit_summary.json")))
d = pd.read_csv(os.path.join(CLEAN, "sales_clean.csv"))
problems = []


def check(label, got, want, tol):
    ok = abs(got - want) <= tol
    print(("PASS " if ok else "FAIL ") + f"{label}: {got} vs {want}")
    if not ok:
        problems.append(label)


check("Sales reported", d.sales_reported.sum(), A["sales_reported"], 0.5)
check("Sales recomputed", d.sales_recomputed.sum(), A["sales_recomputed"], 0.5)
check("Profit reported", d.profit_reported.sum(), A["profit_reported"], 0.5)
check("Share of lines inflated", d.flag_sales_x10.mean(), A["share_rows_x10"], 1e-9)
rep = d.groupby("sales_method").sales_reported.sum() / d.sales_reported.sum()
rec = d.groupby("sales_method").sales_recomputed.sum() / d.sales_recomputed.sum()
for ch in rep.index:
    check(f"{ch} share reported", round(rep[ch], 4), A["channel_share_reported"][ch], 0.00005)
    check(f"{ch} share recomputed", round(rec[ch], 4), A["channel_share_recomputed"][ch], 0.00005)
cities = d.groupby("year").city_state.nunique()
lines = ["# Expected values", "", "From `tools/expected.py`, checked against `data/cleaned/audit_summary.json`: "
         f"**{'all agree' if not problems else 'DISAGREEMENTS: ' + ', '.join(problems)}**.", "",
         "## Page 1 cards", "", "| Card | Expected |", "|---|---:|",
         f"| Sales as reported | ${d.sales_reported.sum():,.0f} |", f"| Sales, price x units | ${d.sales_recomputed.sum():,.0f} |",
         f"| Overstated by | {d.sales_reported.sum() / d.sales_recomputed.sum():.1f}x |", f"| Lines inflated exactly 10x | {d.flag_sales_x10.mean():.1%} |",
         "", "## Channel share (the flip)", "", "| Channel | As reported | Recomputed |", "|---|---:|---:|"]
lines += [f"| {ch} | {rep[ch]:.1%} | {rec[ch]:.1%} |" for ch in rep.index]
lines += ["", "## Page 2 cards, no slicer (recomputed basis)", "", "| Card | Expected |", "|---|---:|",
          f"| Sales | ${d.sales_recomputed.sum():,.0f} |", f"| Operating profit | ${d.profit_recomputed.sum():,.0f} |",
          f"| Units sold | {d.units_sold.sum():,} |", f"| Cities with sales | {d.city_state.nunique()} (2020: {cities[2020]}, 2021: {cities[2021]}) |",
          "", "Switch the slicer to **As reported** and Sales should read " f"${d.sales_reported.sum():,.0f}."]
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
open(os.path.join(ROOT, "docs", "expected_values.md"), "w").write("\n".join(lines) + "\n")
sys.exit(1 if problems else 0)
