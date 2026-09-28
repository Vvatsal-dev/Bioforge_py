# BioForge: Enzyme & Bioreactor Lab (Python Edition)

BioForge is an educational enzyme reaction simulator, now rebuilt **entirely in Python** with
Streamlit. The biology and the maths are the same as the original React website. The
difference is that every page, slider, chart and calculation is Python code.

It has five pages:

| Page | What you can do |
|---|---|
| **Overview** | Hero page, a 3-step demo (choose an enzyme, move temperature/pH, see the live rate) |
| **Simulate** | Virtual lab: animated reaction flask, temperature / pH / stirring / [S] controls, progress chart with run comparison, Michaelis-Menten, Lineweaver-Burk and temperature/pH profiles, CSV export |
| **Build Enzyme** | Design a custom enzyme (Km, Vmax, optimum T and pH), see its curves live, save it and test it in the simulator |
| **Specifications** | 9 equation cards (typeset with LaTeX), filterable, plus a live table of every registered enzyme |
| **Bioreactor** (new) | 24 h *E. coli* K-12 batch fermentation: time-cutoff filter, post-cutoff averages, peak growth time, growth phases, DO / glucose overlay, CSV upload |

---

## 1. How to run it

You need Python 3.10 or newer.

```bash
# 1. go into the project folder
cd bioforge_python

# 2. (optional but recommended) create a virtual environment
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# 3. install the libraries
pip install -r requirements.txt

# 4. start the app
streamlit run app.py
```

The app opens in your browser at http://localhost:8501.
Dark mode: click the **⋮** menu (top right) → **Settings** → **Theme**.

To run the tests: `pip install pytest` and then `python -m pytest -q`.

---

## 2. Project structure

```
bioforge_python/
├── app.py                    # entry point: page setup + top navigation bar
├── requirements.txt          # streamlit, pandas, numpy, plotly, scipy
├── .streamlit/config.toml    # BioForge colours & fonts (light + dark theme)
├── assets/                   # logo and hero illustration (SVG images)
├── data/
│   └── ecoli_k12_batch_24h.csv   # built-in fermentation dataset (49 readings)
├── bioforge/
│   ├── catalog.py            # the 5 enzymes (dictionary of dictionaries)
│   ├── kinetics.py           # Michaelis-Menten, Lineweaver-Burk, T/pH/stirring modifiers, 20 s simulation
│   ├── bioreactor.py         # dataset generation, CSV upload, growth maths, fermentation charts
│   ├── charts.py             # Plotly charts for the enzyme pages + the drawn reaction flask
│   ├── specs.py              # the 9 equation cards
│   ├── state.py              # what the app remembers between clicks (st.session_state)
│   ├── theme.py              # chart colours for light / dark mode
│   ├── plot_style.py         # one shared look for all charts
│   ├── ui.py                 # small helpers (footer, "show the Python" expanders)
│   └── views/                # one file per page
│       ├── overview.py
│       ├── simulate.py
│       ├── build_enzyme.py
│       ├── specifications.py
│       └── bioreactor_lab.py
└── tests/test_bioforge.py    # 13 automatic checks of the maths
```

### Where each original website file went

| Original (React / TypeScript) | Python version |
|---|---|
| `context/EnzymeContext.tsx` (enzyme list) | `bioforge/catalog.py` + `bioforge/state.py` |
| `pages/SimulatePage.tsx` (kinetics + UI) | `bioforge/kinetics.py` + `bioforge/views/simulate.py` |
| `pages/BuildEnzymePage.tsx` | `bioforge/views/build_enzyme.py` |
| `pages/SpecificationsPage.tsx` | `bioforge/specs.py` + `bioforge/views/specifications.py` |
| `pages/LandingPage.tsx` | `bioforge/views/overview.py` |
| `components/Navbar.tsx`, `Footer.tsx` | `app.py` (`st.navigation`) + `bioforge/ui.py` |
| `index.css` (colours, dark mode) | `.streamlit/config.toml` + `bioforge/theme.py` |
| SVG flask + CSS animations | `charts.vessel_figure()` drawn with Plotly shapes |

---

## 3. Which library does what

| Library | Used for |
|---|---|
| **streamlit** | The whole web interface: pages, top navigation, sliders, buttons, metric cards, tables, file upload and download |
| **numpy** | Curves (`np.linspace`), derivatives (`np.gradient` for μ and dOD/dt), logarithms |
| **pandas** | The fermentation dataset, filtering `t ≥ t_cutoff`, averages, CSV import/export |
| **scipy** | `solve_ivp` integrates the Monod growth equations that generated the built-in dataset |
| **plotly** | Interactive charts (hover, zoom, download PNG) and the animated reaction flask |

---

## 4. The science

### Enzyme catalogue (5 benchmark biocatalysts)

| Enzyme | Substrate → Products | Km (mM) | Vmax (µmol/s) | Opt. T | Opt. pH |
|---|---|---|---|---|---|
| Lactase | Lactose → Glucose + Galactose | 12.0 | 8.5 | 37 °C | 6.5 |
| Amylase | Starch → Glucose | 5.0 | 10.0 | 37 °C | 6.7 |
| Catalase | H₂O₂ → H₂O + O₂ | 25.0 | 15.0 | 37 °C | 7.0 |
| **Urease** (new) | Urea → NH₃ + CO₂ | 10.5 | 22.0 | 37 °C | 7.0 |
| **Invertase** (new) | Sucrose → Glucose + Fructose | 26.0 | 14.5 | 50 °C | 4.5 |

### Simulator model (unchanged from the website)
- Rate: `v = Vmax·[S] / (Km + [S])`
- Temperature factor: Gaussian bell (σ = 14 °C) around the optimum; above **55 °C** the enzyme denatures
  (factor drops to ≤ 0.06 and the rate is capped at 4 % of Vmax)
- pH factor: Gaussian bell (σ = 1.6 pH units); more than 1.5 units away counts as "pH stressed"
- Stirring: gentle 0.85×, medium 1.0×, vigorous 1.18×
- Each 0.1 s the reaction closes part of the gap to its yield ceiling (98.5 % when healthy)
- Product (µmol) = [S] (mM) × conversion × 5.2 mL vessel volume

### Bioreactor dataset
A 2 L stirred-tank, aerobic **batch** culture of *E. coli* K-12 MG1655 in M9 + 5 g/L glucose at
37 °C, sampled every 30 min for 24 h. It was generated with `scipy.integrate.solve_ivp` from:
- Monod growth `μ = μmax·S/(Ks+S)` with μmax = 0.65 h⁻¹, plus a Baranyi lag phase (~2 h)
- Glucose uptake with a yield of 0.48 g cells / g glucose plus maintenance
- Oxygen balance `OTR = OUR` with kLa = 220 h⁻¹ (gives the DO dip and the DO spike at glucose exhaustion)
- Slow cell lysis after several hours of starvation (decline phase)
- Small random sensor noise so it looks like real measurements

Analytics on the page:
- **Post-cutoff average**: `df[df.time_hours >= t_cutoff][column].mean()`, compared with the whole-run mean
- **Peak growth time**: the reading where `ΔOD600/Δt` (`np.gradient`) is largest
- **Specific growth rate**: `μ = d ln(OD600)/dt`, μmax and doubling time `ln 2 / μmax`
- **Growth phases**: lag, exponential, stationary and decline detected automatically from μ and OD
- **Process insights**: glucose exhaustion time, DO minimum, DO spike, biomass yield Yx/s

### Upload your own CSV
Required columns: `time_hours, cell_density_OD600, dissolved_oxygen_pct, glucose_conc_gL`
(`specific_growth_rate_mu` is optional; it is recalculated from OD600). Use the
**Download CSV template** button on the Bioreactor page to get a correctly formatted file.

---

## 5. Computational-thinking concepts used

- **Decomposition**: the app is split into data (`catalog.py`), maths (`kinetics.py`, `bioreactor.py`),
  charts (`charts.py`) and pages (`views/`)
- **Abstraction**: one `compute_kinetics()` function hides all four rate modifiers behind one call
- **Algorithms**: the 200-step simulation loop, finding a maximum (`idxmax`), phase detection by scanning left/right from a peak
- **Data structures**: dictionaries for enzymes, lists for run history, pandas DataFrames for time series
- **Numerical methods**: numerical differentiation (`np.gradient`) and ODE integration (`solve_ivp`)
- **Testing**: `tests/test_bioforge.py` checks the maths against known biochemistry facts

Every page has a **"🐍 The Python behind …"** expander that prints the real source code of the
functions doing the calculation, which is handy for a viva or presentation.

---

## 6. Share it online (optional)

1. Put this folder in a GitHub repository.
2. Go to https://share.streamlit.io, sign in with GitHub, choose the repo and `app.py`.
3. You get a public link your teacher and classmates can open.
