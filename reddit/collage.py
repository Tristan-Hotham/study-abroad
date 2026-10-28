"""Reddit collage (2400 x 3000): run from anywhere; reads ../data and draws with code/figlib.py."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "code"))
import numpy as np, pandas as pd
from matplotlib.colors import to_rgb
import matplotlib.patches as mpatches
from figlib import *
from common import DATA, load_json
R = load_json(os.path.join(DATA, "results.json")); V = R["v"]; Y0, Y1 = R["meta"]["first_year"], R["meta"]["last_year"]
TOP = pd.read_csv(os.path.join(DATA, "top_destination.csv"))
P = load_json(os.path.join(DATA, "page.json")); NM = dict(zip(P["codes"], P["names"]))
CBG = "#F5F2EA"
def mix(c, t):
    r = np.array(to_rgb(c)); b = np.array(to_rgb(CBG)); return tuple(b + (r - b) * t)
def ymap(ax, y, big=False):
    g = TOP[TOP.year == y]
    draw_world(ax, {o: mix(hostcol(h), .5 + .5 * min(1, s / .6)) for o, h, s in zip(g.origin, g.top, g.top_share)},
               edge=CBG, lw=.35 if big else .2, dashed=set(g[g.uncertain].origin) if big else ())
    cnt = g.top.value_counts(); mx = cnt.max()
    for h, n in cnt.items():
        c = centroid(h)
        if c is None or (not big and n < 3): continue
        ax.scatter([c[0]], [c[1]], s=(40 + 900 * n / mx) * (1 if big else .35), color=hostcol(h), edgecolor="white", lw=2 if big else 1, zorder=5)
        if big and n >= 4: ax.text(c[0], c[1], str(n), ha="center", va="center", fontsize=11, color="white", weight="bold", zorder=6, family=MONO)
    return cnt

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=CBG)
fig.text(.045, .968, "Where would you go to university?", fontproperties=DISP, fontsize=45, color=FG, va="top")
fig.text(.045, .918, f"Every country coloured by where its own students most often go abroad to study, {Y1}.\nUNESCO counts of {V['students_counted_last']:,} international students by host and home country.",
         family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.4)
ax = fig.add_axes([.0, .485, 1.0, .37]); ax.set_facecolor(CBG)
cnt = ymap(ax, Y1, big=True)
lab = {"USA": (-1.05e7, 1.6e6), "GBR": (-3.6e6, 6.3e6), "FRA": (-3.9e6, 2.3e6), "RUS": (1.38e7, 5.7e6), "AUS": (1.05e7, -5.7e6), "TUR": (1.0e6, 2.6e6), "ARG": (-8.2e6, -5.3e6), "DEU": (-3.7e6, 4.3e6), "ZAF": (4.4e6, -4.6e6)}
for h, (tx, ty) in lab.items():
    c = centroid(h)
    ax.annotate(f"{NM[h]}: first for {cnt.get(h, 0)}", xy=c, xytext=(tx, ty), fontsize=11, family=MONO, color=hostcol(h), weight="bold",
                ha="center", va="center", arrowprops=dict(arrowstyle="-", color=hostcol(h), lw=1.1), zorder=7,
                bbox=dict(boxstyle="round,pad=0.25", fc=CBG, ec="none", alpha=.9))
# big numbers
nums = [(f"{V['n_usa_last']}", COL["USA"], f"countries pick the United\nStates first in {Y1}, more\nthan any other destination"),
        (f"{R['magnets']['TUR']['x']:.1f}x", COL["TUR"], f"growth in Turkey's\ninternational students since\n{R['magnets']['TUR']['y0']}; first for Syria and Iran"),
        (f"{round(V['fra_franco_first']*100)}%: {round(V['fra_franco_last']*100)}%", COL["FRA"], f"share of French-speaking\nAfrica's students abroad who\nare in France, {Y0} and {Y1}"),
        (R["uk"]["india_over_china_first_year"], COL["GBR"], "India overtakes China as\nthe biggest sender to UK\nuniversities (HESA)")]
for k, (big, col, small) in enumerate(nums):
    x = .045 + k * .238
    fig.text(x, .475, big, fontproperties=DISP, fontsize=31, color=col, va="top")
    fig.text(x, .432, small, family=SER, fontsize=11.5, color=FG, va="top", linespacing=1.3)
fig.add_artist(plt.Line2D([.045, .955], [.37, .37], color=RULE, lw=1.2, transform=fig.transFigure))
# small multiples
fig.text(.045, .355, "THE SAME MAP IN EARLIER YEARS", family=MONO, fontsize=11, color=MUTED)
for k, y in enumerate([Y0, 2005, 2013]):
    a = fig.add_axes([.02 + k * .245, .19, .25, .15]); a.set_facecolor(CBG)
    c = ymap(a, y)
    a.set_title(f"{y}: US {c.get('USA',0)} · UK {c.get('GBR',0)} · France {c.get('FRA',0)}", family=MONO, fontsize=10.5, color=FG, pad=2)
# India v China in UK
a = fig.add_axes([.79, .205, .17, .13]); a.set_facecolor(CBG)
s = R["uk"]["series"]; ys = sorted(int(y) for y in s["China"])
for c, col in (("China", "#C9A227"), ("India", "#F26419")):
    a.plot(ys, [s[c][str(y)] / 1000 for y in ys], color=col, lw=2.6)
    a.text(ys[-1] + .3, s[c][str(ys[-1])] / 1000 + (6 if c == "India" else -6), c, color=col, fontsize=10.5, family=MONO, weight="bold", va="center")
a.set_title("UK students (thousands)", family=MONO, fontsize=10.5, color=FG, pad=2)
a.set_xticks([ys[0], ys[-1]]); a.set_xticklabels([f"{ys[0]-1}/{str(ys[0])[2:]}", f"{ys[-1]-1}/{str(ys[-1])[2:]}"], fontsize=9.5)
a.tick_params(labelsize=9.5); a.spines[["top", "right"]].set_visible(False); a.set_xlim(ys[0], ys[-1] + 3)
# legend
items = [h for h in cnt.index if h in COL][:12]
for k, h in enumerate(items):
    x = .045 + (k % 6) * .152; y = .14 - (k // 6) * .022
    fig.patches.append(mpatches.Rectangle((x, y - .006), .014, .012, transform=fig.transFigure, color=COL[h], figure=fig))
    fig.text(x + .019, y, f"{NM[h]} {cnt[h]}", family=MONO, fontsize=10.5, color=FG, va="center")
fig.text(.045, .095, "Circles: destinations, sized by how many countries pick them. Stronger colour: a bigger share of the country's students go there.\nDashed: a host without origin data (such as the UAE) could be first. Grey: not ranked. China, the UAE and Singapore do not report origins.",
         family=MONO, fontsize=9.5, color=MUTED, va="top", linespacing=1.45)
fig.text(.045, .045, f"Data: UNESCO Institute for Statistics, UIS data API, release {R['meta']['uis_version']} (CC BY-SA 4.0); HESA Table 28 (CC BY 4.0); Natural Earth.\nGaps filled only between reported years. Analysis and chart: Tristan Hotham, with Python and matplotlib. maps.tristanhotham.com/study-abroad",
         family=MONO, fontsize=9.5, color=MUTED, va="top", linespacing=1.45)
fig.savefig(os.path.join(HERE, "where_students_go.png"), dpi=200, facecolor=CBG)
print("saved")
