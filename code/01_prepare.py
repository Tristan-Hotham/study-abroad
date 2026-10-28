"""Step 1: read the three source bundles and write tidy tables to data/interim/.

UIS bilateral flows: one indicator per country of origin ("Inbound internationally mobile students from
<continent>: Students from <country>"), reported by each host country and year. Totals: inbound, outbound,
tertiary enrolment and mobility ratios. OECD: shares of each origin's mobile students by destination (a check).
HESA Table 28: non-UK students by UK provider and country of permanent address.
"""
import gzip, json, re, os, collections
import pandas as pd
from common import *

# ---------------- UIS ----------------
U = json.load(gzip.open(UIS_BUNDLE))
geo = {g["id"]: g["name"] for g in U["geounits"] if g["type"] == "NATIONAL"}
byname = {v.lower(): k for k, v in geo.items()}
MANUAL = {"cape verde": "CPV", "the united states": "USA", "the plurinational state of bolivia": "BOL",
          "the bolivarian republic of venezuela": "VEN", "hong kong, special administrative region of china": "HKG",
          "the islamic republic of iran": "IRN", "macao, special administrative region of china": "MAC",
          "turkey": "TUR", "the united kingdom": "GBR", "the federated states of micronesia": "FSM",
          "sudan (pre-secession)": "SDN"}   # pre-2011 Sudan merged with Sudan
ind = U["indicators"]
origin_of = {}
for i, (code, name) in enumerate(ind[:217]):
    o = re.sub(r".*Students from (.*), both sexes.*", r"\1", name).strip()
    k = o.lower()
    if k == "unknown countries":
        origin_of[i] = "UNK"; continue
    iso = MANUAL.get(k) or byname.get(k) or byname.get(re.sub(r"^the ", "", k))
    assert iso, o
    origin_of[i] = iso
TOT = {c: i for i, (c, n) in enumerate(ind)}
rows = []
for i, host, y, v, mag, q in U["rows"]:
    if i in origin_of:
        if v and host != origin_of[i]:
            rows.append((host, origin_of[i], y, float(v), q))
flows = pd.DataFrame(rows, columns=["host", "origin", "year", "students", "qualifier"])
flows = flows.groupby(["host", "origin", "year"], as_index=False).agg(students=("students", "sum"), qualifier=("qualifier", "max"))
flows = flows[flows.host.isin(geo)]
flows.to_csv(os.path.join(INTERIM, "uis_flows_reported.csv"), index=False)
print("UIS reported bilateral rows", len(flows), "hosts", flows.host.nunique(), "origins", flows.origin.nunique(),
      "years", flows.year.min(), flows.year.max())

names = {"26637": "inbound", "OE.5T8.40510": "outbound", "MOR.5T8.40510": "outbound_ratio",
         "MSEP.5T8": "inbound_rate", "25053": "tertiary_enrolment", "MENF.5T8": "net_flow"}
trows = []
for i, host, y, v, mag, q in U["rows"]:
    c = ind[i][0]
    if c in names and host in geo and v is not None:
        trows.append((host, y, names[c], float(v), q))
tot = pd.DataFrame(trows, columns=["iso3", "year", "measure", "value", "qualifier"])
tot.to_csv(os.path.join(INTERIM, "uis_totals.csv"), index=False)
print("UIS totals rows", len(tot))
save_json({"geounits": geo, "uis_source": U["source"], "uis_retrieved": U["retrieved"][:10],
           "uis_version": re.search(r"version (\S+)\)", U["source"]).group(1)}, os.path.join(INTERIM, "uis_meta.json"))

# ---------------- OECD ----------------
O = json.load(gzip.open(OECD_BUNDLE))
orows = []
for r in O["share_dest"]:
    try:
        orows.append((r["REF_AREA"], r["DESTINATION"], int(r["TIME_PERIOD"]), float(r["OBS_VALUE"])))
    except (KeyError, ValueError):
        pass
oe = pd.DataFrame(orows, columns=["host", "origin", "year", "share_pct"])
oe.to_csv(os.path.join(INTERIM, "oecd_share_dest.csv"), index=False)
rrows = []
for r in O["raw_mob"]:
    if r.get("SEX", "_T") in ("_T",) and r.get("ORIGIN") == "W":
        try:
            rrows.append((r["REF_AREA"], int(r["TIME_PERIOD"]), float(r["OBS_VALUE"])))
        except (KeyError, ValueError):
            pass
pd.DataFrame(rrows, columns=["host", "year", "mobile_students"]).to_csv(os.path.join(INTERIM, "oecd_host_totals.csv"), index=False)
print("OECD share rows", len(oe), "host totals", len(rrows))
save_json({"oecd_source": O["source"], "oecd_retrieved": O["retrieved"][:10]}, os.path.join(INTERIM, "oecd_meta.json"))

# ---------------- HESA ----------------
H = json.load(gzip.open(HESA_BUNDLE))
prov = H["providers"]; ctry = H["countries"]
hrows = []
for p, c, y, lv, v in H["rows"]:
    P, C = prov[p], ctry[c]
    hrows.append((P[0], P[1], P[2], P[3], C[0], C[1], int(y[:4]) + 1, ["all", "ug", "pg"][lv], v))
h = pd.DataFrame(hrows, columns=["ukprn", "provider", "prov_country", "prov_region", "dom_region", "dom_country", "year_end", "level", "students"])
h.to_csv(os.path.join(INTERIM, "hesa_t28_raw.csv.gz"), index=False, compression="gzip")
print("HESA rows", len(h))
print(h.prov_country.value_counts().head(8).to_dict())
print(h.dom_region.value_counts().head(20).to_dict())
print(h[h.provider.str.contains("Total", na=False)].provider.unique()[:10])
wd = H["wikidata_ukprn"]["rows"]
w = []
for r in wd:
    m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", r[3]) if len(r) > 3 else None
    w.append((r[1].strip('"'), re.sub(r'"@en$|^"', "", r[2]) if len(r) > 2 else "", r[0].strip("<>").rsplit("/", 1)[-1],
              float(m.group(1)) if m else None, float(m.group(2)) if m else None))
pd.DataFrame(w, columns=["ukprn", "wikidata_label", "qid", "lon", "lat"]).to_csv(os.path.join(INTERIM, "wikidata_ukprn.csv"), index=False)
save_json({"hesa_source": H["source"], "hesa_licence": H["licence"], "hesa_retrieved": H["retrieved"][:10],
           "hesa_meta_2024": H["metas"][-1][1][:14],
           "hesa_table_totals": {int(m.group(1)) + 1: int(m.group(2)) for _, meta in H["metas"] for l in meta
                                 for m in [re.match(r"(?:Table )?(\d{4})/\d{2} total,(\d+)", l)] if m}}, os.path.join(INTERIM, "hesa_meta.json"))
