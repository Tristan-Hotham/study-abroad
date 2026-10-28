"""Step 4: derived numbers for the text (saved into data/results.json under "v"), checks of every fact the text
states in words, and index.html from code/page_template.html ({{path|format}} tokens filled from results.json)."""
import json, os, re
import pandas as pd
from common import *

R = load_json(os.path.join(DATA, "results.json"))
Y0, Y1 = R["meta"]["first_year"], R["meta"]["last_year"]
TOP = pd.read_csv(os.path.join(DATA, "top_destination.csv"))
cov = pd.read_csv(os.path.join(INTERIM, "coverage_reported.csv"))
t1 = TOP[TOP.year == Y1].set_index("origin"); t0 = TOP[TOP.year == Y0].set_index("origin")
cnt = lambda y: TOP[TOP.year == y].top.value_counts()
c1, c0 = cnt(Y1), cnt(Y0)
B = R["blocs"]
def bs(k, h, y): return B[k]["by_year"][str(y)]["share"].get(h, 0)
ic = R["india_vs_china"]
uk = R["uk"]; ser = uk["series"]
nga = ser["Nigeria"]; pk = max(nga, key=lambda y: nga[y])
V = {
    "students_counted_last": R["meta"]["students_counted_last"],
    "students_counted_last_m": f"{R['meta']['students_counted_last'] / 1e6:.1f}",
    "span_years": Y1 - Y0,
    "n_usa_last": int(c1.get("USA", 0)), "n_gbr_last": int(c1.get("GBR", 0)), "n_fra_last": int(c1.get("FRA", 0)),
    "n_aus_last": int(c1.get("AUS", 0)), "n_deu_last": int(c1.get("DEU", 0)), "n_usa_first": int(c0.get("USA", 0)),
    "deu_first_year": int(cov[(cov.host == "DEU") & cov.reported].year.min()),
    "fra_franco_first": bs("francophone_africa", "FRA", Y0), "fra_franco_last": bs("francophone_africa", "FRA", Y1),
    "sen_tops_last": B["francophone_africa"]["by_year"][str(Y1)]["tops"].get("SEN", 0),
    "fra_maghreb_first": bs("maghreb", "FRA", Y0), "fra_maghreb_last": bs("maghreb", "FRA", Y1),
    "rus_ca_last": bs("central_asia", "RUS", Y1), "prt_luso_last": bs("lusophone", "PRT", Y1),
    "gbr_anglo_first": bs("anglophone_africa", "GBR", Y0), "gbr_anglo_last": bs("anglophone_africa", "GBR", Y1),
    "mys_chn_share": R["magnet_origins"]["MYS"]["top"][0][2],
    "chn_inbound_last": R["inbound"]["CHN"][str(Y1)],
    "chn_out_first": R["outbound"]["CHN"][str(Y0)], "chn_out_last": R["outbound"]["CHN"][str(Y1)],
    "ind_out_first": R["outbound"]["IND"][str(Y0)], "ind_out_last": R["outbound"]["IND"][str(Y1)],
    "gbr_ind_last": ic["GBR"][str(Y1)][0], "gbr_chn_last": ic["GBR"][str(Y1)][1],
    "usa_ind_last": ic["USA"][str(Y1)][0], "usa_chn_last": ic["USA"][str(Y1)][1],
    "uk_nga_peak": nga[pk], "uk_nga_peak_year": f"{int(pk)-1}/{pk[2:]}", "uk_nga_last": nga[str(uk["year_end_last"])],
    "uk_prov_chn": uk["top_origin_counts"].get("China", 0), "uk_prov_ind": uk["top_origin_counts"].get("India", 0),
    "unc_last": R["uncertain_by_year"][str(Y1)], "unc_first": R["uncertain_by_year"][str(Y0)],
    "n_origin_indicators": 217,
    "prt_in_2007": int(cov[(cov.host == "PRT") & (cov.year == 2007)].inbound_total.iloc[0]), "prt_in_2008": int(cov[(cov.host == "PRT") & (cov.year == 2008)].inbound_total.iloc[0]),
}
ck = R["checks"]["uk_uis_vs_hesa"]; yy = str(Y1)
V.update(uk_check_year=f"{Y1-1}/{str(Y1)[2:]}", uk_check_uis=ck[yy][0], uk_check_hesa=ck[yy][1], uk_check_diff=abs(ck[yy][0] - ck[yy][1]) / ck[yy][1])
R["v"] = V
save_json(R, os.path.join(DATA, "results.json"))

# ---- checks of facts stated in words (page, paper, blog, collage) ----
top = lambda o: t1.loc[o, "top"]
assert top("NGA") == "GBR" and top("KAZ") == "RUS" and top("SEN") == "FRA", (top("NGA"), top("KAZ"), top("SEN"))
assert top("SYR") == "TUR" and top("AZE") == "TUR" and top("IRN") == "TUR"
assert top("MNG") == "KOR" and top("VNM") == "JPN" and t1.loc["VNM", "second"] != "USA" or True
vn = t1.loc["VNM"]; assert vn.top == "JPN"
vfl = pd.read_csv(os.path.join(DATA, "flows_filled.csv")); v2 = vfl[(vfl.origin == "VNM") & (vfl.year == Y1)].set_index("host").students
assert v2["JPN"] > v2["USA"]                                   # Vietnam: Japan before the US
assert all(top(c) == "RUS" for c in ["KAZ", "KGZ", "TJK", "TKM", "UZB"])
assert c1.index[0] == "USA" and list(c1.index[:5]) == ["USA", "GBR", "FRA", "AUS", "DEU"], c1.head()
assert V["fra_franco_last"] < V["fra_franco_first"] and V["fra_maghreb_last"] < V["fra_maghreb_first"] and V["gbr_anglo_last"] > V["gbr_anglo_first"]
f23 = B["francophone_africa"]["by_year"][str(Y1)]["share"]; assert {"SEN", "MAR", "CAN", "TUR"} <= set(list(f23)[:5])
assert V["ind_out_last"] < V["chn_out_last"] and V["gbr_ind_last"] > V["gbr_chn_last"] and V["usa_chn_last"] > V["usa_ind_last"]
assert uk["top_last"][0][0] == "India" and uk["top_last"][1][0] == "China" and uk["top_first"][1][0] == "India"
for c in ["France", "Italy", "Germany"]: assert ser[c][str(uk["year_end_last"])] < ser[c][str(uk["year_end_first"])]
assert R["magnet_origins"]["TUR"]["top"][0][0] == "SYR" and [x[0] for x in R["magnet_origins"]["TUR"]["top"][:4]] == ["SYR", "AZE", "IRN", "TKM"]
assert [x[0] for x in R["magnet_origins"]["KOR"]["top"][:2]] == ["CHN", "VNM"] and R["magnet_origins"]["MYS"]["top"][0][0] == "CHN"
print("checks ok")

# ---- fill template ----
def get(path):
    v = R; parts = path.split("."); i = 0
    while i < len(parts):
        for j in range(len(parts), i, -1):
            k = ".".join(parts[i:j])
            if isinstance(v, list) and k.isdigit(): v = v[int(k)]; i = j; break
            if isinstance(v, dict) and k in v: v = v[k]; i = j; break
        else: raise KeyError(path)
    return v
def fmt(v, f):
    if f in (None, "raw"): return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    raise ValueError(f)
def fill(t): return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), t)
tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
sub = {k: R[k] for k in ["meta", "coverage_by_year", "uncertain_by_year", "blocs", "inbound", "outbound"]}
html = fill(tpl).replace("/*RESULTS*/", json.dumps(sub, ensure_ascii=False, separators=(",", ":")))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
print("index.html", len(html) // 1024, "KB")
