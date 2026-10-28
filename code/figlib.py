"""Shared drawing helpers: fonts, palette, a Robinson world map of countries keyed by ISO3."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection
from pyproj import Transformer
from shapely.geometry import shape
from common import DATA, NE

FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    p = os.path.join(FONT_DIR, f)
    if os.path.exists(p): fm.fontManager.addfont(p)
DISP = fm.FontProperties(fname=os.path.join(FONT_DIR, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG = "#F7F5F0"; FG = "#1C1D24"; MUTED = "#62636E"; RULE = "#DCD7CC"; NODATA = "#ECE8E0"; SEA = "#F7F5F0"
COL = {"USA": "#2349C9", "GBR": "#D62839", "FRA": "#7A3DB8", "AUS": "#F2A900", "RUS": "#1B7F4C", "DEU": "#D81B60",
       "ZAF": "#F26419", "PRT": "#0EA5A0", "ARG": "#5BC0EB", "TUR": "#8C1C13", "SAU": "#8DB33A",
       "MYS": "#B5651D", "JOR": "#5E7C8A", "AUT": "#C084FC", "ITA": "#1E9E5A"}
MUT = ["#B9AC9C", "#A3B5AA", "#B7A9C3", "#C7B59A", "#A9B5C8", "#C3A7A2", "#ABB79B", "#B5B0A2"]
plt.rcParams.update({"font.family": MONO, "font.size": 12, "text.color": FG, "axes.labelcolor": FG, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": RULE, "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})
ROB = Transformer.from_crs("EPSG:4326", "+proj=robin +lon_0=11 +datum=WGS84", always_xy=True)


def proj(lon, lat):
    return ROB.transform(np.asarray(lon, float), np.asarray(lat, float))


def hostcol(h, codes=None):
    if h in COL: return COL[h]
    return MUT[sum(map(ord, h)) % 8]


_P = None
def world_polys(simplify=0.06):
    global _P
    if _P is not None: return _P
    g = json.load(open(os.path.join(NE, "ne_50m_admin_0_countries.geojson"), encoding="utf-8"))
    out = []
    for f in g["features"]:
        p = f["properties"]; iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
        if iso == "ATA": continue
        geom = shape(f["geometry"]).simplify(simplify, preserve_topology=True)
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        rings = []
        for q in polys:
            x, y = np.asarray(q.exterior.coords).T
            px, py = proj(np.where(x < -169, x + 360, x), y)
            if np.ptp(px) > 3e7: continue
            rings.append(np.column_stack([px, py]))
        out.append((iso, rings, (p["LABEL_X"], p["LABEL_Y"])))
    _P = out
    return out


def draw_world(ax, colours, edge="#FFFFFF", lw=0.25, dashed=(), alpha=None):
    """colours: iso -> colour (missing -> NODATA)."""
    polys, fc, ec = [], [], []
    for iso, rings, _ in world_polys():
        for r in rings:
            polys.append(r); fc.append(colours.get(iso, NODATA)); ec.append(edge)
    pc = PolyCollection(polys, facecolors=fc, edgecolors=ec, linewidths=lw)
    if alpha: pc.set_alpha(alpha)
    ax.add_collection(pc)
    d = [r for iso, rings, _ in world_polys() if iso in dashed for r in rings]
    if d: ax.add_collection(PolyCollection(d, facecolors="none", edgecolors=FG, linewidths=0.7, linestyles=(0, (2, 1.5))))
    ax.set_xlim(-1.25e7, 1.62e7); ax.set_ylim(-6.3e6, 8.4e6); ax.set_aspect("equal"); ax.axis("off")


def centroid(iso):
    for i, _, c in world_polys():
        if i == iso: return proj(*c)
    return None
