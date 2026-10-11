"""Power BI version of the 10x Ledger (Adidas US sales audit). Run from powerbi/:

    python tools/spec.py        # writes Adidas_Audit.pbip and its folders
    python tools/validate.py    # schema and reference checks
    python tools/expected.py    # what the visuals should show, checked against data/cleaned/audit_summary.json

One slicer switches every figure between the sales as reported and as recomputed (price x units): a disconnected
Basis table read with SELECTEDVALUE, the Power BI equivalent of the web dashboard's switch.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbikit import C, M, build, card, color, lit, series_colors, slicer, text_box, visual  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "Adidas_Audit"
INK, RED, GREY, TEAL = "#13201B", "#C8323F", "#9AA3A0", "#0F766E"

TABLES = {
    "Sales": dict(
        file="sales_clean.csv",
        description="One row per invoice line (9,648), with the reported and the recomputed (price x units) sales and profit, and audit flags.",
        columns=[("invoice_date", "dateTime", {"formatString": "dd mmm yyyy"}), ("year", "int64", {"formatString": "0"}),
                 ("month", "string", {"isHidden": True}), ("retailer", "string", {}), ("region", "string", {}), ("state", "string", {}),
                 ("city", "string", {}), ("city_state", "string", {"isHidden": True}), ("product", "string", {}),
                 ("sales_method", "string", {}), ("price_per_unit", "decimal", {}), ("units_sold", "int64", {}),
                 ("operating_margin", "double", {"formatString": "0%"}), ("sales_reported", "decimal", {"isHidden": True}),
                 ("sales_recomputed", "decimal", {"isHidden": True}), ("profit_reported", "decimal", {"isHidden": True}),
                 ("profit_recomputed", "decimal", {"isHidden": True}), ("flag_sales_x10", "boolean", {}),
                 ("flag_same_day_pair", "boolean", {}), ("flag_zero_units", "boolean", {}), ("like_for_like", "boolean", {})],
        added=[("Month Start", "dateTime", {"formatString": "mmm yyyy"})],
        m_extra='''
            #"Month Start" = Table.AddColumn(#"Filtered Rows", "Month Start", each #datetime(
                Number.FromText(Text.Start([month], 4)), Number.FromText(Text.End([month], 2)), 1, 0, 0, 0), type datetime)
        ''', m_last="Month Start"),
    "Basis": dict(
        description="Disconnected table for the slicer that switches every figure between reported and recomputed sales.",
        m='''
let
    Source = Table.FromRecords({[Basis = "Recomputed (price x units)", Order = 1], [Basis = "As reported", Order = 2]}),
    Result = Table.TransformColumnTypes(Source, {{"Basis", type text}, {"Order", Int64.Type}})
in
    Result''',
        columns=[("Basis", "string", {"sortByColumn": "Order"}), ("Order", "int64", {"isHidden": True})]),
    "Quality Log": dict(
        file="data_quality_log.csv", description="Every check run on the raw file, with the rows affected and the action taken.",
        columns=[("check", "string", {}), ("rows_affected", "int64", {}), ("finding", "string", {}), ("action", "string", {})]),
}
RELATIONSHIPS = []

S = "Sales"
MEASURES = [
    ("Selected Basis", S, "Switch", "General", 'SELECTEDVALUE ( Basis[Basis], "Recomputed (price x units)" )',
     "The basis chosen in the slicer; recomputed when nothing is chosen."),
    ("Sales Reported", S, "Sales", "\\$#,0", "SUM ( Sales[sales_reported] )", "Total sales as published in the dataset."),
    ("Sales Recomputed", S, "Sales", "\\$#,0", "SUM ( Sales[sales_recomputed] )", "Price x units for every line."),
    ("Total Sales", S, "Sales", "\\$#,0", 'IF ( [Selected Basis] = "As reported", [Sales Reported], [Sales Recomputed] )',
     "Sales on the basis chosen in the slicer."),
    ("Operating Profit", S, "Sales", "\\$#,0",
     'IF ( [Selected Basis] = "As reported", SUM ( Sales[profit_reported] ), SUM ( Sales[profit_recomputed] ) )',
     "Operating profit on the chosen basis (profit follows the inflated sales column)."),
    ("Units Sold", S, "Sales", "#,0", "SUM ( Sales[units_sold] )", "Units sold."),
    ("Overstatement", S, "Audit", '0.0"x"', "DIVIDE ( [Sales Reported], [Sales Recomputed] )", "Reported sales as a multiple of the recomputed figure."),
    ("Lines", S, "Audit", "#,0", "COUNTROWS ( Sales )", "Invoice lines."),
    ("Lines Inflated 10x", S, "Audit", "#,0", "CALCULATE ( [Lines], Sales[flag_sales_x10] == TRUE () )",
     "Lines whose reported sales are exactly 10 x price x units."),
    ("Share of Lines Inflated", S, "Audit", "0.0%", "DIVIDE ( [Lines Inflated 10x], [Lines] )", "Share of lines carrying the 10x error."),
    ("Channel Share", S, "Channels", "0.0%", "DIVIDE ( [Total Sales], CALCULATE ( [Total Sales], REMOVEFILTERS ( Sales[sales_method] ) ) )",
     "Share of sales by channel on the chosen basis."),
    ("Channel Share Reported", S, "Channels", "0.0%",
     "DIVIDE ( [Sales Reported], CALCULATE ( [Sales Reported], REMOVEFILTERS ( Sales[sales_method] ) ) )", "Channel share as reported."),
    ("Channel Share Recomputed", S, "Channels", "0.0%",
     "DIVIDE ( [Sales Recomputed], CALCULATE ( [Sales Recomputed], REMOVEFILTERS ( Sales[sales_method] ) ) )", "Channel share recomputed."),
    ("Cities Selling", S, "Coverage", "#,0", "DISTINCTCOUNT ( Sales[city_state] )",
     "Cities with sales: 9 in 2020 against 47 in 2021, which is why year-on-year growth is not like-for-like."),
]

p1, p2 = "audit", "sales"
rep, rec = M(S, "Channel Share Reported", "As reported"), M(S, "Channel Share Recomputed", "Recomputed")
srep, srec = M(S, "Sales Reported", "As reported"), M(S, "Sales Recomputed", "Recomputed")
PAGES = [
    (p1, "The audit", [
        text_box(p1, "title", 24, 12, 1232, 52, "The 10x Ledger: the Adidas US sales dataset reports $900M. Price x units says $120M.", 18),
        card(p1, "rep", 24, 76, 300, 96, M(S, "Sales Reported", "Sales as reported")),
        card(p1, "rec", 336, 76, 300, 96, M(S, "Sales Recomputed", "Sales, price x units")),
        card(p1, "over", 648, 76, 300, 96, M(S, "Overstatement", "Overstated by")),
        card(p1, "share", 960, 76, 296, 96, M(S, "Share of Lines Inflated", "Lines inflated exactly 10x")),
        visual(p1, "flip", "clusteredColumnChart", 24, 184, 560, 300, {"Category": [C(S, "sales_method", "Channel")], "Y": [rep, rec]},
               "The flip: channel share before and after the correction",
               objects={"dataPoint": series_colors([rep, rec], [GREY, RED]), "labels": [{"properties": {"show": lit(True)}}]}, z=10),
        visual(p1, "trend", "lineChart", 600, 184, 656, 300, {"Category": [C(S, "Month Start", "Month")], "Y": [srep, srec]},
               "Monthly sales, reported vs recomputed", objects={"dataPoint": series_colors([srep, srec], [GREY, RED])}, z=11),
        visual(p1, "log", "tableEx", 24, 496, 1232, 212,
               {"Values": [C("Quality Log", "check", "Check"), C("Quality Log", "rows_affected", "Rows"), C("Quality Log", "finding", "Finding"),
                           C("Quality Log", "action", "Action")]}, "Every check on the raw file", z=12),
    ]),
    (p2, "Sales", [
        text_box(p2, "title", 24, 12, 700, 52, "Sales, on the basis you choose", 18),
        slicer(p2, "basis", 736, 8, 260, 64, C("Basis", "Basis"), None, single=True, mode="Basic"),
        slicer(p2, "year", 1008, 8, 248, 64, C(S, "year", "Year"), None),
        card(p2, "sales", 24, 76, 300, 96, M(S, "Total Sales", "Sales")),
        card(p2, "profit", 336, 76, 300, 96, M(S, "Operating Profit", "Operating profit")),
        card(p2, "units", 648, 76, 300, 96, M(S, "Units Sold", "Units sold")),
        card(p2, "cities", 960, 76, 296, 96, M(S, "Cities Selling", "Cities with sales")),
        visual(p2, "retailer", "clusteredBarChart", 24, 184, 400, 260, {"Category": [C(S, "retailer", "Retailer")], "Y": [M(S, "Total Sales", "Sales")]},
               "By retailer", objects={"dataPoint": [{"properties": {"fill": color(RED)}}]}, sort=(M(S, "Total Sales"), "Descending"), z=10),
        visual(p2, "channel", "clusteredBarChart", 440, 184, 400, 260, {"Category": [C(S, "sales_method", "Channel")], "Y": [M(S, "Channel Share", "Share")]},
               "Channel share", objects={"dataPoint": [{"properties": {"fill": color(INK)}}], "labels": [{"properties": {"show": lit(True)}}]},
               sort=(M(S, "Channel Share"), "Descending"), z=11),
        visual(p2, "state", "clusteredBarChart", 856, 184, 400, 524, {"Category": [C(S, "state", "State")], "Y": [M(S, "Total Sales", "Sales")]},
               "By state", objects={"dataPoint": [{"properties": {"fill": color(TEAL)}}]}, sort=(M(S, "Total Sales"), "Descending"), z=12),
        visual(p2, "matrix", "pivotTable", 24, 456, 816, 252,
               {"Rows": [C(S, "product", "Product")], "Columns": [C(S, "region", "Region")], "Values": [M(S, "Total Sales", "Sales")]},
               "Product by region", z=13),
    ]),
]

SPEC = dict(name=NAME, root=ROOT, tables=TABLES, measures=MEASURES, relationships=RELATIONSHIPS, pages=PAGES,
            base_url="https://raw.githubusercontent.com/QaisBello/adidas-sales-dashboard/main/data/cleaned/",
            base_desc="Folder of cleaned CSVs from this repo (data/cleaned). Point it at a local folder or another branch to test.")

if __name__ == "__main__":
    build(SPEC)
