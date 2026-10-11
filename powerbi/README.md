# The 10x Ledger: Power BI

The Adidas US sales audit as a Power BI report: the dataset reports $900M; price x units says $120M, and fixing it reverses which channel looks strongest.

This folder is a Power BI project (`Adidas_Audit.pbip`): a TMDL semantic model and a PBIR report. It is generated from one Python spec, checked against Microsoft's JSON schemas, and its numbers are recomputed independently in pandas.

## Open it

1. Open **`Adidas_Audit.pbip`** in Power BI Desktop. In versions before mid-2025, first turn on the preview features for Power BI Project (.pbip), the TMDL model format and the PBIR report format.
2. Click **Refresh**. The model reads this repo's cleaned CSVs from GitHub through the **BaseUrl** parameter. If asked, choose **Anonymous** access for `raw.githubusercontent.com`.
3. Check the visuals against [`docs/expected_values.md`](docs/expected_values.md).

## Pages

- **The audit:** reported vs recomputed sales, the overstatement and the share of lines inflated tenfold; the channel-share flip; monthly sales both ways; every data quality check.
- **Sales:** a Basis slicer switches every figure between reported and recomputed; year slicer; retailer, channel, state and a product-by-region matrix.

## Model

- **Tables:** Sales, Basis, Quality Log.
- **Relationships:** none (each page reads its own table).
- **14 DAX measures** in display folders: Switch (Selected Basis); Sales (Sales Reported, Sales Recomputed, Total Sales, Operating Profit, Units Sold); Audit (Overstatement, Lines, Lines Inflated 10x, Share of Lines Inflated); Channels (Channel Share, Channel Share Reported, Channel Share Recomputed); Coverage (Cities Selling). The full DAX is in [`docs/measures.md`](docs/measures.md).

## The switch

`Basis` is a disconnected table. `Selected Basis` reads the slicer with `SELECTEDVALUE` and every sales and profit measure follows it, the Power BI equivalent of the web dashboard's switch. `tools/expected.py` checks the totals and channel shares against `data/cleaned/audit_summary.json`: all agree.

## Rebuild and check

```bash
pip install jsonschema referencing pandas numpy
python tools/spec.py        # the spec: writes the .pbip and its folders
python tools/validate.py    # Microsoft schemas, field and DAX references, name clashes
python tools/expected.py    # what the report should show, checked against the project's own results
```

`tools/pbikit.py` is a small shared library for writing Power BI projects as code. It is used across the portfolio and encodes lessons from real Power BI Desktop runs: names are case-insensitive; a format string must not start with a quote; empty CSV cells must become null before a type change; in DAX, `BLANK() = FALSE()` is true.
