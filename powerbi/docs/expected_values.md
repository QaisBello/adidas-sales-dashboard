# Expected values

From `tools/expected.py`, checked against `data/cleaned/audit_summary.json`: **all agree**.

## Page 1 cards

| Card | Expected |
|---|---:|
| Sales as reported | $899,902,125 |
| Sales, price x units | $120,166,650 |
| Overstated by | 7.5x |
| Lines inflated exactly 10x | 40.3% |

## Channel share (the flip)

| Channel | As reported | Recomputed |
|---|---:|---:|
| In-store | 39.6% | 29.7% |
| Online | 27.5% | 37.4% |
| Outlet | 32.8% | 32.9% |

## Page 2 cards, no slicer (recomputed basis)

| Card | Expected |
|---|---:|
| Sales | $120,166,650 |
| Operating profit | $47,224,968 |
| Units sold | 2,478,861 |
| Cities with sales | 54 (2020: 9, 2021: 47) |

Switch the slicer to **As reported** and Sales should read $899,902,125.
