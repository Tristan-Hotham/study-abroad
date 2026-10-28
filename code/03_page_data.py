"""Step 3: compact data files for the interactive page.

data/page.json      names, colours, number one destination per country and year, all filled flows of 10+ students,
                    inbound and outbound totals, host-year methods, UK provider data
data/countries.json Natural Earth 1:50m countries (simplified) keyed by ISO3, for the choropleth and borders
data/towns.json, data/hills.png  the same generic world place-name and hill-shading layers as games-on-the-map
                    (GeoNames cities15000, CC BY 4.0; AWS Terrain Tiles); copied, not recomputed
"""
import os, json, shutil, re, collections
import numpy as np
import pandas as pd
from shapely.geometry import shape, mapping
from common import *

R = load_json(os.path.join(DATA, "results.json"))
Y0, Y1 = R["meta"]["first_year"], R["meta"]["last_year"]
GEO = R["names"]
FL = pd.read_csv(os.path.join(DATA, "flows_filled.csv"))
TOP = pd.read_csv(os.path.join(DATA, "top_destination.csv"))
T = pd.read_csv(os.path.join(INTERIM, "uis_totals.csv"))
cov = pd.read_csv(os.path.join(INTERIM, "coverage_reported.csv"))

# ---------- names ----------
SHORT = {"USA": "United States", "GBR": "United Kingdom", "RUS": "Russia", "KOR": "South Korea", "PRK": "North Korea", "IRN": "Iran",
         "SYR": "Syria", "VNM": "Vietnam", "LAO": "Laos", "BOL": "Bolivia", "VEN": "Venezuela", "TZA": "Tanzania", "MDA": "Moldova",
         "COD": "DR Congo", "COG": "Congo", "CZE": "Czechia", "HKG": "Hong Kong", "MAC": "Macao", "PSE": "Palestine",
         "CIV": "Côte d'Ivoire", "FSM": "Micronesia", "CPV": "Cape Verde", "SWZ": "Eswatini", "TUR": "Turkey", "MKD": "North Macedonia",
         "ARE": "UAE", "CAF": "Central African Republic", "DOM": "Dominican Republic", "BIH": "Bosnia and Herzegovina", "NLD": "Netherlands",
         "PHL": "Philippines", "GMB": "Gambia", "VAT": "Holy See", "BRN": "Brunei", "TLS": "Timor-Leste", "KNA": "St Kitts and Nevis",
         "LCA": "St Lucia", "VCT": "St Vincent", "VGB": "British Virgin Islands", "TCA": "Turks and Caicos", "ANT": "Netherlands Antilles",
         "XKX": "Kosovo", "SSD": "South Sudan", "GNQ": "Equatorial Guinea", "SLB": "Solomon Islands", "MHL": "Marshall Islands",
         "UNK": "unknown", "CUW": "Curaçao", "SXM": "Sint Maarten"}
def nm(c):
    if c in SHORT: return SHORT[c]
    n = GEO.get(c, c)
    n = re.sub(r"\s*\(.*\)$", "", n)
    return n
codes = sorted(set(FL.host) | set(FL.origin) | set(TOP.origin) | set(T.iso3))
IDX = {c: i for i, c in enumerate(codes)}

# ---------- colours (bold for the destinations that are number one most often; muted for the rest) ----------
COL = {"USA": "#2349C9", "GBR": "#D62839", "FRA": "#7A3DB8", "AUS": "#F2A900", "RUS": "#1B7F4C", "DEU": "#D81B60",
       "ZAF": "#F26419", "PRT": "#0EA5A0", "ARG": "#5BC0EB", "TUR": "#8C1C13", "SAU": "#8DB33A",
       "MYS": "#B5651D", "JOR": "#5E7C8A", "AUT": "#C084FC", "ITA": "#1E9E5A"}
COL_DARK = {"USA": "#5C83FF", "GBR": "#FF5A68", "FRA": "#B07CF0", "AUS": "#FFC933", "RUS": "#3DBE7C", "DEU": "#FF5C93",
            "ZAF": "#FF8A47", "PRT": "#2ED3CC", "ARG": "#8AD8FF", "TUR": "#E2574C", "SAU": "#B5DB5E",
            "MYS": "#E3964F", "JOR": "#9BB8C6", "AUT": "#D8B4FE", "ITA": "#4CC98A"}

# ---------- number one per year ----------
top = {}
for y, g in TOP.groupby("year"):
    top[str(y)] = {IDX[o]: [IDX[h], int(round(s * 1000)), int(u), int(n), IDX[sec] if isinstance(sec, str) and sec else -1, int(ts)]
                   for o, h, s, u, n, sec, ts in zip(g.origin, g.top, g.top_share, g.uncertain, g.abroad_counted, g.second, g.top_students)}
unc = {f"{IDX[o]}_{y}": h for o, y, h in zip(TOP.origin, TOP.year, TOP.uncertain_hosts) if isinstance(h, str) and h}

# ---------- flows (10+ students) ----------
f = FL[FL.students >= 10]
flows = {}
for y, g in f.groupby("year"):
    arr = []
    for h, o, v in zip(g.host, g.origin, g.students):
        arr += [IDX[h], IDX[o], int(round(v))]
    flows[str(y)] = arr
meth = {}
mcode = {"reported": 0, "interpolated": 1, "carried": 2}
for (h, y), g in FL.groupby(["host", "year"]):
    meth.setdefault(str(IDX[h]), {})[str(y)] = mcode[g.method.iloc[0]]

def tot(measure):
    t = T[(T.measure == measure) & (T.year >= Y0 - 1) & (T.year <= Y1 + 1)]
    out = {}
    for c, y, v in zip(t.iso3, t.year, t.value):
        if c in IDX: out.setdefault(str(IDX[c]), {})[str(y)] = int(round(v)) if measure in ("inbound", "outbound") else round(v, 2)
    return out

# ---------- countries geometry ----------
ne = load_json(os.path.join(NE, "ne_50m_admin_0_countries.geojson"))
feats, cent = [], {}
for ft in ne["features"]:
    p = ft["properties"]; iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
    if iso == "SDS": iso = "SSD"
    if iso in ("ATA",): continue
    g = shape(ft["geometry"]).simplify(0.04, preserve_topology=True)
    if g.is_empty: continue
    gj = mapping(g)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 2), round(c[1], 2)]
    gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
    feats.append({"type": "Feature", "properties": {"iso": iso, "i": IDX.get(iso, -1), "n": p["NAME"]}, "geometry": gj})
    cent[iso] = [round(p["LABEL_X"], 2), round(p["LABEL_Y"], 2)]
save_json({"type": "FeatureCollection", "features": feats}, os.path.join(DATA, "countries.json"))
# centroids for countries without a polygon at this scale: none invented; they simply have no dot or arc

# ---------- UK providers ----------
H = pd.read_csv(os.path.join(DATA, "uk_providers_domicile.csv.gz"))
HMAP = {"Bahamas, The": "BHS", "Gambia, The": "GMB", "Congo (Democratic Republic)": "COD", "Cyprus (European Union)": "CYP",
        "Cyprus (Non-European Union)": "CYP", "Hong Kong (Special Administrative Region of China)": "HKG",
        "Macao (Special Administrative Region of China)": "MAC", "Korea (North)": "PRK", "Korea (South)": "KOR",
        "Myanmar (Burma)": "MMR", "Occupied Palestinian Territories": "PSE", "Kingdom of eSwatini": "SWZ", "Swaziland": "SWZ",
        "Ivory Coast": "CIV", "East Timor": "TLS", "Canary Islands": "ESP", "St Kitts and Nevis": "KNA", "St Lucia": "LCA",
        "St Vincent and The Grenadines": "VCT", "Russia": "RUS", "Taiwan": "TWN", "Kosovo": "XKX", "Laos": "LAO", "Vietnam": "VNM",
        "Iran": "IRN", "Syria": "SYR", "Bolivia": "BOL", "Venezuela": "VEN", "Tanzania": "TZA", "Moldova": "MDA", "Brunei": "BRN",
        "Czech Republic": "CZE", "Cape Verde": "CPV", "Congo": "COG", "United States": "USA", "Turkey": "TUR", "Micronesia": "FSM",
        "Netherlands": "NLD", "Philippines": "PHL", "Sint Maarten (Dutch part)": "SXM", "Curaçao": "CUW",
        "St Helena, Ascension and Tristan da Cunha": "SHN", "Falkland Islands": "FLK", "Faroe Islands": "FRO", "Réunion": "REU",
        "Martinique": "MTQ", "Guadeloupe": "GLP", "French Guiana": "GUF", "Mayotte": "MYT", "Åland Islands": "ALA"}
byname = {}
for ft in ne["features"]:
    p = ft["properties"]; iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
    for k in ("NAME", "NAME_LONG", "NAME_EN", "ADMIN"): byname[p[k].lower()] = iso
for c, n in GEO.items(): byname.setdefault(n.lower(), c)
hiso = {}
for c in H.dom_country.unique():
    hiso[c] = HMAP.get(c) or byname.get(c.lower()) or ""
unm = sorted(c for c, v in hiso.items() if not v)
print("HESA countries without ISO3:", unm)
H["iso"] = H.dom_country.map(hiso)
H.drop(columns=[]).to_csv(os.path.join(DATA, "uk_providers_domicile.csv.gz"), index=False, compression="gzip")
ha = H[H.level == "all"]
years = sorted(ha.year_end.unique())
hc = sorted(ha.dom_country.unique()); hci = {c: i for i, c in enumerate(hc)}
wd = pd.read_csv(os.path.join(INTERIM, "wikidata_ukprn.csv"), dtype={"ukprn": str}).drop_duplicates("ukprn")
wd = wd.set_index("ukprn")
provs = []
pdata = {}
ha = ha[ha.ukprn.notna()].copy(); ha["ukprn"] = ha.ukprn.astype("int64").astype(str)
last_names = ha.sort_values("year_end").drop_duplicates("ukprn", keep="last").set_index("ukprn").provider
for k, (u, g) in enumerate(ha.groupby("ukprn")):
    ll = wd.loc[u] if u in wd.index else None
    lon = float(ll.lon) if ll is not None and pd.notna(ll.lon) else None
    lat = float(ll.lat) if ll is not None and pd.notna(ll.lat) else None
    tot_by_y = g.groupby("year_end").students.sum()
    provs.append([last_names[u], u, lon, lat, int(tot_by_y.get(years[-1], 0)), ll.qid if ll is not None else ""])
    d = {}
    for y, gg in g.groupby("year_end"):
        arr = []
        for c, v in zip(gg.dom_country, gg.students): arr += [hci[c], int(v)]
        d[str(y)] = arr
    pdata[str(k)] = d
uk_tot = {}
for y, gg in ha.groupby("year_end"):
    s = gg.groupby("dom_country").students.sum()
    uk_tot[str(y)] = [x for c, v in s.items() for x in (hci[c], int(v))]

page = {"years": [Y0, Y1], "codes": codes, "names": [nm(c) for c in codes], "cent": [cent.get(c) for c in codes],
        "col": {str(IDX[k]): v for k, v in COL.items()}, "colDark": {str(IDX[k]): v for k, v in COL_DARK.items()},
        "top": top, "unc": unc, "flows": flows, "meth": meth,
        "inbound": tot("inbound"), "outbound": tot("outbound"), "outRatio": tot("outbound_ratio"),
        "uk": {"years": [int(y) for y in years], "countries": hc, "iso": [IDX.get(hiso[c], -1) for c in hc], "providers": provs, "data": pdata, "total": uk_tot}}
save_json(page, os.path.join(DATA, "page.json"))
print("page.json", os.path.getsize(os.path.join(DATA, "page.json")) // 1024, "KB; countries.json",
      os.path.getsize(os.path.join(DATA, "countries.json")) // 1024, "KB; providers", len(provs),
      "with coords", sum(1 for p in provs if p[2] is not None))
G = "/home/claude/hist/games-on-the-map/data"
for fn in ("towns.json", "hills.png"):
    if not os.path.exists(os.path.join(DATA, fn)): shutil.copy(os.path.join(G, fn), os.path.join(DATA, fn))
