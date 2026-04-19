# 🌿 India Air Quality Analysis Dashboard
**Data Visualization & Analysis (DVA) Project | IPU BCA 6th Semester**

A professional, fully interactive, desktop-scale analytics dashboard rendering real-time air quality metrics across India. Built natively in Python leveraging **Tkinter** for the graphical interface and **Matplotlib** for high-resolution, responsive backend data rendering.

---

## ✨ Key Features
- **Live Data Hot-Reloading:** Includes a robust "Refresh Data" synchronization pipeline that natively hot-reloads the CSV data and rebuilds the active dashboard state in under a second without requiring an application restart.
- **Interactive Tooltips (Hover Analytics):** Globally integrated with `mplcursors` across the layout. Hovering over any bar chart natively draws a styled, precision popup floating card containing the exact geographical index and pollution subset value.
- **Dynamic Subplot Geometry:** The layout exclusively relies on custom Matplotlib `GridSpecs` and strict boundary `tight_layout` parameters (including explicitly reserved absolute pixel clearances) to perfectly eliminate data clipping, string overlaps, or native scrollbar artifacts.
- **Sleek Aesthetic Engine:** Programmatically enforces a high-contrast dark theme parameter (`#0D1117` base) mapping gracefully across both Tkinter container widgets and nested Matplotlib figure patches.

---

## 📊 Dashboard Architecture (5-Panel System)

| Module | Analytical Scope |
|-----|-------------|
| **1. Executive Overview** | High-level national KPI stacks. Sub-grids feature *Top 5 Polluted/Cleanest Cities*, mathematical AQI dispersion Donuts, and *Top 10 State Deficits*. |
| **2. State Analysis** | Massive split-view matrix plotting sorted state-aggregated metrics opposite to a scrolling interactive table matrix. |
| **3. Pollutants** | Advanced 4-grid subplot mapping specific chemical concentrations (PM2.5, PM10, NO₂, SO₂) against static WHO/CPCB hardcoded limits. |
| **4. City Rankings** | A localized deep-dive containing thousands of data points presented in an embedded infinite-scrolling Canvas widget mapped out per city framework. |
| **5. Heatmap & Correlation** | Rendered cross-tabulation arrays. Computes pollutant-to-pollutant correlation variables and paints a normalized 2D geographical Heatmap. |

---

## 📂 The Dataset
Data represents localized realtime snapshot values aggregated by the Central Pollution Control Board (CPCB), Government of India (`Real_Time_GOV_Of_India_AQI.csv`).

- **Coverage:** ~3400+ distinct recording stations mapped across 264 Cities and 30 States.
- **Captured Pollutants:** PM2.5, PM10, NO₂, SO₂, CO, O₃, NH₃.
- **Categorical Processing:**
  - *`0–50`*      : Good
  - *`51–100`*    : Satisfactory
  - *`101–200`*   : Moderately Polluted
  - *`201–300`*   : Poor
  - *`301–400`*   : Very Poor
  - *`401–500`*   : Severe

---

## ⚙️ Installation & Deployment

**1. Install Core Dependencies**
The backend requires Matplotlib mapping tools and MPLCursor tooltip handlers to run smoothly:
```bash
pip install pandas numpy matplotlib pillow mplcursors
```

**2. Execute Environment**
Ensure the Python script (`AirQualityDashboard.py`), the image logos, and the core dataset (`Real_Time_GOV_Of_India_AQI.csv`) reside parallel within the same directory.
```bash
python AirQualityDashboard.py
```
