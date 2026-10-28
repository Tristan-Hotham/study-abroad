"""Step 7: blog post (release/blog/post.html, meta.json), Zenodo files (release/zenodo/), README.md and LICENSE."""
import os, re, json, shutil, zipfile, importlib
from common import *
site = importlib.import_module("04_build_site")
R = site.R
def fill(t):
    def rep(m):
        v = site.get(m.group(1)); f = m.group(3)
        return site.fmt(v, f)
    return re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", rep, t)
BL = os.path.join(ROOT, "release", "blog")
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read())
open(os.path.join(BL, "post.html"), "w", encoding="utf-8").write(post)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", post): assert os.path.exists(os.path.join(BL, m)), m
words = len(re.sub(r"<[^>]+>|\{\{IMG[^}]*\}\}", " ", post).split())
print("blog words", words)
Y0, Y1 = R["meta"]["first_year"], R["meta"]["last_year"]
meta = {"title": "Where would you go to university?", "slug": SLUG,
        "excerpt": f"Every country coloured by where its students most often go to university abroad, {Y0} to {Y1}. Old empires still show through, Turkey has become a magnet, and India has overtaken China in Britain.",
        "seo_description": f"A world map of each country's number one study abroad destination, {Y0} to {Y1}, from UNESCO data, plus every UK university.",
        "tags": ["international students", "higher education", "maps", "UNESCO", "HESA", "migration", "data visualisation", "data"],
        "header_alt": f"Title card reading 'Where would you go to university?' on pale paper beside a world map with each country coloured by its students' number one study destination in {Y1}: blue for the United States across the Americas, India and China; purple for France in West Africa; green for Russia in Central Asia; red for the United Kingdom; yellow for Australia; light blue for Argentina in South America."}
assert len(meta["seo_description"]) < 160
json.dump(meta, open(os.path.join(BL, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- README and LICENSE ----
V = R["v"]; m = R["meta"]; mg = R["magnets"]; uk = R["uk"]
readme = f"""# Where would you go to university?

Each country coloured by its students' number one study destination abroad, every year from {Y0} to {Y1}, from the UNESCO Institute for Statistics table of internationally mobile students by host and country of origin. With a flow explorer (where a country's students go, and where its own international students come from) and a view of every UK university from HESA.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- In {Y1} the table counts {V['students_counted_last']:,} students abroad in {m['hosts_last']} host countries that report origins.
- The United States is the most common number one destination ({V['n_usa_last']} countries in {Y1}), then the United Kingdom ({V['n_gbr_last']}), France ({V['n_fra_last']}), Australia ({V['n_aus_last']}) and Germany ({V['n_deu_last']}). Among countries measured cleanly in both years, the United States fell from {R['changed_2013']['count_a']['USA']} to {R['changed_2013']['count_b']['USA']} between 2013 and {Y1}.
- Russia is number one for all five Central Asian republics; Portugal takes {round(V['prt_luso_last']*100)}% of students abroad from Portuguese-speaking Africa. France's share of students from French-official sub-Saharan Africa fell from {round(V['fra_franco_first']*100)}% ({Y0}) to {round(V['fra_franco_last']*100)}% ({Y1}).
- Turkey's international students rose {mg['TUR']['x']:.1f} times, from {mg['TUR']['v0']:,} ({mg['TUR']['y0']}) to {mg['TUR']['v1']:,} ({mg['TUR']['y1']}); it is now first for Syria, Azerbaijan and Iran. South Korea grew {mg['KOR']['x']:.1f} times from {mg['KOR']['y0']}, Malaysia {mg['MYS']['x']:.1f} times from {mg['MYS']['y0']}. Vietnam's top destination has been Japan since 2017.
- China remains the largest sender ({V['chn_out_last']:,} abroad in {Y1}, UNESCO estimate) ahead of India ({V['ind_out_last']:,}). In the UK India overtook China in {uk['india_over_china_first_year']} (HESA): {uk['top_last'][0][1]:,} from India and {uk['top_last'][1][1]:,} from China in {uk['last_year']}.
- China, the United Arab Emirates and Singapore report no origins and cannot be ranked; {V['unc_last']} countries are flagged as uncertain in {Y1} because a host without data could be their number one.
- Checks: UNESCO-based shares are within one percentage point of the OECD's in {round(R['checks']['oecd_within_1pp']*100)}% of {R['checks']['oecd_pairs']:,} comparisons; UNESCO's UK total for {V['uk_check_year']} is within {V['uk_check_diff']*100:.1f}% of HESA's.

## Files

- `index.html`: the interactive page (Leaflet; loads `data/page.json`, `data/countries.json`, `data/towns.json`, `data/hills.png`).
- `data/flows_filled.csv`: every host, origin and year row used, with students and method (reported, interpolated, carried).
- `data/top_destination.csv`: each origin's number one destination by year, its share, the runner-up, students counted abroad, UIS outbound estimate, and the uncertainty flag with the hosts that could change it.
- `data/uk_providers_domicile.csv.gz`: HESA Table 28 as used (provider, country of permanent address, academic year, level, students).
- `data/results.json`: every number used in the page, paper, blog and collage.
- `data/interim/`: tidy extracts of the source bundles (UIS flows and totals, OECD shares, HESA, Wikidata provider locations) and the host coverage table.
- `code/`: the pipeline. `release/`: paper, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## How to rerun

Python 3 with pandas, numpy, shapely, pyproj, matplotlib; xelatex for the paper. The three source bundles (gzipped JSON fetched in a browser from the UIS data API, the OECD Data Explorer and HESA on 28 October 2026) are read from `SA_RAW`; Natural Earth from `NE`.

```
python3 code/01_prepare.py      # bundles -> data/interim/
python3 code/02_analyse.py      # gap filling, number one destinations, results.json
python3 code/03_page_data.py    # page.json, countries.json
python3 code/04_build_site.py   # index.html (with checks of facts stated in words)
python3 code/05_figures.py      # blog and paper figures, header.png
python3 code/06_paper.py        # paper PDF
python3 code/07_release.py      # blog post, Zenodo files, README
python3 reddit/collage.py       # Reddit collage
```

## Method in brief

A host-year counts as reported when its students by origin add up to at least 30% of its inbound total. A missing year between two reported years at most nine years apart is interpolated; otherwise the nearest reported year within two years is carried over. The number one destination is the host with the most students from that origin; countries with fewer than 50 students counted abroad are not ranked. For hosts without a breakdown in a year, the nearest reported breakdown, scaled by the change in the host's total, is compared with the counted number one; at 70% or more the country is flagged as uncertain.

## Sources and licences

- UNESCO Institute for Statistics (UIS), UIS Data API (https://api.uis.unesco.org), release {m['uis_version']}, extracted {m['uis_retrieved']}: inbound internationally mobile students by country of origin, totals of inbound and outbound mobile students. CC BY-SA 4.0.
- OECD Education at a Glance database (OECD Data Explorer), share of mobile students by destination and mobile students by region of origin, extracted {m['oecd_retrieved']}. CC BY 4.0.
- HESA Table 28, Non-UK permanent address students by HE provider and country of permanent address, 2014/15 to 2024/25 (https://www.hesa.ac.uk/data-and-analysis/students/table-28). CC BY 4.0; country names from ONS (OGL v3).
- Wikidata (CC0): UK provider locations via the UK Provider Reference Number.
- Natural Earth 1:50m admin 0 countries (public domain). Map layers shared with games-on-the-map: GeoNames cities15000 place names (CC BY 4.0) and hill shading from AWS Terrain Tiles. Optional base maps: Tiles © Esri.

Text, figures and derived data: CC BY-SA 4.0 (the UIS data are CC BY-SA 4.0). Code: MIT. See LICENSE.

## Citation

Hotham, T. (2026) Where would you go to university? Each country's number one study destination, {Y0} to {Y1}, from UNESCO data. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher, ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """Licences for this repository

Text, figures, the interactive page content and derived data (data/, release/, reddit/):
Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), https://creativecommons.org/licenses/by-sa/4.0/
The derived data adapt UNESCO Institute for Statistics data (CC BY-SA 4.0) and include HESA open data (CC BY 4.0),
OECD data (CC BY 4.0), Wikidata (CC0) and Natural Earth (public domain). Please credit the original sources as listed in README.md.

Code (code/, reddit/collage.py):

MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

# ---- Zenodo ----
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
pdf = "Hotham_Study_Abroad.pdf"
shutil.copy(os.path.join(ROOT, "release", pdf), Z)
for f in ["flows_filled.csv", "top_destination.csv", "uk_providers_domicile.csv.gz", "results.json"]:
    shutil.copy(os.path.join(DATA, f), Z)
zp = os.path.join(Z, f"{SLUG}_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ["code", "data"]:
        for root, _, files in os.walk(os.path.join(ROOT, d)):
            for f in files:
                if f.endswith(".pyc") or "__pycache__" in root: continue
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, ROOT))
    for f in ["README.md", "LICENSE"]: z.write(os.path.join(ROOT, f), f)
tex = open(os.path.join(ROOT, "release", "paper", "Hotham_Study_Abroad.tex"), encoding="utf-8").read()
ab = re.search(r"\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("``", "\u201c").replace("''", "\u201d")
title = "Where Would You Go to University? Each Country's Number One Study Destination, 1999 to 2023, from UNESCO Data".replace("1999", str(Y0)).replace("2023", str(Y1))
zm = {"title": title,
      "description_html": f"<p>{ab}</p><p>Interactive version: {PAGE}. Data and code: {REPO}. Blog post: to follow.</p>",
      "keywords": ["international students", "student mobility", "higher education", "UNESCO Institute for Statistics", "HESA", "OECD", "migration", "colonial ties", "language", "data visualisation"],
      "licence": "cc-by-sa-4.0",
      "related": [{"identifier": REPO, "relation": "issupplementedby", "resource_type": "software"},
                  {"identifier": PAGE, "relation": "issupplementedby", "resource_type": "other"},
                  {"identifier": "https://api.uis.unesco.org", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://data-explorer.oecd.org", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://www.hesa.ac.uk/data-and-analysis/students/table-28", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://www.naturalearthdata.com", "relation": "isderivedfrom", "resource_type": "dataset"}]}
json.dump(zm, open(os.path.join(Z, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for f in sorted(os.listdir(Z)): print(f, os.path.getsize(os.path.join(Z, f)) // 1024, "KB")
