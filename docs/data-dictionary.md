# Data dictionary: `data/cleaned/sales_clean.csv`

One row per invoice line (9,648 rows). Money in US dollars.

| Column | Type | Description |
|---|---|---|
| invoice_date | date | Invoice date (2020-01-01 to 2021-12-31) |
| year, month | int, text | Derived from invoice_date (`month` = `YYYY-MM`) |
| retailer | text | Amazon, Foot Locker, Kohl's, Sports Direct, Walmart, West Gear |
| region | text | Midwest, Northeast, South, Southeast, West |
| state, city | text | US state and city |
| city_state | text | `City, State`; Charleston and Portland exist in two states |
| product | text | Six product lines (men's/women's × apparel, athletic footwear, street footwear) |
| sales_method | text | In-store, Online, Outlet |
| price_per_unit | number | Unit price |
| units_sold | int | Units on the line |
| operating_margin | number | Operating margin as a fraction (0.10–0.80) |
| sales_reported | number | Total sales **as published** in the dataset |
| sales_recomputed | number | `price_per_unit × units_sold` (internally consistent) |
| profit_reported | number | Operating profit as published (= sales_reported × margin) |
| profit_recomputed | number | `sales_recomputed × operating_margin` |
| flag_sales_x10 | bool | `sales_reported` is exactly 10 × `sales_recomputed` |
| flag_same_day_pair | bool | Another line shares retailer, date, city, product and channel |
| flag_zero_units | bool | Line has 0 units |
| like_for_like | bool | City + retailer pair appears in both 2020 and 2021 |

Dropped: `retailer_id` (the same ID is shared by up to six different retailers).
