"""Step 5: static figures for the blog (release/blog/b_*.png, 1520 px wide), the paper (release/paper/f_*.png) and header.png."""
import os, json
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from figlib import *
from common import *

R = load_json(os.path.join(DATA, "results.json")); V = R["v"]
Y0, Y1 = R["meta"]["first_year"], R["meta"]["last_year"]
TOP = pd.read_csv(os.path.join(DATA, "top_destination.csv"))
NAMES = load_json(os.path.join(DATA, "page.json"))
NM = dict(zip(NAMES["codes"], NAMES["names"]))
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)

def mix(c, t):
    r = np.array(to_rgb(c)); b = np.array(to_rgb(BG)); return tuple(b + (r - b) * t)

def year_map(ax, y, dots=True, labels=True, fs=10):
    g = TOP[TOP.year == y]
    cols = {o: mix(hostcol(h), .5 + .5 * min(1, s / .6)) for o, h, s in zip(g.origin, g.top, g.top_share)}
    draw_world(ax, cols, dashed=set(g[g.uncertain].origin))
    if dots:
        cnt = g.top.value_counts(); mx = cnt.max()
        for h, n in cnt.items():
            c = centroid(h)
            if c is None: continue
            ax.scatter([c[0]], [c[1]], s=30 + 520 * np.sqrt(n / mx) ** 2, color=hostcol(h), edgecolor="white", linewidth=1.4, zorder=5)
            if labels and n >= 3: ax.text(c[0], c[1], str(n), ha="center", va="center", fontsize=fs, color="white", weight="bold", zorder=6)
    return g.top.value_counts()

def legend_row(fig, cnt, x0, y0, w, ncol=6, fs=12):
    items = [(h, n) for h, n in cnt.items() if h in COL][:12]
    for k, (h, n) in enumerate(items):
        cx = x0 + (k % ncol) * w / ncol; cy = y0 - (k // ncol) * 0.045
        fig.patches.append(__import__("matplotlib").patches.Rectangle((cx, cy - .012), .014, .024, transform=fig.transFigure, color=COL[h], figure=fig))
        fig.text(cx + .02, cy, f"{NM[h]} {n}", fontsize=fs, va="center", color=FG)

# 1. headline map, last year
for out, W in ((os.path.join(BL, "b_map.png"), 15.2), (os.path.join(PA, "f_map.png"), 12)):
    fig = plt.figure(figsize=(W, W * .62)); ax = fig.add_axes([0, .13, 1, .87])
    cnt = year_map(ax, Y1, fs=11 if W > 13 else 9)
    legend_row(fig, cnt, .03, .085, .95, fs=13 if W > 13 else 10.5)
    fig.savefig(out, dpi=100 if W > 13 else 200); plt.close(fig)

# 2. four years
fig, axs = plt.subplots(2, 2, figsize=(15.2, 9.6)); fig.subplots_adjust(0.005, 0.01, .995, .95, .02, .1)
for ax, y in zip(axs.flat, [Y0, 2005, 2013, Y1]):
    cnt = year_map(ax, y, fs=8)
    ax.set_title(f"{y}: United States {cnt.get('USA', 0)}, United Kingdom {cnt.get('GBR', 0)}, France {cnt.get('FRA', 0)}", fontsize=13, family=MONO, color=FG)
fig.savefig(os.path.join(BL, "b_years.png"), dpi=100); fig.savefig(os.path.join(PA, "f_years.png"), dpi=150); plt.close(fig)

def lines(ax, series, pct=False, x0=Y0, x1=Y1, lab=True):
    ends = []
    for name, col, pts in series:
        pts = sorted(pts); x = [p[0] for p in pts]; y = [p[1] for p in pts]
        ax.plot(x, y, color=col, lw=2.8)
        if pts: ends.append([y[-1], x[-1], name, col])
    if lab:
        top = max(max(p[1] for p in sorted(se[2])) for se in series); gap = .065 * top; ends.sort(); last = -1e18
        for e in ends:
            e[0] = max(e[0], last + gap); last = e[0]
            ax.text(e[1] + .4, e[0], e[2], color=e[3], fontsize=12, va="center", weight="bold")
    ax.set_xlim(x0, x1 + 5.5); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color=RULE, lw=.8)
    if pct: ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0%}")
    else: ax.yaxis.set_major_formatter(lambda v, p: f"{v/1e6:.1f}m" if v >= 1e6 else f"{v/1e3:.0f}k" if v else "0")

def spread(series, gap):
    """nudge end labels apart"""
    return series

# 3. blocs
B = R["blocs"]
bl = [("francophone_africa", "FRA", "French-official Africa: France", "#7A3DB8"), ("maghreb", "FRA", "Maghreb: France", "#B07CF0"),
      ("central_asia", "RUS", "Central Asia: Russia", "#1B7F4C"), ("lusophone", "PRT", "Lusophone Africa: Portugal", "#0EA5A0"),
      ("anglophone_africa", "GBR", "English-official Africa: UK", "#D62839")]
for out, sz, dpi in ((os.path.join(BL, "b_blocs.png"), (15.2, 7), 100), (os.path.join(PA, "f_blocs.png"), (10, 5), 200)):
    fig, ax = plt.subplots(figsize=sz); fig.subplots_adjust(.07, .08, .7, .97)
    ser = [(n, c, [(int(y), d["share"].get(h, 0)) for y, d in B[k]["by_year"].items()]) for k, h, n, c in bl]
    lines(ax, ser, pct=True, lab=False); ax.set_xlim(Y0, Y1 + .5); ax.set_ylim(0, 1)
    ends = sorted([(s[2][-1][1], s[0], s[1]) for s in ser]); last = -1
    for v, n, c in ends:
        v2 = max(v, last + .055); last = v2
        ax.annotate(n, (Y1, v), (Y1 + .8, v2), color=c, fontsize=12 if sz[0] > 12 else 9.5, weight="bold", va="center", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=c, lw=.8))
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 4. magnets
mg = [("TUR", "Turkey", "#8C1C13"), ("RUS", "Russia", "#1B7F4C"), ("ARE", "UAE", "#5E7C8A"), ("CHN", "China", "#C9A227"),
      ("KOR", "South Korea", "#2349C9"), ("MYS", "Malaysia", "#B5651D"), ("SAU", "Saudi Arabia", "#8DB33A")]
for out, sz, dpi in ((os.path.join(BL, "b_magnets.png"), (15.2, 7), 100), (os.path.join(PA, "f_magnets.png"), (10, 5), 200)):
    fig, ax = plt.subplots(figsize=sz); fig.subplots_adjust(.08, .08, .82, .97)
    ser = [(n, c, [(int(y), v) for y, v in R["inbound"][k].items() if Y0 <= int(y) <= Y1]) for k, n, c in mg]
    lines(ax, ser, lab=False); ax.set_xlim(Y0, Y1 + .5)
    ends = sorted([(max(s[2])[1], s[0], s[1]) for s in ser]); last = -1e9
    for v, n, c in ends:
        v2 = max(v, last + 17000); last = v2
        ax.annotate(n, (Y1, v), (Y1 + .8, v2), color=c, fontsize=12 if sz[0] > 12 else 9.5, weight="bold", va="center", annotation_clip=False, arrowprops=dict(arrowstyle="-", color=c, lw=.8))
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 5. India and China: world outbound and UK (HESA)
uk = R["uk"]["series"]
for out, sz, dpi in ((os.path.join(BL, "b_india_china.png"), (15.2, 6.4), 100), (os.path.join(PA, "f_india_china.png"), (10, 4.4), 200)):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=sz); fig.subplots_adjust(.07, .12, .93, .88, .35)
    lines(a1, [("China", "#C9A227", [(int(y), v) for y, v in R["outbound"]["CHN"].items() if int(y) <= Y1]),
               ("India", "#F26419", [(int(y), v) for y, v in R["outbound"]["IND"].items() if int(y) <= Y1])])
    a1.set_title("Students abroad, all destinations (UNESCO)", fontsize=12 if sz[0] > 12 else 9.5, loc="left")
    yrs = sorted(int(y) for y in uk["China"])
    lines(a2, [("China", "#C9A227", [(y, uk["China"][str(y)]) for y in yrs]), ("India", "#F26419", [(y, uk["India"][str(y)]) for y in yrs]),
               ("Nigeria", "#1B7F4C", [(y, uk["Nigeria"][str(y)]) for y in yrs]), ("Pakistan", "#2349C9", [(y, uk["Pakistan"][str(y)]) for y in yrs])], x0=yrs[0], x1=yrs[-1])
    st = 2 if sz[0] > 12 else 3; a2.set_xticks(yrs[::st]); a2.set_xticklabels([f"{str(y-1)[2:]}/{str(y)[2:]}" for y in yrs[::st]])
    a2.set_title("Students in UK universities (HESA)", fontsize=12 if sz[0] > 12 else 9.5, loc="left")
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 6. UK top origins first vs last
tf = dict(R["uk"]["top_first"]); tl = dict(R["uk"]["top_last"])
cs = [c for c, _ in R["uk"]["top_last"][:12]]
short = lambda c: c.replace(" (Special Administrative Region of China)", "")
for out, sz, dpi in ((os.path.join(BL, "b_uk.png"), (15.2, 7.4), 100), (os.path.join(PA, "f_uk.png"), (10, 5.2), 200)):
    fig, ax = plt.subplots(figsize=sz); fig.subplots_adjust(.17, .09, .97, .95)
    yy = np.arange(len(cs))[::-1]
    ser = R["uk"]["series"]
    H = pd.read_csv(os.path.join(DATA, "uk_providers_domicile.csv.gz")); H = H[(H.level == "all") & (H.year_end == R["uk"]["year_end_first"])]
    hf = H.groupby("dom_country").students.sum()
    v0 = [int(hf.get(c, 0)) for c in cs]
    ax.barh(yy + .2, v0, .4, color="#B9AC9C", label=R["uk"]["first_year"]); ax.barh(yy - .2, [tl[c] for c in cs], .4, color="#2349C9", label=R["uk"]["last_year"])
    ax.set_yticks(yy); ax.set_yticklabels([short(c) for c in cs]); ax.legend(frameon=False, loc="lower right")
    ax.xaxis.set_major_formatter(lambda v, p: f"{v/1e3:.0f}k"); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="x", color=RULE)
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 7. check: UIS vs OECD shares (paper)
oe = pd.read_csv(os.path.join(INTERIM, "oecd_share_dest.csv")); FL = pd.read_csv(os.path.join(DATA, "flows_filled.csv"))
T = pd.read_csv(os.path.join(INTERIM, "uis_totals.csv")); ob = T[T.measure == "outbound"].set_index(["iso3", "year"]).value
u = FL[FL.method == "reported"].merge(oe, on=["host", "origin", "year"]); u["ob"] = [ob.get((o, y), np.nan) for o, y in zip(u.origin, u.year)]
u = u[u.ob > 500]; u["uis"] = 100 * u.students / u.ob
fig, ax = plt.subplots(figsize=(6, 5.4)); fig.subplots_adjust(.13, .12, .97, .97)
ax.scatter(u.share_pct, u.uis.clip(upper=100), s=3, alpha=.25, color="#2349C9", lw=0); ax.plot([0, 100], [0, 100], color=FG, lw=.8)
ax.set_xlabel("OECD share of origin's mobile students (%)"); ax.set_ylabel("UNESCO-based share (%)"); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
fig.savefig(os.path.join(PA, "f_check.png"), dpi=200); plt.close(fig)

# header.png 1200x630
fig = plt.figure(figsize=(12, 6.3)); ax = fig.add_axes([.335, .03, .67, .94])
year_map(ax, Y1, labels=False)
fig.text(.035, .86, "Where would\nyou go to\nuniversity?", fontproperties=DISP, fontsize=37, va="top", color=FG, linespacing=.95)
fig.text(.035, .37, f"Each country coloured by\nits students' number one\nstudy destination, {Y1}.\nUNESCO data, {Y0} to {Y1}.", family=SER, fontsize=14, va="top", color=FG, linespacing=1.3)
fig.text(.035, .06, "maps.tristanhotham.com/study-abroad", fontsize=10, color=MUTED)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100); plt.close(fig)
print("figures done")
