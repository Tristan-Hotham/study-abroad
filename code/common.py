"""Shared paths and helpers for the study-abroad pipeline."""
import os, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
INTERIM = os.path.join(DATA, "interim")
RAW = os.environ.get("SA_RAW", "/home/claude/hist/_data18/study-abroad")
NE = os.environ.get("NE", "/home/claude/hist/_data3/ne/geojson")
UIS_BUNDLE = os.path.join(RAW, "sa_uis_bilateral_v1.json.gz")
OECD_BUNDLE = os.path.join(RAW, "sa_oecd_mobility_v1.json.gz")
HESA_BUNDLE = os.path.join(RAW, "sa_hesa_t28_v1.json.gz")

SLUG = "study-abroad"
DOI = "10.5281/zenodo.23748258"
PAGE = "https://maps.tristanhotham.com/study-abroad/"
REPO = "https://github.com/Tristan-Hotham/study-abroad"
BLOG = "https://blog.tristanhotham.com/2026/10/28/study-abroad/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

FIRST_YEAR, LAST_YEAR = 1999, 2023   # animation range (set from coverage in 02_analyse.py; see results.json)

os.makedirs(INTERIM, exist_ok=True)


def save_json(obj, path, **kw):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), **kw)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
