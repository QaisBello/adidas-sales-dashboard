"""Build dashboard/index.html from src/dashboard_template.html. The page reads data/cleaned/*.csv
live from GitHub and falls back to the local copy when opened from the repo."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(ROOT, "src", "dashboard_template.html"), encoding="utf-8").read()
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>body{margin:0}</style>\n</head>\n<body>\n'
        + tpl.replace("<!--SITEBAR-->", "").replace('/*FALLBACKS*/["../data/cleaned/"]', '["../data/cleaned/"]')
        + "\n</body>\n</html>\n")
os.makedirs(os.path.join(ROOT, "dashboard"), exist_ok=True)
open(os.path.join(ROOT, "dashboard", "index.html"), "w", encoding="utf-8").write(page)
print("built dashboard/index.html")

# also make the page work when opened straight from disk (file://)
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from offline_snapshot import inline as _inline
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_inline(os.path.join(_R, "dashboard/index.html"), ['data_quality_log.csv', 'sales_clean.csv'], "../data/cleaned/", os.path.join(_R, "data/cleaned"))
