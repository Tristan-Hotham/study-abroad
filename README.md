# Where would you go to university?

Each country coloured by its students' number one study destination abroad, every year from 1999 to 2023, from the UNESCO Institute for Statistics table of internationally mobile students by host and country of origin. With a flow explorer (where a country's students go, and where its own international students come from) and a view of every UK university from HESA.

Interactive version: https://maps.tristanhotham.com/study-abroad/
Paper: https://doi.org/10.5281/zenodo.23748258
Blog post: https://blog.tristanhotham.com/2026/10/28/study-abroad/

## Headline results

- In 2023 the table counts 6,234,900 students abroad in 114 host countries that report origins.
- The United States is the most common number one destination (38 countries in 2023), then the United Kingdom (28), France (16), Australia (15) and Germany (11). Among countries measured cleanly in both years, the United States fell from 39 to 33 between 2013 and 2023.
- Russia is number one for all five Central Asian republics; Portugal takes 61% of students abroad from Portuguese-speaking Africa. France's share of students from French-official sub-Saharan Africa fell from 57% (1999) to 29% (2023).
- Turkey's international students rose 16.6 times, from 18,166 (2005) to 301,634 (2023); it is now first for Syria, Azerbaijan and Iran. South Korea grew 8.2 times from 2005, Malaysia 4.5 times from 2006. Vietnam's top destination has been Japan since 2017.
- China remains the largest sender (1,076,015 abroad in 2023, UNESCO estimate) ahead of India (833,835). In the UK India overtook China in 2022/23 (HESA): 146,505 from India and 143,145 from China in 2024/25.
- China, the United Arab Emirates and Singapore report no origins and cannot be ranked; 22 countries are flagged as uncertain in 2023 because a host without data could be their number one.
- Checks: UNESCO-based shares are within one percentage point of the OECD's in 84% of 56,908 comparisons; UNESCO's UK total for 2022/23 is within 1.4% of HESA's.

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

- UNESCO Institute for Statistics (UIS), UIS Data API (https://api.uis.unesco.org), release 20260507-91260335, extracted 2026-10-28: inbound internationally mobile students by country of origin, totals of inbound and outbound mobile students. CC BY-SA 4.0.
- OECD Education at a Glance database (OECD Data Explorer), share of mobile students by destination and mobile students by region of origin, extracted 2026-10-28. CC BY 4.0.
- HESA Table 28, Non-UK permanent address students by HE provider and country of permanent address, 2014/15 to 2024/25 (https://www.hesa.ac.uk/data-and-analysis/students/table-28). CC BY 4.0; country names from ONS (OGL v3).
- Wikidata (CC0): UK provider locations via the UK Provider Reference Number.
- Natural Earth 1:50m admin 0 countries (public domain). Map layers shared with games-on-the-map: GeoNames cities15000 place names (CC BY 4.0) and hill shading from AWS Terrain Tiles. Optional base maps: Tiles © Esri.

Text, figures and derived data: CC BY-SA 4.0 (the UIS data are CC BY-SA 4.0). Code: MIT. See LICENSE.

## Citation

Hotham, T. (2026) Where would you go to university? Each country's number one study destination, 1999 to 2023, from UNESCO data. Zenodo. https://doi.org/10.5281/zenodo.23748258

Dr Tristan Hotham, Independent researcher, ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
