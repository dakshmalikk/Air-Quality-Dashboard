"""
Pollution & Air Quality Analysis Dashboard
Real-Time Data — Government of India (CPCB)
DVA Project | IPU BCA 6th Semester
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from PIL import Image, ImageTk
import os
import warnings

# Suppress harmless warnings from mplcursors regarding incomplete pick support for Wedges/Bars
warnings.filterwarnings("ignore", category=UserWarning, message=".*Pick support.*")
# ══════════════════════════════════════════════════
#  COLOUR THEME
# ══════════════════════════════════════════════════
BG      = "#0D1117"
CARD    = "#161B22"
CARD2   = "#1C2128"
FG      = "#E6EDF3"
ACCENT  = "#58A6FF"
ACCENT2 = "#79C0FF"
GOOD    = "#3FB950"
WARN    = "#F85149"
MID     = "#D29922"
MUTED   = "#8B949E"
BORDER  = "#30363D"

AQI_COLORS = {
    "Good":                "#3FB950",
    "Satisfactory":        "#56D364",
    "Moderately Polluted": "#D29922",
    "Poor":                "#FFA657",
    "Very Poor":           "#F85149",
    "Severe":              "#BC8CFF",
}

# ── Global matplotlib defaults ───────────────────
# NOTE: do NOT put figure.dpi here – set it per-Figure to avoid Windows DPI issues
# font.family uses a fallback list: Segoe UI for Latin/general text, then
# DejaVu Sans which ships with matplotlib and covers subscript glyphs (₂ ₃)
# and common symbols (⚠ ✓).  Emoji are replaced with plain-text alternatives
# below to avoid missing-glyph boxes on any platform.
mpl.rcParams.update({
    "font.family":      "sans-serif",
    "font.sans-serif":  ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"],
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.labelsize":   11,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
    "legend.fontsize":  10,
    "figure.facecolor": BG,
    "axes.facecolor":   CARD,
    "axes.edgecolor":   BORDER,
    "axes.labelcolor":  MUTED,
    "xtick.color":      FG,
    "ytick.color":      FG,
    "text.color":       FG,
    "grid.color":       BORDER,
    "grid.linewidth":   0.5,
})

DPI = 100   # consistent, avoids Windows high-DPI distortion

# ══════════════════════════════════════════════════
#  DATA PREP
# ══════════════════════════════════════════════════
FILE_PATH = "Real_Time_GOV_Of_India_AQI.csv"

def pm25_to_aqi(pm):
    if pd.isna(pm): return np.nan
    bp = [(0,30,0,50),(30,60,51,100),(60,90,101,200),
          (90,120,201,300),(120,250,301,400),(250,500,401,500)]
    for lo, hi, alo, ahi in bp:
        if lo <= pm <= hi:
            return round(((ahi-alo)/(hi-lo))*(pm-lo)+alo)
    return 500

def aqi_category(aqi):
    if pd.isna(aqi):  return "Unknown"
    if aqi <= 50:     return "Good"
    if aqi <= 100:    return "Satisfactory"
    if aqi <= 200:    return "Moderately Polluted"
    if aqi <= 300:    return "Poor"
    if aqi <= 400:    return "Very Poor"
    return "Severe"

def aqi_color(aqi):
    if pd.isna(aqi): return MUTED
    if aqi <= 50:    return "#3FB950"
    if aqi <= 100:   return "#56D364"
    if aqi <= 200:   return "#D29922"
    if aqi <= 300:   return "#FFA657"
    if aqi <= 400:   return "#F85149"
    return "#BC8CFF"

def load_data():
    try:
        import urllib.request
        import json
        # Fetch live data using the provided API key
        url = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69?api-key=579b464db66ec23bdd000001a543ae981efc4582423d659393a0949f&format=json&limit=10000"
        req = urllib.request.urlopen(url, timeout=15)
        data = json.loads(req.read().decode('utf-8'))
        raw = pd.DataFrame(data['records'])
        
        # Rename API keys to match what the dashboard expects
        rename_map = {
            "min_value": "pollutant_min",
            "max_value": "pollutant_max",
            "avg_value": "pollutant_avg"
        }
        raw.rename(columns=rename_map, inplace=True)
        
        # Ensure correct datatypes
        raw["pollutant_avg"] = pd.to_numeric(raw["pollutant_avg"], errors="coerce")
        raw["pollutant_max"] = pd.to_numeric(raw["pollutant_max"], errors="coerce")
        raw["pollutant_min"] = pd.to_numeric(raw["pollutant_min"], errors="coerce")

        # Save to CSV as cache for offline use
        raw.to_csv(FILE_PATH, index=False)
        print("Successfully fetched live data and updated local CSV.")
    except Exception as e:
        print(f"Failed to fetch live data ({e}). Loading from static CSV fallback.")
        raw = pd.read_csv(FILE_PATH)

    raw.columns = [c.strip().lower() for c in raw.columns]
    wide = raw.pivot_table(
        index=["state","city"], columns="pollutant_id",
        values="pollutant_avg", aggfunc="mean"
    ).reset_index()
    wide.columns.name = None
    wide.columns = [c.lower().replace(".","").replace("-","").replace(" ","_")
                    for c in wide.columns]
    wide["aqi"]      = wide["pm25"].apply(pm25_to_aqi) if "pm25" in wide.columns else np.nan
    wide["category"] = wide["aqi"].apply(aqi_category)
    wide["state"]    = wide["state"].str.replace("_"," ").str.title()
    raw["state"]     = raw["state"].str.replace("_"," ").str.title()
    raw["last_update"] = pd.to_datetime(raw["last_update"],
                                        format="%d-%m-%Y %H:%M:%S", errors="coerce")
    return wide, raw

# ══════════════════════════════════════════════════
#  LOGO LOADER
# ══════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_logo(filename, size):
    try:
        img = Image.open(os.path.join(BASE_DIR, filename)).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[logo] {filename}: {e}")
        return None

# ══════════════════════════════════════════════════
#  CHART HELPERS
# ══════════════════════════════════════════════════
FONT_KPI_TITLE = ("Segoe UI", 10, "bold")
FONT_KPI_VAL   = ("Segoe UI", 16, "bold")
FONT_KPI_SUB   = ("Segoe UI", 9)
FONT_TABLE     = ("Segoe UI", 10)
FONT_THEAD     = ("Segoe UI", 10, "bold")

def kpi_card(parent, title, value, sub="", color=FG):
    f = tk.Frame(parent, bg=CARD, padx=12, pady=7,
                 highlightbackground=BORDER, highlightthickness=1)
    f.pack(fill="x", pady=4)
    tk.Label(f, text=title, bg=CARD, fg=MUTED,   font=FONT_KPI_TITLE).pack(anchor="w")
    tk.Label(f, text=value, bg=CARD, fg=color,   font=FONT_KPI_VAL).pack(anchor="w", pady=(0, 2))
    if sub:
        tk.Label(f, text=sub, bg=CARD, fg=ACCENT2, font=FONT_KPI_SUB).pack(anchor="w")

def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    # NOTE: do NOT pass colors= here — it would reset labelrotation
    ax.tick_params(axis="x", colors=FG)
    ax.tick_params(axis="y", colors=FG)
    if title:
        ax.set_title(title, color=ACCENT2, fontsize=13, fontweight="bold", pad=10)
    if xlabel: ax.set_xlabel(xlabel, color=MUTED, fontsize=11)
    if ylabel: ax.set_ylabel(ylabel, color=MUTED, fontsize=11)

def fix_yticks(ax, fontsize=11):
    """Force y-axis labels horizontal via tick_params — persists through all canvas redraws.
    
    IMPORTANT: ax.get_yticklabels() returns ghost objects before draw() and must NOT
    be used for rotation. tick_params(labelrotation=0) sets the property on the Axis
    itself and is the only reliable API.
    """
    ax.tick_params(
        axis="y",
        labelrotation=0,    # labelrotation, not rotation — persists through redraws
        labelsize=fontsize,
        colors=FG,
    )

def trunc(name, maxlen=11):
    """Shorten long city/state names to avoid chart overflow."""
    s = str(name)
    return s if len(s) <= maxlen else s[:maxlen - 1] + "…"

def _cell_txt_color(cmap, norm_val):
    """Return 'black' or 'white' for readable text over a colormap cell.
    Uses perceived luminance (ITU-R BT.601) of the cell fill colour.
    """
    import numpy as np
    if norm_val is None or (isinstance(norm_val, float) and np.isnan(norm_val)):
        return FG
    rgba = cmap(float(norm_val))
    lum  = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
    return "black" if lum > 0.50 else "white"

def hbar(ax, labels, values, colors, fontsize=11, bar_h=0.68, val_labels=True):
    """Draw a horizontal bar chart with guaranteed horizontal y labels."""
    bars = ax.barh(labels, values, color=colors, height=bar_h)
    if val_labels:
        ax.bar_label(bars, fmt="%.0f", color=FG, fontsize=fontsize - 1, padding=4)
    fix_yticks(ax, fontsize=fontsize)
    ax.tick_params(axis="x", labelsize=fontsize - 1, colors=FG)
    
    try:
        import mplcursors
        cursor = mplcursors.cursor(bars, hover=2)
        lbl_list = list(labels)
        val_list = list(values)
        @cursor.connect("add")
        def on_add(sel):
            # sel.index works perfectly for BarContainers in mplcursors
            idx = int(sel.index)
            sel.annotation.set_text(f"{lbl_list[idx]}\nValue: {val_list[idx]:.1f}")
            sel.annotation.get_bbox_patch().set(boxstyle="round,pad=0.3", fc=CARD, ec=BORDER, alpha=0.95)
            sel.annotation.set_color(FG)
            sel.annotation.set_fontsize(10)
    except Exception:
        pass
        
    return bars

def embed(fig, parent):
    c = FigureCanvasTkAgg(fig, master=parent)
    c.draw()
    c.get_tk_widget().pack(fill="both", expand=True)

def embed_scrollable(fig, parent, bg=BG):
    """Embed a matplotlib figure in a scrollable Tk canvas.

    Unlike embed(), the figure canvas is placed inside a tk.Canvas with a
    scrollbar so Tkinter CANNOT squish/resize it.  The figure renders at its
    native pixel size (figsize × dpi) and the user scrolls to see it all.
    This is the ONLY reliable way to display tall charts without crowding.
    """
    fig_h_px = int(fig.get_figheight() * fig.get_dpi())
    fig_w_px = int(fig.get_figwidth()  * fig.get_dpi())

    outer = tk.Frame(parent, bg=bg)
    outer.pack(fill="both", expand=True)

    vbar = ttk.Scrollbar(outer, orient="vertical")
    vbar.pack(side="right", fill="y")
    
    hbar = ttk.Scrollbar(outer, orient="horizontal")
    hbar.pack(side="bottom", fill="x")

    sc = tk.Canvas(outer, bg=bg, highlightthickness=0, yscrollcommand=vbar.set, xscrollcommand=hbar.set)
    sc.pack(side="left", fill="both", expand=True)
    
    vbar.config(command=sc.yview)
    hbar.config(command=sc.xview)

    mpl_c = FigureCanvasTkAgg(fig, master=sc)
    mpl_c.draw()
    widget = mpl_c.get_tk_widget()
    # explicitly set bg just in case
    widget.configure(bg=bg, highlightthickness=0)
    win_id = sc.create_window((0, 0), window=widget, anchor="nw")

    def _update_scroll(event=None):
        sc.configure(scrollregion=sc.bbox("all"))

    def _resize(event):
        req_w = widget.winfo_reqwidth()
        req_h = widget.winfo_reqheight()
        sc.itemconfig(win_id, width=max(event.width, req_w), height=max(event.height, req_h))
        sc.configure(scrollregion=sc.bbox("all"))

    widget.bind("<Configure>", _update_scroll)
    sc.bind("<Configure>", _resize)
    
    sc.bind("<MouseWheel>", lambda e: sc.yview_scroll(int(-1 * (e.delta / 120)), "units"))
    sc.bind("<Shift-MouseWheel>", lambda e: sc.xview_scroll(int(-1 * (e.delta / 120)), "units"))
    
    return mpl_c

def page_header(parent, title, subtitle=""):
    tk.Label(parent, text=title,    bg=BG, fg=FG,   font=("Segoe UI", 20, "bold")
             ).pack(anchor="w", padx=22, pady=(18, 2))
    if subtitle:
        tk.Label(parent, text=subtitle, bg=BG, fg=MUTED, font=("Segoe UI", 11)
                 ).pack(anchor="w", padx=22, pady=(0, 8))

# ══════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════
def build_dashboard(root, wide, raw, refresh_callback=None):
    root.title("India Air Quality Dashboard — Real-Time CPCB Data")
    root.configure(bg=BG)
    root.state("zoomed")

    update_time = (raw["last_update"].dropna().max().strftime("%d %b %Y, %H:%M")
                   if not raw["last_update"].dropna().empty else "—")
    valid = wide.dropna(subset=["aqi"])

    # ── LOGOS ───────────────────────────────────────
    _earth = load_logo("Earth Pollution Pattern.jpg", (80, 80))
    _cpcb  = load_logo("3840px-Logo_of_the_Central_Pollution_Control_Board.svg.png", (80, 80))

    # ── HEADER ──────────────────────────────────────
    hdr = tk.Frame(root, bg=BG); hdr.pack(fill="x", padx=22, pady=(14, 4))

    lh = tk.Frame(hdr, bg=BG); lh.pack(side="left", fill="y")
    if _earth:
        w = tk.Label(lh, image=_earth, bg=BG); w.image = _earth
        w.pack(side="left", padx=(0, 14))
    tf = tk.Frame(lh, bg=BG); tf.pack(side="left", anchor="center")
    tk.Label(tf, text="India Air Quality Analysis Dashboard",
             bg=BG, fg=FG, font=("Segoe UI", 22, "bold")).pack(anchor="w")
    tk.Label(tf, bg=BG, fg=MUTED, font=("Segoe UI", 11),
             text=(f"Real-Time CPCB Data  ·  {valid['city'].nunique()} Cities  ·  "
                   f"{valid['state'].nunique()} States  ·  Updated: {update_time}")
             ).pack(anchor="w")

    rh = tk.Frame(hdr, bg=BG); rh.pack(side="right", fill="y")
    rl = tk.Frame(rh,  bg=BG); rl.pack(anchor="e")
    if _cpcb:
        w2 = tk.Label(rl, image=_cpcb, bg=BG); w2.image = _cpcb
        w2.pack(side="right", padx=(12, 0))
    rt = tk.Frame(rl, bg=BG); rt.pack(side="right", anchor="center")
    tk.Label(rt, text="CPCB · GOV OF INDIA", bg=BG, fg=ACCENT,
             font=("Segoe UI", 11, "bold")).pack(anchor="e")
    tk.Label(rt, text="DVA | IPU BCA 6th Sem", bg=BG, fg=MUTED,
             font=("Segoe UI", 10)).pack(anchor="e")
             
    if refresh_callback:
        btn_refresh = tk.Button(rt, text="⟳ Refresh Data", bg=CARD, fg=FG, font=("Segoe UI", 9, "bold"),
                                relief="flat", activebackground=ACCENT, activeforeground=BG,
                                cursor="hand2", padx=10, pady=2)
        btn_refresh.config(command=lambda: refresh_callback(btn_refresh))
        btn_refresh.pack(anchor="e", pady=(6, 0))

    ttk.Separator(root, orient="horizontal").pack(fill="x", padx=16, pady=(8, 0))

    # ── NOTEBOOK ────────────────────────────────────
    st = ttk.Style(); st.theme_use("default")
    st.configure("TNotebook",     background=BG, borderwidth=0)
    st.configure("TNotebook.Tab", background=CARD, foreground=FG,
                 padding=(28, 11), font=("Segoe UI", 11, "bold"))
    st.map("TNotebook.Tab",
           background=[("selected", ACCENT)], foreground=[("selected", BG)])
    nb = ttk.Notebook(root, style="TNotebook")
    nb.pack(fill="both", expand=True, padx=14, pady=10)

    # ══════════════════════════════════════════════════════════
    # PAGE 1 LAYOUT
    #   LEFT  col: KPI sidebar (fixed 260px) + 3 mini charts below
    #   RIGHT col: full-height scrollable state-wise AQI bar
    # ══════════════════════════════════════════════════════════
    p1    = tk.Frame(nb, bg=BG); nb.add(p1, text="  Overview  ")
    body1 = tk.Frame(p1, bg=BG); body1.pack(fill="both", expand=True)

    # ── LEFT column ─────────────────────────────────────────
    left1 = tk.Frame(body1, bg=BG, width=310)
    left1.pack(side="left", fill="y", padx=(10, 6), pady=10)

    avg_aqi    = valid["aqi"].mean()
    worst_city = valid.loc[valid["aqi"].idxmax(), "city"]
    best_city  = valid.loc[valid["aqi"].idxmin(), "city"]
    worst_st   = valid.groupby("state")["aqi"].mean().idxmax()
    best_st    = valid.groupby("state")["aqi"].mean().idxmin()
    severe_pct = (valid["category"].isin(["Very Poor","Severe"])).mean()*100
    good_pct   = (valid["category"] == "Good").mean()*100

    # KPI cards — pure vertical stack exactly like the example dashboard
    left1.pack_propagate(False) # strictly fix the width to 310
    for title, val, sub, c in [
        ("National Avg",  f"{avg_aqi:.0f}",  aqi_category(avg_aqi), aqi_color(avg_aqi)),
        ("Stations",      str(raw["station"].nunique()), "Monitored", ACCENT),
        ("Worst City",    worst_city,        f"AQI {valid['aqi'].max():.0f}", WARN),
        ("Clean City",    best_city,         f"AQI {valid['aqi'].min():.0f}", GOOD),
        ("Worst State",   worst_st,          "", WARN),
        ("Clean State",   best_st,           "", GOOD)
    ]:
        card = tk.Frame(left1, bg=CARD, padx=14, pady=8)
        card.pack(fill="x", pady=4)
        tk.Label(card, text=title, bg=CARD, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(card, text=val, bg=CARD, fg=c, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        if sub: tk.Label(card, text=sub, bg=CARD, fg=MID, font=("Segoe UI", 8)).pack(anchor="w")

    # ── RIGHT column: 2x2 Dashboard Grid ─────────────
    right1 = tk.Frame(body1, bg=BG)
    right1.pack(side="left", fill="both", expand=True, padx=(10, 20), pady=10)

    fig1 = Figure(figsize=(10.5, 5.5), dpi=DPI)
    fig1.patch.set_facecolor(BG)
    gs1  = GridSpec(2, 2, figure=fig1, hspace=0.35, wspace=0.25)

    # 1a: Top 10 Worst States (Takes up the Top Left cell)
    ax_st = fig1.add_subplot(gs1[0, 0])
    ax_st.set_facecolor(CARD)
    st_aqi = valid.groupby("state")["aqi"].mean().sort_values(ascending=False).head(10)
    hbar(ax_st, st_aqi.index, st_aqi.values, [aqi_color(v) for v in st_aqi.values], fontsize=9, bar_h=0.55, val_labels=False)
    ax_st.axvline(100, color=MUTED, lw=1.3, ls="--", label="Safe (100)")
    ax_st.legend(loc="lower right", fontsize=8, labelcolor=FG, facecolor=CARD, edgecolor=BORDER)
    style_ax(ax_st, "Top 10 Most Polluted States", "AQI")

    # 1b: AQI Donut Chart (Takes up the Bottom Left cell)
    ax_donut = fig1.add_subplot(gs1[1, 0])
    cat_cnt = valid["category"].value_counts()
    clrs    = [AQI_COLORS.get(c, ACCENT) for c in cat_cnt.index]
    wedges, _, autotexts = ax_donut.pie(
        cat_cnt.values, colors=clrs,
        autopct=lambda pct: f"{pct:.0f}%" if pct >= 5 else "", pctdistance=0.75,
        startangle=90, wedgeprops=dict(width=0.45, edgecolor=BG, linewidth=2.5),
        radius=0.80
    )
    
    try:
        import mplcursors
        cursor_pie1 = mplcursors.cursor(wedges, hover=2)
        names = list(cat_cnt.index)
        vals  = list(cat_cnt.values)
        @cursor_pie1.connect("add")
        def on_add_pie1(sel):
            sel.annotation.set_text(f"{names[int(sel.index)]}\n{vals[int(sel.index)]} Cities")
            sel.annotation.get_bbox_patch().set(boxstyle="round,pad=0.3", fc=CARD, ec=BORDER, alpha=0.95)
            sel.annotation.set_color(FG)
    except Exception:
        pass
    for at, wdg in zip(autotexts, wedges):
        fc  = wdg.get_facecolor()
        lum = 0.299*fc[0] + 0.587*fc[1] + 0.114*fc[2]
        at.set_fontsize(9)
        at.set_fontweight("bold")
        at.set_color("black" if lum > 0.50 else "white")
    ax_donut.legend(
        wedges, [f"{cat} ({cnt})" for cat, cnt in cat_cnt.items()],
        loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
        fontsize=8, labelcolor=FG, facecolor=CARD, edgecolor=BORDER, framealpha=0.9
    )
    ax_donut.set_title("AQI Distribution", color=ACCENT2, fontsize=11, fontweight="bold", pad=8)

    # 1c: Top 5 Polluted Cities (Top Right)
    ax_pol = fig1.add_subplot(gs1[0, 1])
    t5p = valid.nlargest(5, "aqi").sort_values("aqi")
    hbar(ax_pol, t5p["city"].map(trunc), t5p["aqi"], [aqi_color(v) for v in t5p["aqi"]], fontsize=9, bar_h=0.60)
    ax_pol.axvline(200, color=MID, lw=1.4, ls="--", label="Poor 200")
    ax_pol.legend(loc="lower right", fontsize=8, labelcolor=FG, facecolor=CARD, edgecolor=BORDER)
    style_ax(ax_pol, "Top 5 Most Polluted Cities", "AQI")
    fix_yticks(ax_pol, fontsize=9)

    # 1d: Top 5 Cleanest Cities (Bottom Right)
    ax_clean = fig1.add_subplot(gs1[1, 1])
    t5c = valid.nsmallest(5, "aqi").sort_values("aqi", ascending=False)
    hbar(ax_clean, t5c["city"].map(trunc), t5c["aqi"], [aqi_color(v) for v in t5c["aqi"]], fontsize=9, bar_h=0.60)
    style_ax(ax_clean, "Top 5 Cleanest Cities", "AQI")
    fix_yticks(ax_clean, fontsize=9)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        fig1.tight_layout(pad=1.5, w_pad=3.0, h_pad=3.0, rect=[0, 0.15, 1, 1])
    embed(fig1, right1)

    # ════════════════════════════════════════════════
    # PAGE 2 — State Analysis
    # ════════════════════════════════════════════════
    p2 = tk.Frame(nb, bg=BG); nb.add(p2, text="  State Analysis  ")
    page_header(p2,
                "State-wise Air Quality Performance",
                "Aggregated AQI and pollutant averages per state")

    body2 = tk.Frame(p2, bg=BG); body2.pack(fill="both", expand=True, padx=18, pady=6)

    # Scrollable table
    tbl_frame = tk.Frame(body2, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    tbl_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))

    tbl_canvas = tk.Canvas(tbl_frame, bg=CARD, highlightthickness=0, width=800)
    tbl_vscroll = ttk.Scrollbar(tbl_frame, orient="vertical", command=tbl_canvas.yview)
    tbl_hscroll = ttk.Scrollbar(tbl_frame, orient="horizontal", command=tbl_canvas.xview)
    tbl_vscroll.pack(side="right", fill="y")
    tbl_hscroll.pack(side="bottom", fill="x")
    tbl_canvas.pack(side="left", fill="both", expand=True)
    tbl_canvas.configure(yscrollcommand=tbl_vscroll.set, xscrollcommand=tbl_hscroll.set)

    tbl_inner = tk.Frame(tbl_canvas, bg=CARD)
    tbl_win   = tbl_canvas.create_window((0,0), window=tbl_inner, anchor="nw")
    tbl_inner.bind("<Configure>", lambda e: tbl_canvas.configure(scrollregion=tbl_canvas.bbox("all")))
    tbl_canvas.bind("<Configure>", lambda e: tbl_canvas.itemconfig(tbl_win, width=max(e.width, tbl_inner.winfo_reqwidth())))

    st_df = valid.groupby("state").agg(
        cities=("city","count"), avg_aqi=("aqi","mean"),
        avg_pm25=("pm25","mean"), avg_pm10=("pm10","mean"), avg_no2=("no2","mean")
    ).reset_index().sort_values("avg_aqi", ascending=False)
    st_df["category"] = st_df["avg_aqi"].apply(aqi_category)

    hdrs2 = ["STATE","CITIES","Avg AQI","PM2.5","PM10","NO₂","STATUS"]
    cw2   = [26, 9, 12, 12, 12, 12, 24]
    for i in range(len(cw2)): tbl_inner.columnconfigure(i, weight=(2 if i==0 else 1))
    for i, (h, w) in enumerate(zip(hdrs2, cw2)):
        tk.Label(tbl_inner, text=h, bg=CARD2, fg=ACCENT2,
                 font=FONT_THEAD, width=w, anchor="w"
                 ).grid(row=0, column=i, padx=14, pady=13, sticky="we")

    for idx, (_, row) in enumerate(st_df.iterrows(), 1):
        cbg = CARD2 if idx%2==0 else CARD
        vals = [row["state"], int(row["cities"]),
                f"{row['avg_aqi']:.0f}",
                f"{row['avg_pm25']:.1f}" if not pd.isna(row["avg_pm25"]) else "—",
                f"{row['avg_pm10']:.1f}" if not pd.isna(row["avg_pm10"]) else "—",
                f"{row['avg_no2']:.1f}"  if not pd.isna(row["avg_no2"])  else "—",
                row["category"]]
        for c, (val, w) in enumerate(zip(vals, cw2)):
            col = (aqi_color(float(str(val))) if c==2
                   else AQI_COLORS.get(str(val), FG) if c==6
                   else MUTED if c==1 else FG)
            tk.Label(tbl_inner, text=val, bg=cbg, fg=col,
                     font=FONT_TABLE, width=w, anchor="w"
                     ).grid(row=idx, column=c, padx=14, pady=11, sticky="we")

    # Right panel — 2×2 summary charts (no duplicate state bar)
    ch2 = tk.Frame(body2, bg=BG)
    ch2.pack(side="left", fill="both", expand=True)

    fig2 = Figure(figsize=(8.5, 6.0), dpi=DPI)
    fig2.patch.set_facecolor(BG)
    gs2  = GridSpec(2, 2, figure=fig2, hspace=0.65, wspace=0.46)

    # 2a — Top 10 Most Polluted Cities
    ax2a = fig2.add_subplot(gs2[0, 0])
    t10p2 = valid.nlargest(10, "aqi").sort_values("aqi")
    hbar(ax2a, t10p2["city"].map(trunc), t10p2["aqi"],
         [aqi_color(v) for v in t10p2["aqi"]], fontsize=8, bar_h=0.60, val_labels=False)
    ax2a.axvline(200, color=MID, lw=1.2, ls="--", label="Poor (200)")
    ax2a.legend(fontsize=7.5, labelcolor=FG, facecolor=CARD, edgecolor=BORDER)
    ax2a.set_title("Top 10 Most Polluted Cities", color=ACCENT2, fontsize=10, fontweight="bold", pad=6)
    fix_yticks(ax2a, fontsize=8)

    # 2b — Top 10 Cleanest Cities
    ax2b = fig2.add_subplot(gs2[0, 1])
    t10c2 = valid.nsmallest(10, "aqi").sort_values("aqi", ascending=False)
    hbar(ax2b, t10c2["city"].map(trunc), t10c2["aqi"],
         [aqi_color(v) for v in t10c2["aqi"]], fontsize=8, bar_h=0.60, val_labels=False)
    ax2b.set_title("Top 10 Cleanest Cities", color=ACCENT2, fontsize=10, fontweight="bold", pad=6)
    fix_yticks(ax2b, fontsize=8)

    # 2c — AQI Category Donut
    ax2c = fig2.add_subplot(gs2[1, 0])
    cat_cnt2 = valid["category"].value_counts()
    clrs2    = [AQI_COLORS.get(c, ACCENT) for c in cat_cnt2.index]
    def _autopct2(pct):
        return f"{pct:.0f}%" if pct >= 5 else ""
    wedges2, _, autotexts2 = ax2c.pie(
        cat_cnt2.values, colors=clrs2,
        autopct=_autopct2, pctdistance=0.75,
        startangle=90,
        wedgeprops=dict(width=0.45, edgecolor=BG, linewidth=2.0),
        radius=0.80
    )
    
    try:
        import mplcursors
        cursor_pie2 = mplcursors.cursor(wedges2, hover=2)
        names2 = list(cat_cnt2.index)
        vals2  = list(cat_cnt2.values)
        @cursor_pie2.connect("add")
        def on_add_pie2(sel):
            sel.annotation.set_text(f"{names2[int(sel.index)]}\n{vals2[int(sel.index)]} Cities")
            sel.annotation.get_bbox_patch().set(boxstyle="round,pad=0.3", fc=CARD, ec=BORDER, alpha=0.95)
            sel.annotation.set_color(FG)
    except Exception:
        pass
    for at2, wdg2 in zip(autotexts2, wedges2):
        fc2  = wdg2.get_facecolor()
        lum2 = 0.299*fc2[0] + 0.587*fc2[1] + 0.114*fc2[2]
        at2.set_fontsize(8.5); at2.set_fontweight("bold")
        at2.set_color("black" if lum2 > 0.50 else "white")
    ax2c.legend(wedges2,
        [f"{cat}  ({cnt})" for cat, cnt in cat_cnt2.items()],
        loc="upper center", bbox_to_anchor=(0.5, 0.0),
        fontsize=8, labelcolor=FG, facecolor=CARD,
        edgecolor=BORDER, ncol=2, framealpha=0.9)
    ax2c.set_facecolor(CARD)
    ax2c.set_title("AQI Category Distribution", color=ACCENT2, fontsize=10, fontweight="bold", pad=6)

    # 2d — Top 10 States by Avg PM2.5
    ax2d = fig2.add_subplot(gs2[1, 1])
    if "pm25" in wide.columns:
        pm_st = (wide.dropna(subset=["pm25"])
                     .groupby("state")["pm25"].mean()
                     .sort_values(ascending=True)
                     .tail(10))
        hbar(ax2d, pm_st.index, pm_st.values,
             [WARN if v > 15 else GOOD for v in pm_st.values],
             fontsize=8, bar_h=0.60, val_labels=False)
        ax2d.axvline(15, color=MID, lw=1.2, ls="--", label="WHO limit 15")
        ax2d.legend(fontsize=7.5, labelcolor=FG, facecolor=CARD, edgecolor=BORDER)
    else:
        ax2d.text(0.5, 0.5, "No PM2.5 data", ha="center", va="center",
                  color=MUTED, fontsize=10)
    ax2d.set_title("Top 10 States — PM2.5 (µg/m³)", color=ACCENT2, fontsize=10, fontweight="bold", pad=6)
    fix_yticks(ax2d, fontsize=8)

    fig2.subplots_adjust(left=0.22, right=0.97, top=0.94, bottom=0.15, hspace=0.65, wspace=0.46)
    embed(fig2, ch2)

    # ════════════════════════════════════════════════
    # PAGE 3 — Pollutants (2×4 grid, top 10 states each)
    # ════════════════════════════════════════════════
    p3 = tk.Frame(nb, bg=BG); nb.add(p3, text="  Pollutants  ")
    page_header(p3,
                "Pollutant Concentrations vs Safe Limits",
                "Red = exceeds WHO/CPCB limit  ·  Green = within safe limit  ·  Dashed line = safe limit")

    poll_list = [
        ("pm25",  "PM2.5  (µg/m³)", 15),
        ("pm10",  "PM10   (µg/m³)", 45),
        ("no2",   "NO₂    (µg/m³)", 40),
        ("so2",   "SO₂    (µg/m³)", 40),
    ]

    fig3 = Figure(figsize=(9.0, 5.5), dpi=DPI)
    fig3.patch.set_facecolor(BG)
    gs3  = GridSpec(2, 2, figure=fig3)
    positions = [(0,0),(0,1),(1,0),(1,1)]

    for (r, cp), (pol, lbl, limit) in zip(positions, poll_list):
        ax = fig3.add_subplot(gs3[r, cp])
        title_short = lbl.strip()
        if pol not in wide.columns:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color=MUTED, fontsize=8)
            ax.set_title(title_short, color=ACCENT2, fontsize=9, fontweight="bold", pad=2)
            continue

        # Only top 5 states — fewer rows = bars never overflow the axes vertically
        data = (wide.dropna(subset=[pol])
                    .groupby("state")[pol].mean()
                    .sort_values(ascending=False)
                    .head(5))

        hbar(ax, data.index.map(lambda x: trunc(x, 12)), data.values,
             [WARN if v > limit else GOOD for v in data.values],
             fontsize=8, bar_h=0.40, val_labels=False)
        ax.axvline(limit, color=MID, ls="--", lw=1.2, label=f"Safe:{limit}")
        ax.legend(fontsize=7, labelcolor=FG, facecolor=CARD, edgecolor=BORDER,
                  handlelength=1.2, borderpad=0.4)
        ax.tick_params(axis="x", labelsize=7)
        ax.set_title(title_short, color=ACCENT2, fontsize=9, fontweight="bold", pad=3)
        fix_yticks(ax, fontsize=8)

    fig3.tight_layout(pad=2.0)
    embed(fig3, p3)

    # ════════════════════════════════════════════════
    # PAGE 4 — City Rankings (scrollable table + 2 charts)
    # ════════════════════════════════════════════════
    p4 = tk.Frame(nb, bg=BG); nb.add(p4, text="  City Rankings  ")
    page_header(p4,
                f"City-level AQI Rankings — {len(valid)} Cities",
                "Sorted by AQI descending  ·  Scroll to browse all cities")

    outer4 = tk.Frame(p4, bg=BG); outer4.pack(fill="both", expand=True, padx=18, pady=6)

    frm_l = tk.Frame(outer4, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    frm_l.pack(side="left", fill="both", expand=True, padx=(0, 12))

    sc_canvas = tk.Canvas(frm_l, bg=CARD, highlightthickness=0, width=780)
    vscroll   = ttk.Scrollbar(frm_l, orient="vertical", command=sc_canvas.yview)
    hscroll   = ttk.Scrollbar(frm_l, orient="horizontal", command=sc_canvas.xview)
    vscroll.pack(side="right", fill="y")
    hscroll.pack(side="bottom", fill="x")
    sc_canvas.pack(side="left", fill="both", expand=True)
    sc_canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

    inner  = tk.Frame(sc_canvas, bg=CARD)
    win_id = sc_canvas.create_window((0,0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: sc_canvas.configure(scrollregion=sc_canvas.bbox("all")))
    sc_canvas.bind("<Configure>", lambda e: sc_canvas.itemconfig(win_id, width=max(e.width, inner.winfo_reqwidth())))
    sc_canvas.bind_all("<MouseWheel>",
                       lambda e: sc_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

    city_sorted = valid.sort_values("aqi", ascending=False).reset_index(drop=True)
    hdrs4 = ["#","CITY","STATE","AQI","PM2.5","PM10","NO₂","CATEGORY"]
    cw4   = [5, 22, 22, 9, 9, 9, 9, 24]
    for i in range(len(cw4)): inner.columnconfigure(i, weight=(2 if i in [1,2] else 1))

    for i, (h, w) in enumerate(zip(hdrs4, cw4)):
        tk.Label(inner, text=h, bg=CARD2, fg=ACCENT2,
                 font=FONT_THEAD, width=w, anchor="w"
                 ).grid(row=0, column=i, padx=12, pady=12, sticky="we")

    for r, row in city_sorted.iterrows():
        rank   = r+1; cbg = CARD2 if rank%2==0 else CARD
        pm25_v = f"{row['pm25']:.0f}" if not pd.isna(row.get("pm25", np.nan)) else "—"
        pm10_v = f"{row['pm10']:.0f}" if not pd.isna(row.get("pm10", np.nan)) else "—"
        no2_v  = f"{row['no2']:.0f}"  if not pd.isna(row.get("no2",  np.nan)) else "—"
        vals   = [rank, row["city"], row["state"],
                  f"{row['aqi']:.0f}" if not pd.isna(row["aqi"]) else "—",
                  pm25_v, pm10_v, no2_v, row["category"]]
        for c, (val, w) in enumerate(zip(vals, cw4)):
            col = (aqi_color(float(str(val))) if c==3 and str(val)!="—"
                   else AQI_COLORS.get(str(val), FG) if c==7
                   else MUTED if c==0 else FG)
            tk.Label(inner, text=val, bg=cbg, fg=col,
                     font=FONT_TABLE, width=w, anchor="w"
                     ).grid(row=rank, column=c, padx=12, pady=10, sticky="we")

    # Right: top10 / bottom10 — 10 items each = very readable
    frm_r = tk.Frame(outer4, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    frm_r.pack(side="left", fill="both", expand=True)

    fig4 = Figure(figsize=(6.8, 6.0), dpi=DPI)
    fig4.patch.set_facecolor(CARD)
    ax4a = fig4.add_subplot(211); ax4a.set_facecolor(CARD)
    t10  = city_sorted.head(10).sort_values("aqi")
    hbar(ax4a, t10["city"].map(trunc), t10["aqi"], [aqi_color(v) for v in t10["aqi"]], fontsize=9, bar_h=0.60, val_labels=False)
    ax4a.set_title("[HIGH]  Top 10 Most Polluted", color=ACCENT2, fontsize=10, fontweight="bold", pad=6)
    fix_yticks(ax4a, fontsize=9)

    ax4b = fig4.add_subplot(212); ax4b.set_facecolor(CARD)
    b10  = city_sorted.tail(10).sort_values("aqi", ascending=False)
    hbar(ax4b, b10["city"].map(trunc), b10["aqi"], [aqi_color(v) for v in b10["aqi"]], fontsize=9, bar_h=0.60, val_labels=False)
    ax4b.set_title("[LOW]  Top 10 Cleanest", color=ACCENT2, fontsize=10, fontweight="bold", pad=6)
    fix_yticks(ax4b, fontsize=9)

    fig4.subplots_adjust(left=0.28, right=0.96, top=0.92, bottom=0.08, hspace=0.60)
    embed(fig4, frm_r)

    # ════════════════════════════════════════════════
    # PAGE 5 — Correlation & Heatmap
    # ════════════════════════════════════════════════
    p5 = tk.Frame(nb, bg=BG); nb.add(p5, text="  Heatmap & Correlation  ")
    page_header(p5,
                "Pollutant Correlation Matrix & State × Pollutant Heatmap",
                "Left: inter-pollutant correlation  ·  Right: normalised state-level burden heatmap")

    # Protect against Tkinter crop by using an incredibly safe base geometry of (4.0, 2.5)
    fig5 = Figure(figsize=(9.0, 5.8), dpi=DPI)
    fig5.subplots_adjust(left=0.08, right=0.96, top=0.88, bottom=0.15, wspace=0.30)
    fig5.patch.set_facecolor(BG)

    corr_cols = [c for c in ["aqi","pm25","pm10","no2","so2","co","ozone","nh3"]
                 if c in wide.columns]
    corr_lbl  = [c.upper().replace("OZONE","O₃").replace("NH3","NH₃") for c in corr_cols]
    corr      = wide[corr_cols].corr()

    ax5a = fig5.add_subplot(121)
    im5a = ax5a.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax5a.set_xticks(range(len(corr_lbl)))
    ax5a.set_xticklabels(corr_lbl, rotation=35, ha="right", fontsize=11, color=FG)
    ax5a.set_yticks(range(len(corr_lbl)))
    ax5a.set_yticklabels(corr_lbl, fontsize=11, color=FG)
    _cmap_corr = plt.get_cmap("RdYlGn")
    for i in range(len(corr_lbl)):
        for j in range(len(corr_lbl)):
            v = corr.values[i, j]
            # Normalize correlation (-1…1) → (0…1) for the colormap
            txt_c = _cell_txt_color(_cmap_corr, (v + 1) / 2)
            ax5a.text(j, i, f"{v:.2f}", ha="center", va="center",
                      fontsize=10.5, fontweight="bold", color=txt_c)
    cb5a = fig5.colorbar(im5a, ax=ax5a, shrink=0.80)
    cb5a.ax.yaxis.set_tick_params(color=FG, labelsize=10)
    plt.setp(cb5a.ax.yaxis.get_ticklabels(), color=FG)
    style_ax(ax5a, "Pollutant Correlation Matrix")

    heat_cols = [c for c in ["pm25","pm10","no2","so2","ozone","nh3"] if c in wide.columns]
    heat_lbl  = [c.upper().replace("OZONE","O₃").replace("NH3","NH₃") for c in heat_cols]
    
    # Filter heatmap to Top 12 highest AQI states to prevent dense vertical text overlap
    top_12_states = valid.groupby("state")["aqi"].mean().sort_values(ascending=False).head(12).index
    state_pol = wide[wide["state"].isin(top_12_states)].groupby("state")[heat_cols].mean()
    state_pol = state_pol.loc[top_12_states]
    norm      = (state_pol - state_pol.min()) / (state_pol.max() - state_pol.min())

    ax5b = fig5.add_subplot(122)
    im5b = ax5b.imshow(norm.values, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)
    ax5b.set_xticks(range(len(heat_lbl)))
    ax5b.set_xticklabels(heat_lbl, fontsize=10, color=FG)
    ax5b.set_yticks(range(len(state_pol)))
    ax5b.set_yticklabels(state_pol.index, fontsize=9.5, color=FG)
    _cmap_heat = plt.get_cmap("RdYlGn_r")
    for i in range(len(state_pol)):
        for j in range(len(heat_cols)):
            rv  = state_pol.values[i, j]
            nv  = norm.values[i, j]
            txt = "nan" if (isinstance(rv, float) and np.isnan(rv)) else f"{rv:.0f}"
            txt_c = _cell_txt_color(_cmap_heat, None if (isinstance(nv, float) and np.isnan(nv)) else nv)
            ax5b.text(j, i, txt, ha="center", va="center",
                      fontsize=9, color=txt_c)
    cb5b = fig5.colorbar(im5b, ax=ax5b, shrink=0.80)
    cb5b.ax.yaxis.set_tick_params(color=FG, labelsize=10)
    plt.setp(cb5b.ax.yaxis.get_ticklabels(), color=FG)
    style_ax(ax5b, "Heatmap: Top 12 Most Polluted States")

    embed(fig5, p5)


# ══════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════
def main():
    root = tk.Tk()
    root.title("India Air Quality Dashboard — Real-Time CPCB Data")
    root.configure(bg=BG)
    root.state("zoomed")
    
    def refresh_data(btn_widget=None):
        if btn_widget:
            btn_widget.config(text="Syncing Data...", bg=ACCENT, fg=BG, state="disabled")
            root.update()
            
        new_wide, new_raw = load_data()
        
        for widget in root.winfo_children():
            widget.destroy()
            
        build_dashboard(root, new_wide, new_raw, refresh_callback=refresh_data)

    wide, raw = load_data()
    build_dashboard(root, wide, raw, refresh_callback=refresh_data)
    root.mainloop()

if __name__ == "__main__":
    main()
