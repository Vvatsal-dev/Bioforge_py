"""
bioreactor.py - fermentation data, microbial growth maths and charts.

What lives here
---------------
1. A built-in 24 h aerobic batch culture of Escherichia coli K-12
   (generated from a Monod / Baranyi growth model with scipy, then sampled
   every 30 min with realistic sensor noise and saved to data/*.csv).
2. Loading + validating a user's own CSV file.
3. The analytics: specific growth rate (mu), post-cutoff averages,
   peak growth time, growth phases, key process events.
4. Plotly charts (biomass vs time with a DO / glucose overlay, growth rates).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.integrate import solve_ivp

from bioforge.plot_style import base_layout, style_axes, with_alpha

# ---------------------------------------------------------------------------
# Column names (the "contract" every dataset must follow)
# ---------------------------------------------------------------------------
TIME = "time_hours"
OD = "cell_density_OD600"
DO = "dissolved_oxygen_pct"
GLUCOSE = "glucose_conc_gL"
MU = "specific_growth_rate_mu"
REQUIRED_COLUMNS = [TIME, OD, DO, GLUCOSE]
ALL_COLUMNS = REQUIRED_COLUMNS + [MU]

# Extra columns the app calculates (not stored in the CSV)
GROWTH_RATE = "growth_rate_OD_per_h"   # dOD600/dt

PARAMETERS = {
    "Dissolved Oxygen (%)": {"column": DO, "unit": "%", "short": "DO", "decimals": 1},
    "Nutrient / Glucose Level (g/L)": {"column": GLUCOSE, "unit": "g/L", "short": "Glucose", "decimals": 2},
}

OD_TO_DCW = 0.40              # g dry cell weight per litre per OD600 unit (typical E. coli)
GLUCOSE_DEPLETED_GL = 0.1     # below this glucose counts as exhausted
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "ecoli_k12_batch_24h.csv"

EXPERIMENT_INFO = {
    "Organism": "Escherichia coli K-12 (MG1655)",
    "Mode": "Aerobic batch culture, no feeding",
    "Vessel": "2 L stirred-tank bioreactor (1.5 L working volume)",
    "Medium": "M9 minimal salts + 5 g/L glucose",
    "Conditions": "37 °C, pH 7.0 (controlled), 1 vvm air, fixed agitation",
    "Sampling": "Every 30 min for 24 h (49 readings)",
    "Inoculum": "OD600 = 0.10",
}

# Kinetic parameters used to generate the built-in dataset
MODEL_PARAMS = {
    "mu_max": 0.65,      # 1/h    maximum specific growth rate
    "Ks": 0.05,          # g/L    Monod half-saturation constant for glucose
    "Yxs": 0.48,         # g/g    biomass yield on glucose
    "ms": 0.03,          # g/g/h  maintenance glucose uptake
    "q0": 0.30,          # -      Baranyi initial physiological state (sets the lag)
    "Yxo": 1.2,          # g/g    biomass yield on oxygen
    "mo": 0.02,          # g/g/h  maintenance / endogenous oxygen uptake
    "kLa": 220.0,        # 1/h    oxygen transfer coefficient
    "C_star": 6.8,       # mg/L   O2 saturation at 37 C
    "kd_max": 0.035,     # 1/h    death/lysis rate after prolonged starvation
    "starve_onset": 5.0, # h      starvation time before death dominates
    "X0": 0.10 * OD_TO_DCW,
    "S0": 5.0,
}


class DatasetError(ValueError):
    """Raised when an uploaded CSV cannot be used."""


# ===========================================================================
# 1. Built-in dataset
# ===========================================================================
def _batch_model(t, y, p):
    """Right-hand side of the growth ODEs.

    y = [X biomass g/L, S glucose g/L, q physiological state, tau starvation h]
    """
    X, S, q, tau = y
    S = max(S, 0.0)
    alpha = q / (1.0 + q)                          # Baranyi lag adjustment (0 -> 1)
    mu = alpha * p["mu_max"] * S / (p["Ks"] + S)   # Monod kinetics
    kd = p["kd_max"] / (1.0 + np.exp(-(tau - p["starve_onset"]) / 0.8))

    dX = (mu - kd) * X
    dS = -(mu / p["Yxs"] + p["ms"] * S / (S + p["Ks"])) * X
    dq = p["mu_max"] * q
    dtau = 0.01 / (0.01 + S)                       # ~1 once glucose is gone
    return [dX, dS, dq, dtau]


def simulate_ecoli_batch(hours=24.0, sample_every_h=0.5, seed=42, noise=True):
    """Generate the built-in E. coli K-12 batch fermentation dataset."""
    p = MODEL_PARAMS
    t_eval = np.round(np.arange(0.0, hours + 1e-9, sample_every_h), 2)
    solution = solve_ivp(
        _batch_model, (0.0, hours), [p["X0"], p["S0"], p["q0"], 0.0],
        t_eval=t_eval, args=(p,), method="LSODA", rtol=1e-8, atol=1e-10,
    )
    X, S, q, _ = solution.y
    S = np.clip(S, 0, None)

    # Dissolved oxygen: quasi-steady-state oxygen balance  OTR = OUR
    mu = (q / (1 + q)) * p["mu_max"] * S / (p["Ks"] + S)
    our = (mu / p["Yxo"] + p["mo"]) * X * 1000.0           # mg O2 / L / h
    do_pct = 100.0 * (1.0 - our / (p["kLa"] * p["C_star"]))

    od = X / OD_TO_DCW
    if noise:
        rng = np.random.default_rng(seed)
        od = od * (1 + rng.normal(0, 0.012, od.size)) + rng.normal(0, 0.002, od.size)
        do_pct = do_pct + rng.normal(0, 0.8, do_pct.size)
        S = S * (1 + rng.normal(0, 0.01, S.size)) + rng.normal(0, 0.02, S.size)

    df = pd.DataFrame(
        {
            TIME: t_eval,
            OD: np.clip(od, 0.001, None).round(3),
            DO: np.clip(do_pct, 0, 100).round(1),
            GLUCOSE: np.clip(S, 0, None).round(3),
        }
    )
    return add_growth_rates(df)


def load_builtin_dataset():
    """Read the shipped CSV (or regenerate it if the file is missing)."""
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        return add_growth_rates(df[REQUIRED_COLUMNS])
    return simulate_ecoli_batch()


def save_builtin_dataset(path=DATA_FILE):
    """Write the built-in dataset to CSV (run once when setting up the project)."""
    df = simulate_ecoli_batch()
    df[ALL_COLUMNS].to_csv(path, index=False)
    return df


# ===========================================================================
# 2. Uploaded datasets
# ===========================================================================
def parse_uploaded_csv(file):
    """Read and clean an uploaded CSV. Returns (DataFrame, list of notes).

    Raises DatasetError with a friendly message when the file can't be used.
    """
    try:
        raw = pd.read_csv(file)
    except Exception as exc:  # noqa: BLE001 - any parsing problem is a user error
        raise DatasetError(f"Could not read the file as CSV ({exc}).") from exc

    notes = []
    # match column names without caring about capitals or extra spaces
    lookup = {col.strip().lower(): col for col in raw.columns}
    missing = [col for col in REQUIRED_COLUMNS if col.lower() not in lookup]
    if missing:
        raise DatasetError("Missing required column(s): " + ", ".join(missing))

    df = pd.DataFrame({col: raw[lookup[col.lower()]] for col in REQUIRED_COLUMNS})
    df = df.apply(pd.to_numeric, errors="coerce")

    bad_rows = int(df.isna().any(axis=1).sum())
    if bad_rows:
        df = df.dropna()
        notes.append(f"Dropped {bad_rows} row(s) with missing or non-numeric values.")

    duplicates = int(df.duplicated(subset=TIME).sum())
    if duplicates:
        df = df.drop_duplicates(subset=TIME)
        notes.append(f"Removed {duplicates} duplicated time point(s).")

    df = df.sort_values(TIME).reset_index(drop=True)
    if len(df) < 3:
        raise DatasetError("Need at least 3 valid time points to calculate growth rates.")
    if (df[OD] <= 0).any():
        df[OD] = df[OD].clip(lower=0.001)
        notes.append("OD600 values ≤ 0 were set to 0.001 so ln(OD) can be taken.")

    if MU.lower() in lookup:
        notes.append("specific_growth_rate_mu was recalculated from OD600 for consistency.")
    else:
        notes.append("specific_growth_rate_mu was calculated from OD600 (column not in file).")
    return add_growth_rates(df), notes


# ===========================================================================
# 3. Analytics
# ===========================================================================
def add_growth_rates(df):
    """Add mu = d ln(OD)/dt and the absolute growth rate dOD/dt.

    np.gradient uses central differences (and one-sided ones at the ends),
    and handles uneven time steps correctly.
    """
    df = df.copy()
    t = df[TIME].to_numpy(dtype=float)
    od = df[OD].to_numpy(dtype=float)
    df[MU] = np.gradient(np.log(od), t).round(4)
    df[GROWTH_RATE] = np.gradient(od, t).round(4)
    return df


def filter_after(df, cutoff_h):
    """Keep only readings taken at or after the cutoff time (t >= t_cutoff)."""
    return df[df[TIME] >= cutoff_h]


def post_cutoff_average(df, column, cutoff_h):
    """Return (average after cutoff, whole-run average, readings used)."""
    window = filter_after(df, cutoff_h)
    after = window[column].mean() if len(window) else float("nan")
    return after, df[column].mean(), len(window)


def find_peak_growth(df):
    """Locate the time point where dOD600/dt is at its absolute maximum."""
    i = df[GROWTH_RATE].idxmax()
    return {"time": float(df.at[i, TIME]), "rate": float(df.at[i, GROWTH_RATE]), "od": float(df.at[i, OD])}


def find_mu_max(df):
    """Locate the maximum specific growth rate mu (1/h) and the doubling time."""
    i = df[MU].idxmax()
    mu_max = float(df.at[i, MU])
    doubling_min = (np.log(2) / mu_max * 60) if mu_max > 0 else float("nan")
    return {"time": float(df.at[i, TIME]), "mu": mu_max, "od": float(df.at[i, OD]), "doubling_min": doubling_min}


def detect_phases(df):
    """Split the run into lag, exponential, stationary and decline phases.

    Rules (applied to lightly smoothed data):
      exponential = the block around the fastest growth where mu >= 50% of mu_max
      lag         = everything before that block
      decline     = after the OD peak, once OD falls below 95% of its maximum
      stationary  = between the end of exponential growth and the decline
    """
    t = df[TIME].to_numpy(dtype=float)
    mu_s = df[MU].rolling(3, center=True, min_periods=1).mean().to_numpy()
    od_s = df[OD].rolling(3, center=True, min_periods=1).mean().to_numpy()

    peak = int(np.argmax(mu_s))
    threshold = 0.5 * mu_s[peak]
    start = peak
    while start > 0 and mu_s[start - 1] >= threshold:
        start -= 1
    end = peak
    while end < len(t) - 1 and mu_s[end + 1] >= threshold:
        end += 1

    od_peak = int(np.argmax(od_s))
    decline = None
    for i in range(max(od_peak, end), len(t)):
        if od_s[i] <= 0.95 * od_s[od_peak]:
            decline = i
            break

    bounds = [("Lag", 0, start), ("Exponential", start, end)]
    if decline is None:
        bounds.append(("Stationary", end, len(t) - 1))
    else:
        bounds += [("Stationary", end, decline), ("Decline", decline, len(t) - 1)]

    phases = []
    for name, i0, i1 in bounds:
        if t[i1] > t[i0]:
            window = df[(df[TIME] >= t[i0]) & (df[TIME] <= t[i1])]
            phases.append({
                "Phase": name,
                "Start (h)": t[i0],
                "End (h)": t[i1],
                "Duration (h)": t[i1] - t[i0],
                "Mean μ (1/h)": window[MU].mean(),
            })
    return phases


def key_events(df):
    """Find the bioprocess 'landmarks' an engineer would look for."""
    events = {}
    depleted = df[df[GLUCOSE] <= GLUCOSE_DEPLETED_GL]
    events["glucose_depleted_at"] = float(depleted[TIME].iloc[0]) if len(depleted) else None

    i_min = df[DO].idxmin()
    events["do_min"] = float(df.at[i_min, DO])
    events["do_min_time"] = float(df.at[i_min, TIME])

    jumps = df[DO].diff()
    i_jump = jumps.idxmax()
    if pd.notna(jumps.max()) and jumps.max() >= 20:
        events["do_spike_time"] = float(df.at[i_jump, TIME])
        events["do_spike_size"] = float(jumps.max())
    else:
        events["do_spike_time"] = None
        events["do_spike_size"] = None

    i_od = df[OD].idxmax()
    events["od_max"] = float(df.at[i_od, OD])
    events["od_max_time"] = float(df.at[i_od, TIME])
    return events


def biomass_yield(df):
    """Biomass yield Yx/s (g cells per g glucose) up to the OD peak."""
    i_od = df[OD].idxmax()
    x_gain = (df.at[i_od, OD] - df[OD].iloc[0]) * OD_TO_DCW
    s_used = df[GLUCOSE].iloc[0] - df.at[i_od, GLUCOSE]
    return float(x_gain / s_used) if s_used > 0 else float("nan")


# ===========================================================================
# 4. Charts
# ===========================================================================
def growth_chart(df, cutoff_h, parameter_label, peak, phases, pal, layout="Overlay"):
    """Biomass (OD600) vs time with DO or glucose overlaid on a second axis.

    layout = "Overlay" -> one panel with a secondary y-axis
    layout = "Stacked" -> two panels sharing the time axis
    """
    info = PARAMETERS[parameter_label]
    param_color = pal["blue"] if info["column"] == DO else pal["orange"]
    stacked = layout == "Stacked"

    if stacked:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                            row_heights=[0.62, 0.38])
        param_kwargs = dict(row=2, col=1)
        od_kwargs = dict(row=1, col=1)
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        param_kwargs = dict(secondary_y=True)
        od_kwargs = dict(secondary_y=False)

    t_min, t_max = float(df[TIME].min()), float(df[TIME].max())

    # grey wash over the readings excluded by the filter
    if cutoff_h > t_min:
        fig.add_vrect(x0=t_min, x1=cutoff_h, fillcolor=pal["muted"], opacity=0.12,
                      line_width=0, layer="below")

    # phase boundaries (thin lines) + phase names along the top
    for ph in phases[1:]:
        fig.add_vline(x=ph["Start (h)"], line_width=1, line_color=pal["axis"])
    for ph in phases:
        fig.add_annotation(
            x=(ph["Start (h)"] + ph["End (h)"]) / 2, y=1.0, xref="x", yref="paper",
            yanchor="bottom", text=ph["Phase"], showarrow=False,
            font=dict(size=11, color=pal["text2"]),
        )

    # biomass curve
    fig.add_trace(
        go.Scatter(
            x=df[TIME], y=df[OD], name="Biomass (OD600)", mode="lines+markers",
            line=dict(color=pal["primary"], width=2),
            marker=dict(size=6, color=pal["primary"], line=dict(width=1.5, color=pal["surface"])),
            hovertemplate="%{y:.3f} OD<extra>Biomass</extra>",
        ),
        **od_kwargs,
    )
    # DO or glucose curve
    fig.add_trace(
        go.Scatter(
            x=df[TIME], y=df[info["column"]], name=parameter_label, mode="lines+markers",
            line=dict(color=param_color, width=2),
            marker=dict(size=5, color=param_color, line=dict(width=1.5, color=pal["surface"])),
            hovertemplate=f"%{{y:.{info['decimals']}f}} {info['unit']}<extra>{info['short']}</extra>",
        ),
        **param_kwargs,
    )
    # peak growth marker
    fig.add_trace(
        go.Scatter(
            x=[peak["time"]], y=[peak["od"]], name="Peak growth rate (max dOD/dt)",
            mode="markers",
            marker=dict(symbol="star", size=18, color=pal["text"], line=dict(width=2, color=pal["surface"])),
            hovertemplate=f"t_peak = {peak['time']:.1f} h<br>dOD/dt = {peak['rate']:.2f} OD/h<extra></extra>",
        ),
        **od_kwargs,
    )
    fig.add_annotation(
        x=peak["time"], y=peak["od"], text=f"<b>t<sub>peak</sub> = {peak['time']:.1f} h</b>",
        showarrow=True, arrowhead=0, arrowcolor=pal["text2"], ax=-70, ay=-30,
        font=dict(color=pal["text"], size=12), bgcolor=pal["surface"], borderpad=3,
        **({"row": 1, "col": 1} if stacked else {}),
    )

    # the cutoff line the user controls
    fig.add_vline(x=cutoff_h, line_dash="dash", line_width=2, line_color=pal["text2"])
    fig.add_annotation(
        x=cutoff_h, y=0.02, xref="x", yref="paper", xanchor="left", yanchor="bottom",
        text=f" t<sub>cutoff</sub> = {cutoff_h:g} h", showarrow=False,
        font=dict(size=12, color=pal["text"]), bgcolor=pal["surface"],
    )

    base_layout(fig, pal, height=520 if stacked else 470)
    style_axes(fig, pal)
    fig.update_xaxes(range=[t_min - 0.3, t_max + 0.3])
    param_title = f"{info['short']} ({info['unit']})"
    param_range = [0, 105] if info["column"] == DO else [0, float(df[info["column"]].max()) * 1.1]
    if stacked:
        fig.update_xaxes(title_text="Time (h)", row=2, col=1)
        fig.update_yaxes(title_text="OD600", rangemode="tozero", row=1, col=1)
        fig.update_yaxes(title_text=param_title, range=param_range, row=2, col=1)
    else:
        fig.update_xaxes(title_text="Time (h)")
        fig.update_yaxes(title_text="Cell density (OD600)", rangemode="tozero", secondary_y=False)
        fig.update_yaxes(title_text=param_title, range=param_range, tickmode="auto", nticks=7,
                         showgrid=False, secondary_y=True)
    return fig


def rate_chart(df, column, marker, pal, title_unit, color_key="primary"):
    """Small chart of a growth rate over time with its maximum marked."""
    color = pal[color_key]
    y_value = marker["rate"] if column == GROWTH_RATE else marker["mu"]
    fig = go.Figure()
    fig.add_hline(y=0, line_width=1, line_color=pal["axis"])
    fig.add_trace(
        go.Scatter(
            x=df[TIME], y=df[column], mode="lines", name=title_unit,
            line=dict(color=color, width=2), fill="tozeroy",
            fillcolor=with_alpha(color, 0.10),
            hovertemplate=f"%{{y:.3f}} {title_unit}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[marker["time"]], y=[y_value], mode="markers+text", name="Maximum",
            marker=dict(size=11, color=color, line=dict(width=2, color=pal["surface"])),
            text=[f"max at {marker['time']:.1f} h"], textposition="top center",
            textfont=dict(color=pal["text"], size=12),
            hovertemplate=f"max {y_value:.3f} {title_unit} at %{{x:.1f}} h<extra></extra>",
        )
    )
    base_layout(fig, pal, height=300)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
    style_axes(fig, pal)
    fig.update_xaxes(title_text="Time (h)")
    low, high = float(df[column].min()), float(df[column].max())
    fig.update_yaxes(title_text=title_unit, range=[min(0.0, low) * 1.2, high * 1.3])
    return fig
