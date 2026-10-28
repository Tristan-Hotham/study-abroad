"""Step 6: the paper PDF. Fills code/paper_template.tex from data/results.json, checks facts stated in words,
writes release/paper/Hotham_Study_Abroad.tex and compiles it with xelatex (figures from step 5)."""
import os, re, shutil, subprocess, importlib
import pandas as pd
from common import *
site = importlib.import_module("04_build_site")
R = site.R; Y1 = R["meta"]["last_year"]
TOP = pd.read_csv(os.path.join(DATA, "top_destination.csv")); t1 = TOP[TOP.year == Y1].set_index("origin").top
FL = pd.read_csv(os.path.join(DATA, "flows_filled.csv"))
# facts stated only in the paper
assert all(t1[c] == "ARG" for c in ["BRA", "BOL", "PRY", "PER", "COL", "ECU"])
assert t1["DEU"] == "AUT" and t1["BEL"] == "DEU" and t1["AUT"] == "DEU" and t1["SVK"] == "CZE"
vt = TOP[(TOP.origin == "VNM") & (TOP.top == "JPN")].year
assert vt.min() == 2017 and all(TOP[(TOP.origin == "VNM") & (TOP.year >= 2017)].top == "JPN")
v = FL[(FL.origin == "VNM") & (FL.year == Y1)].set_index("host").students; assert v["JPN"] > v["USA"] and v["KOR"] > v["USA"]
assert [x[0] for x in R["magnet_origins"]["RUS"]["top"][:4]] == ["KAZ", "CHN", "UZB", "TKM"]
assert [x[0] for x in R["magnet_origins"]["ARE"]["top"][:4]] == ["IND", "OMN", "JOR", "PSE"]
assert TOP[(TOP.origin == "IRN") & (TOP.year == R["meta"]["first_year"])].top.iloc[0] == "USA" and t1["IRN"] == "TUR"
assert R["checks"]["usa_reported_years"] == [1999, 2005, 2013, 2014, 2015, 2016, 2017, 2018, 2020, 2021, 2023]
assert set(TOP[(TOP.year == Y1) & TOP.origin.isin(["TON", "WSM", "VUT", "SLB", "KIR", "TUV", "FJI", "PNG", "FSM"])].top) == {"AUS", "USA"}
assert t1["NAM"] == "ZAF" and t1["BWA"] == "ZAF" and t1["LSO"] == "ZAF"
assert R["changed_2013"]["moves"][0][0] == "USA>AUS" and R["changed_2013"]["moves"][1][0] == "FRA>SEN"
assert R["uk"]["provider_top_counts_2015"]["China"] > R["uk"]["provider_top_counts_2025"]["China"] and R["uk"]["provider_top_counts_2025"]["India"] > R["uk"]["provider_top_counts_2025"]["China"]
assert [x[0] for x in R["uk"]["top_last"][:5]] == ["India", "China", "Pakistan", "Nigeria", "Nepal"]
print("paper checks ok")

tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    return tex(v)
NM = dict(zip(*[site.load_json(os.path.join(DATA, "page.json"))[k] for k in ("codes", "names")]))
yrs = ["1999", "2005", "2013", str(Y1)]
hosts = []
for y in yrs:
    for h, n in sorted(R["top_counts"][y].items(), key=lambda x: -x[1])[:8]:
        if h not in hosts: hosts.append(h)
rows = "".join(f"{tex(NM[h])} & " + " & ".join(str(R['top_counts'][y].get(h, 0)) for y in yrs) + "\\\\\n" for h in hosts)
rows += "\\midrule Countries ranked & " + " & ".join(str(sum(R["top_counts"][y].values())) for y in yrs) + "\\\\\n"
rows += "Of which uncertain & " + " & ".join(str(R["uncertain_by_year"][y]) for y in yrs) + "\\\\\n"
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Number of countries for which each host is the number one destination. Hosts in the top eight in any of the four years.}\\label{tab:counts}"
      "\\begin{tabular}{lrrrr}\\toprule Host & " + " & ".join(yrs) + "\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
mr = ""
for c in ["TUR", "KOR", "MYS", "RUS", "SAU", "KGZ", "ARE", "CHN", "EGY"]:
    m = R["magnets"][c]
    mr += f"{tex(NM[c])} & {m['y0']} & {m['v0']:,} & {m['y1']} & {m['v1']:,} & {m['x']:.1f}\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Growth of international students in selected hosts (UIS inbound totals; first year is 2005 or the first available year after it).}\\label{tab:magnets}"
      "\\begin{tabular}{lrrrrr}\\toprule Host & From & Students & To & Students & Times\\\\\\midrule\n" + mr + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{TABLE_COUNTS}}", TC).replace("{{TABLE_MAGNETS}}", TM)
t = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(site.get(m.group(1)), m.group(3)), t)
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Study_Abroad"
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("pdf", os.path.getsize(os.path.join(ROOT, "release", NAME + ".pdf")) // 1024, "KB")
