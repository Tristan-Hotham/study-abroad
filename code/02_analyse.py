"""Step 2: fill gaps in the bilateral table, find each country's number one destination by year, and
compute every number used in the page, paper, blog and collage (data/results.json).

Gap filling (stated on the page and in the paper):
  * A host-year counts as reported when the students it reports by country of origin add up to at least
    30% of its total inbound mobile students (or, when the total is missing, at least 30% of the host's
    largest reported year).
  * A host's missing year between two reported years at most 9 years apart is filled by straight-line
    interpolation of every origin's count; otherwise the nearest reported year within 2 years is carried
    over. Nothing is invented beyond that. Every filled row is marked.
"""
import os, json, collections
import numpy as np
import pandas as pd
from common import *

Y0, Y1 = FIRST_YEAR, LAST_YEAR
F = pd.read_csv(os.path.join(INTERIM, "uis_flows_reported.csv"))
T = pd.read_csv(os.path.join(INTERIM, "uis_totals.csv"))
GEO = load_json(os.path.join(INTERIM, "uis_meta.json"))["geounits"]
inb = T[T.measure == "inbound"].set_index(["iso3", "year"]).value
outb = T[T.measure == "outbound"].set_index(["iso3", "year"]).value

# ---------- coverage ----------
bil = F.groupby(["host", "year"]).students.sum()
known = F[F.origin != "UNK"].groupby(["host", "year"]).students.sum()
cov = pd.DataFrame({"bilateral": bil, "known_origin": known}).fillna(0)
cov["inbound_total"] = [inb.get(k, np.nan) for k in cov.index]
hostmax = cov.groupby(level=0).bilateral.max()
cov["ratio"] = cov.bilateral / cov.inbound_total
cov["reported"] = np.where(cov.inbound_total.notna(), cov.ratio >= 0.3,
                           cov.bilateral >= 0.3 * hostmax.reindex(cov.index.get_level_values(0)).values)
cov = cov.reset_index().rename(columns={"level_0": "host"})
cov.to_csv(os.path.join(INTERIM, "coverage_reported.csv"), index=False)
REP = {h: sorted(g[g.reported].year.tolist()) for h, g in cov.groupby("host")}

# ---------- fill ----------
fl = F[F.origin != "UNK"]
by = {k: g.set_index("origin").students for k, g in fl.groupby(["host", "year"])}
REP = {h: [y for y in yrs if (h, y) in by] for h, yrs in REP.items()}
out = []
method_hy = {}
for h, yrs in REP.items():
    if not yrs: continue
    for y in range(Y0, Y1 + 1):
        if y in yrs:
            s = by[(h, y)]; m = "reported"
        else:
            prv = [x for x in yrs if x < y]; nxt = [x for x in yrs if x > y]
            p = prv[-1] if prv else None; n = nxt[0] if nxt else None
            if p is not None and n is not None and n - p <= 9:
                a, b = by[(h, p)], by[(h, n)]
                idx = a.index.union(b.index)
                w = (y - p) / (n - p)
                s = a.reindex(idx, fill_value=0) * (1 - w) + b.reindex(idx, fill_value=0) * w
                m = "interpolated"
            elif p is not None and y - p <= 2:
                s = by[(h, p)]; m = "carried"
            elif n is not None and n - y <= 2:
                s = by[(h, n)]; m = "carried"
            else:
                continue
        method_hy[(h, y)] = m
        for o, v in s.items():
            if v > 0 and o != h:
                out.append((h, o, y, round(float(v), 1), m))
FL = pd.DataFrame(out, columns=["host", "origin", "year", "students", "method"])
FL.to_csv(os.path.join(DATA, "flows_filled.csv"), index=False)
print("filled flows", len(FL), FL.method.value_counts().to_dict())

# ---------- number one destination ----------
tops = []
for (o, y), g in FL.groupby(["origin", "year"]):
    g = g.sort_values("students", ascending=False)
    tot = g.students.sum()
    if tot < 50: continue   # countries with fewer than 50 students counted abroad are not ranked
    a = g.iloc[0]; b = g.iloc[1] if len(g) > 1 else None
    tops.append(dict(origin=o, year=y, top=a.host, top_students=round(a.students), top_share=round(a.students / tot, 4),
                     second=b.host if b is not None else "", second_students=round(b.students) if b is not None else 0,
                     abroad_counted=round(tot), n_hosts=len(g),
                     top_estimated=a.method != "reported" or (b is not None and b.method != "reported")))
TOP = pd.DataFrame(tops)
# ---------- uncertainty: big hosts missing in a year ----------
# For a host with no origin data in year y (after filling), estimate what it might hold for each origin from its
# nearest reported year, scaled by the change in its total inbound students when both totals are known.
# If that estimate reaches 70% of the counted number one, the year is flagged as uncertain for that origin.
fill_years = collections.defaultdict(set)
for (h, y) in method_hy: fill_years[h].add(y)
unc = collections.defaultdict(list)
topd = TOP.set_index(["origin", "year"])
for h, yrs in REP.items():
    if not yrs: continue
    for y in range(Y0, Y1 + 1):
        if y in fill_years[h]: continue
        ny = min(yrs, key=lambda x: (abs(x - y), x))
        sc = 1.0
        if (h, y) in inb and (h, ny) in inb and inb[(h, ny)] > 0:
            sc = inb[(h, y)] / inb[(h, ny)]
        elif y < ny and (h, ny) in inb:
            sc = 1.0   # earlier than any total: assume no growth (conservative for a growing host)
        for o, v in by[(h, ny)].items():
            if o == h or (o, y) not in topd.index: continue
            est = v * sc
            if est >= 0.7 * topd.loc[(o, y), "top_students"]:
                unc[(o, y)].append((h, round(est)))
TOP["uncertain_hosts"] = [";".join(f"{h}:{e}" for h, e in sorted(unc.get((o, y), []), key=lambda x: -x[1])) for o, y in zip(TOP.origin, TOP.year)]
TOP["uncertain"] = TOP.uncertain_hosts != ""
TOP["outbound_uis"] = [round(outb[(o, y)]) if (o, y) in outb else None for o, y in zip(TOP.origin, TOP.year)]
TOP["share_of_outbound_counted"] = (TOP.abroad_counted / TOP.outbound_uis).round(3)

TOP.to_csv(os.path.join(DATA, "top_destination.csv"), index=False)
# ---------- results ----------
R = {"meta": {}, "checks": {}}
name = lambda c: GEO.get(c, c)
um = load_json(os.path.join(INTERIM, "uis_meta.json")); om = load_json(os.path.join(INTERIM, "oecd_meta.json")); hm = load_json(os.path.join(INTERIM, "hesa_meta.json"))
R["meta"].update(first_year=Y0, last_year=Y1, uis_version=um["uis_version"], uis_retrieved=um["uis_retrieved"],
                 oecd_retrieved=om["oecd_retrieved"], hesa_retrieved=hm["hesa_retrieved"],
                 reported_rows=int(len(F)), filled_rows=int(len(FL)),
                 filled_by_method={k: int(v) for k, v in FL.method.value_counts().items()},
                 hosts_any_bilateral=int(F.host.nunique()), origins=int(F[F.origin != "UNK"].origin.nunique()))
# coverage per year
cy = []
for y in range(Y0, Y1 + 1):
    hosts = [h for (h, yy), m in method_hy.items() if yy == y]
    world = sum(v for (c, yy), v in inb.items() if yy == y)
    shown = FL[FL.year == y].students.sum()
    # hosts with an inbound total but no origin breakdown in this year
    miss = sorted([(c, v) for (c, yy), v in inb.items() if yy == y and (c, y) not in method_hy], key=lambda x: -x[1])
    cy.append(dict(year=y, hosts=len(hosts), hosts_reported=sum(1 for h in hosts if method_hy[(h, y)] == "reported"),
                   students_counted=round(shown), inbound_total_all_hosts=round(world),
                   biggest_missing=[[c, round(v)] for c, v in miss[:6]]))
R["coverage_by_year"] = cy
last = {d["year"]: d for d in cy}[Y1]
R["meta"]["students_counted_last"] = last["students_counted"]
R["meta"]["hosts_last"] = last["hosts"]

# number of origins mapped and top hosts by number of origins
nt = TOP.groupby("year").size()
R["meta"]["origins_mapped_first"] = int(nt.get(Y0, 0)); R["meta"]["origins_mapped_last"] = int(nt.get(Y1, 0))
cnt = TOP.groupby(["year", "top"]).size().unstack(fill_value=0)
R["top_counts"] = {str(y): {h: int(v) for h, v in cnt.loc[y].items() if v} for y in cnt.index}
lead = lambda y: cnt.loc[y].sort_values(ascending=False)
R["lead_first"] = [[h, int(v)] for h, v in lead(Y0).head(8).items()]
R["lead_last"] = [[h, int(v)] for h, v in lead(Y1).head(8).items()]
# countries whose number one changed between first and last year
a = TOP[TOP.year == Y0].set_index("origin").top; b = TOP[TOP.year == Y1].set_index("origin").top
both = a.index.intersection(b.index)
ch = [(o, a[o], b[o]) for o in both if a[o] != b[o]]
R["changed"] = {"n_both": int(len(both)), "n_changed": len(ch),
                "moves": collections.Counter(f"{x}>{y}" for _, x, y in ch).most_common(15),
                "list": [[o, x, y] for o, x, y in sorted(ch)]}
R["uncertain_by_year"] = {str(y): int(g.uncertain.sum()) for y, g in TOP.groupby("year")}
R["uncertain_hosts_named"] = collections.Counter(h.split(":")[0] for s_ in TOP.uncertain_hosts for h in s_.split(";") if h).most_common(10)
def changes(ya, yb):
    A = TOP[(TOP.year == ya) & ~TOP.uncertain].set_index("origin").top; B = TOP[(TOP.year == yb) & ~TOP.uncertain].set_index("origin").top
    ix = A.index.intersection(B.index); c = [(o, A[o], B[o]) for o in ix if A[o] != B[o]]
    ca = A[ix].value_counts(); cb = B[ix].value_counts()
    return {"n_both": int(len(ix)), "n_changed": len(c), "moves": collections.Counter(f"{x}>{y}" for _, x, y in c).most_common(12),
            "list": [[o, x, y] for o, x, y in sorted(c)], "count_a": {k: int(v) for k, v in ca.head(10).items()}, "count_b": {k: int(v) for k, v in cb.head(10).items()}}
R["changed_robust"] = changes(Y0, Y1)
R["changed_2013"] = changes(2013, Y1)
cntc = TOP[~TOP.uncertain].groupby(["year", "top"]).size().unstack(fill_value=0)
R["top_counts_certain"] = {str(y): {h: int(v) for h, v in cntc.loc[y].items() if v} for y in cntc.index}
gain = collections.Counter(y for _, _, y in ch); loss = collections.Counter(x for _, x, _ in ch)
R["changed"]["gained"] = gain.most_common(10); R["changed"]["lost"] = loss.most_common(10)

# blocs
BLOCS = {
    "francophone_africa": ("French-official sub-Saharan Africa", ["BEN", "BFA", "CIV", "GAB", "GIN", "MLI", "NER", "SEN", "TGO", "CMR", "CAF", "TCD", "COG", "COD", "DJI", "COM", "MDG", "BDI", "RWA"]),
    "maghreb": ("Algeria, Morocco and Tunisia", ["DZA", "MAR", "TUN"]),
    "anglophone_africa": ("English-official Africa", ["NGA", "GHA", "KEN", "UGA", "TZA", "ZMB", "MWI", "BWA", "SLE", "GMB", "LSO", "SWZ", "ZWE", "NAM", "LBR"]),
    "central_asia": ("Central Asia", ["KAZ", "KGZ", "TJK", "TKM", "UZB"]),
    "lusophone": ("Portuguese-speaking Africa", ["AGO", "MOZ", "CPV", "GNB", "STP"]),
}
R["blocs"] = {}
for k, (lab, mem) in BLOCS.items():
    d = {"label": lab, "members": mem, "by_year": {}}
    for y in range(Y0, Y1 + 1):
        g = FL[(FL.year == y) & FL.origin.isin(mem)]
        tot = g.students.sum()
        if not tot: continue
        sh = g.groupby("host").students.sum().sort_values(ascending=False) / tot
        tt = TOP[(TOP.year == y) & TOP.origin.isin(mem)].top.value_counts()
        d["by_year"][str(y)] = {"total": round(tot), "share": {h: round(v, 4) for h, v in sh.head(6).items()},
                                "tops": {h: int(v) for h, v in tt.items()}, "n": int(tt.sum())}
    R["blocs"][k] = d

# magnets: inbound totals over time
MAG = ["USA", "GBR", "AUS", "DEU", "CAN", "FRA", "RUS", "JPN", "CHN", "TUR", "ARE", "MYS", "KOR", "SAU", "ARG", "IRN", "KGZ", "EGY", "SGP", "UZB", "NLD", "ITA", "ESP", "POL", "IND"]
R["inbound"] = {c: {str(y): round(v) for (cc, y), v in inb.items() if cc == c and 1998 <= y <= 2024} for c in MAG}
def grow(c, y0, y1):
    s = R["inbound"][c]; return s.get(str(y1)), s.get(str(y0))
R["magnets"] = {}
for c, y0 in [("TUR", 2005), ("ARE", 2011), ("MYS", 2005), ("KOR", 2005), ("CHN", 2006), ("RUS", 2005), ("SAU", 2005), ("KGZ", 2005), ("UZB", 2015), ("EGY", 2005), ("ARG", 2005)]:
    s = R["inbound"][c]; ys = sorted(int(k) for k in s)
    yy0 = min([y for y in ys if y >= y0], default=None); yy1 = max([y for y in ys if y <= Y1], default=None)
    if yy0 and yy1:
        R["magnets"][c] = {"y0": yy0, "v0": s[str(yy0)], "y1": yy1, "v1": s[str(yy1)], "x": round(s[str(yy1)] / s[str(yy0)], 1)}
# where do the new magnets' students come from (last reported year)
R["magnet_origins"] = {}
for c in ["TUR", "MYS", "KOR", "RUS", "SAU", "KGZ", "ARG", "ARE"]:
    g = FL[(FL.host == c) & (FL.method == "reported")]
    if g.empty: continue
    y = int(g.year.max()); g = g[g.year == y].sort_values("students", ascending=False); tot = g.students.sum()
    R["magnet_origins"][c] = {"year": y, "total": round(tot), "top": [[o, round(v), round(v / tot, 3)] for o, v in zip(g.origin, g.students)][:6]}

# outbound India vs China (UIS estimate)
R["outbound"] = {c: {str(y): round(v) for (cc, y), v in outb.items() if cc == c and 1998 <= y <= 2024}
                 for c in ["CHN", "IND", "VNM", "DEU", "NGA", "KOR", "UZB", "NPL", "FRA", "KAZ", "SAU", "USA", "GBR", "PAK", "IRN", "MAR", "TUR", "MYS"]}
# biggest senders, last year with estimates
ob = T[(T.measure == "outbound") & (T.year == Y1)].sort_values("value", ascending=False)
R["senders_last"] = [[c, round(v)] for c, v in zip(ob.iso3, ob.value)][:15]
ob0 = T[(T.measure == "outbound") & (T.year == Y0)].sort_values("value", ascending=False)
R["senders_first"] = [[c, round(v)] for c, v in zip(ob0.iso3, ob0.value)][:15]
world_out = T[(T.measure == "outbound")].groupby("year").value.sum()
R["world_outbound"] = {str(y): round(v) for y, v in world_out.items() if Y0 <= y <= 2024}
# India and China in the flows: in which hosts India now outnumbers China
ic = FL[FL.origin.isin(["IND", "CHN"]) & (FL.year == Y1)].pivot_table(index="host", columns="origin", values="students", aggfunc="sum").fillna(0)
ic = ic[(ic.IND + ic.CHN) >= 2000]
R["india_vs_china"] = {"hosts_india_more": sorted(ic[ic.IND > ic.CHN].index.tolist()), "hosts_china_more": sorted(ic[ic.CHN >= ic.IND].index.tolist()),
                       "by_host": {h: [round(r.IND), round(r.CHN)] for h, r in ic.sort_values("IND", ascending=False).iterrows()}}
for h in ["USA", "GBR", "AUS", "CAN", "DEU"]:
    s = FL[(FL.host == h) & FL.origin.isin(["IND", "CHN"])].pivot_table(index="year", columns="origin", values="students", aggfunc="sum")
    R["india_vs_china"][h] = {str(y): [round(r.get("IND", 0)), round(r.get("CHN", 0)), method_hy.get((h, y), "")] for y, r in s.iterrows()}

# top destination snapshots for named countries
for k in ["NGA", "IND", "CHN", "KAZ", "SEN", "MAR", "VNM", "PAK", "IRN", "BRA", "DEU", "GBR", "USA", "FRA", "UZB", "TKM", "AZE", "SYR", "IRQ", "AFG", "IDN", "KOR", "JPN", "NPL", "BGD", "EGY", "CMR", "CIV", "GHA", "KEN", "ZWE", "ZAF", "MEX", "CAN", "AUS", "ITA", "ESP", "TUR", "RUS", "UKR", "BLR", "MNG", "LAO", "KHM", "MMR", "THA", "MYS", "SAU", "YEM", "SDN", "SOM", "LBY", "TUN", "DZA"]:
    g = TOP[TOP.origin == k].set_index("year")
    R.setdefault("top_of", {})[k] = {str(y): [r.top, r.top_share, r.second, int(r.abroad_counted)] for y, r in g.iterrows() if y in (Y0, 2005, 2010, 2015, 2019, Y1)}

# ---------- checks ----------
# 1. UIS vs OECD shares
oe = pd.read_csv(os.path.join(INTERIM, "oecd_share_dest.csv"))
oe = oe[(oe.year <= Y1)]
uf = FL[FL.method == "reported"].merge(oe, on=["host", "origin", "year"])
uf["outb"] = [outb.get((o, y), np.nan) for o, y in zip(uf.origin, uf.year)]
uf = uf[uf.outb > 500]
uf["uis_pct"] = 100 * uf.students / uf.outb
d = (uf.uis_pct - uf.share_pct).abs()
big = uf[uf.share_pct >= 5]
R["checks"]["oecd_pairs"] = int(len(uf)); R["checks"]["oecd_median_abs_diff_pp"] = round(float(d.median()), 2)
R["checks"]["oecd_within_1pp"] = round(float((d <= 1).mean()), 3)
R["checks"]["oecd_corr"] = round(float(np.corrcoef(uf.uis_pct, uf.share_pct)[0, 1]), 4)
R["checks"]["oecd_big_pairs"] = int(len(big)); R["checks"]["oecd_big_within_2pp"] = round(float(((big.uis_pct - big.share_pct).abs() <= 2).mean()), 3)
# OECD hosts' top-origin agreement: the destination with the biggest OECD share for each origin among OECD hosts vs UIS
# 2. UK: UIS inbound vs HESA total (UIS year y = academic year ending in y)
H = pd.read_csv(os.path.join(INTERIM, "hesa_t28_raw.csv.gz")).drop_duplicates()
ht = pd.Series({int(k): v for k, v in hm["hesa_table_totals"].items()}).sort_index()   # published table totals
R["checks"]["uk_uis_vs_hesa"] = {str(y): [round(inb.get(("GBR", y), np.nan)) if ("GBR", y) in inb else None, int(v)] for y, v in ht.items()}
# 3. China
R["checks"]["china_inbound"] = R["inbound"]["CHN"]
R["checks"]["china_reports_origins"] = bool(("CHN" in REP) and REP.get("CHN"))
# largest hosts never reporting origins in the window
nev = [(c, max(v for (cc, yy), v in inb.items() if cc == c and Y0 <= yy <= Y1)) for c in set(i[0] for i in inb.index)
       if not any(Y0 <= y <= Y1 for y in REP.get(c, [])) and any(Y0 <= yy <= Y1 for (cc, yy) in inb.index if cc == c)]
R["checks"]["never_report_origin"] = sorted([[c, round(v)] for c, v in nev], key=lambda x: -x[1])[:12]
R["checks"]["japan_partial"] = {str(int(r.year)): round(float(r.ratio), 3) for _, r in cov[(cov.host == "JPN") & (cov.year >= 2013)].iterrows()}
R["checks"]["usa_reported_years"] = REP.get("USA", [])
R["checks"]["usa_methods"] = {str(y): method_hy.get(("USA", y), "") for y in range(Y0, Y1 + 1)}
R["checks"]["top_estimated_share_last"] = round(float(TOP[TOP.year == Y1].top_estimated.mean()), 3)
R["names"] = {c: GEO[c] for c in GEO}

# ---------- UK by university ----------
H = H[(H.provider != "Total") & (H.dom_country != "Total") & ~H.dom_country.str.startswith("Total") & (H.dom_region != "Total")]
H = H[~H.dom_country.str.contains("not otherwise specified|Unknown", case=False, regex=True)]
H.to_csv(os.path.join(DATA, "uk_providers_domicile.csv.gz"), index=False, compression="gzip")
ha = H[H.level == "all"]
yl = int(ha.year_end.max()); yf = int(ha.year_end.min())
uk = ha.groupby(["year_end", "dom_country"]).students.sum().unstack(fill_value=0)
R["uk"] = {"first_year": f"{yf-1}/{str(yf)[2:]}", "last_year": f"{yl-1}/{str(yl)[2:]}", "year_end_first": yf, "year_end_last": yl,
           "providers_last": int(ha[ha.year_end == yl].provider.nunique()),
           "total_by_year": {str(y): int(v) for y, v in ht.items()},
           "top_last": [[c, int(v)] for c, v in uk.loc[yl].sort_values(ascending=False).head(15).items()],
           "top_first": [[c, int(v)] for c, v in uk.loc[yf].sort_values(ascending=False).head(15).items()],
           "series": {c: {str(y): int(uk.loc[y, c]) for y in uk.index} for c in ["China", "India", "Nigeria", "Pakistan", "United States", "Hong Kong (Special Administrative Region of China)", "Malaysia", "Ireland", "France", "Italy", "Germany", "Spain", "Romania", "Bangladesh", "Saudi Arabia", "Greece", "Cyprus (European Union)"] if c in uk.columns}}
pt = ha[ha.year_end == yl].groupby(["provider", "dom_country"]).students.sum().reset_index()
provtot = pt.groupby("provider").students.sum()
toporig = pt.sort_values("students", ascending=False).drop_duplicates("provider").set_index("provider")
toporig["total"] = provtot
toporig["share"] = toporig.students / toporig.total
big = toporig[toporig.total >= 1000]
R["uk"]["providers_ge1000"] = int(len(big))
R["uk"]["top_origin_counts"] = big.dom_country.value_counts().head(10).to_dict()
R["uk"]["largest_providers"] = [[p, int(r.total), r.dom_country, round(r.share, 3)] for p, r in toporig.sort_values("total", ascending=False).head(12).iterrows()]
R["uk"]["most_concentrated"] = [[p, int(r.total), r.dom_country, round(r.share, 3)] for p, r in big.sort_values("share", ascending=False).head(10).iterrows()]
# diversity: number of countries with 5+ students; effective number (1/HHI)
div = []
for p, g in pt.groupby("provider"):
    tot = g.students.sum()
    if tot < 1000: continue
    s = g.students / tot
    div.append((p, int(tot), int((g.students >= 5).sum()), round(float(1 / (s ** 2).sum()), 1)))
div.sort(key=lambda x: -x[3])
R["uk"]["most_diverse"] = div[:8]; R["uk"]["least_diverse"] = div[-8:]
# China vs India top providers
for c in ["China", "India", "Nigeria", "United States", "Pakistan"]:
    g = pt[pt.dom_country == c].sort_values("students", ascending=False).head(6)
    R["uk"].setdefault("top_providers_for", {})[c] = [[p, int(v)] for p, v in zip(g.provider, g.students)]
# China-to-India switch at UK level
R["uk"]["india_over_china_first_year"] = next((f"{y-1}/{str(y)[2:]}" for y in uk.index if uk.loc[y, "India"] > uk.loc[y, "China"]), None)
# provider-level: how many providers had China top in first vs last year
for yy in (yf, yl):
    q = ha[ha.year_end == yy].groupby(["provider", "dom_country"]).students.sum().reset_index()
    qt = q.groupby("provider").students.sum()
    qq = q.sort_values("students", ascending=False).drop_duplicates("provider").set_index("provider")
    qq = qq[qt.reindex(qq.index) >= 500]
    R["uk"][f"provider_top_counts_{yy}"] = qq.dom_country.value_counts().head(8).to_dict()
# UG/PG split last year for China and India
lv = H[(H.year_end == yl) & H.dom_country.isin(["China", "India", "Nigeria"])].groupby(["dom_country", "level"]).students.sum().unstack()
R["uk"]["levels_last"] = {c: {k: int(v) for k, v in r.items()} for c, r in lv.iterrows()}

save_json(R, os.path.join(DATA, "results.json"), indent=None)
print(json.dumps({k: R[k] for k in ["lead_first", "lead_last"]}))
print("uncertain", R["uncertain_by_year"], R["uncertain_hosts_named"])
print("robust", R["changed_robust"]["n_changed"], R["changed_robust"]["n_both"], R["changed_robust"]["moves"][:8], R["changed_robust"]["count_a"], R["changed_robust"]["count_b"])
print("2013", R["changed_2013"]["n_changed"], R["changed_2013"]["n_both"], R["changed_2013"]["moves"][:8], R["changed_2013"]["count_a"], R["changed_2013"]["count_b"])
print("changed", R["changed"]["n_changed"], "of", R["changed"]["n_both"], R["changed"]["moves"][:8])
print("checks", {k: v for k, v in R["checks"].items() if not isinstance(v, dict)})
print("coverage last", last)
print("magnets", R["magnets"])
print("uk", R["uk"]["top_last"][:6], R["uk"]["india_over_china_first_year"])
