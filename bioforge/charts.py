"""
charts.py - Plotly figures for the enzyme pages.

  vessel_figure       the reaction flask drawn with shapes (replaces the CSS flask)
  progress_chart      reaction progress over 20 s, with earlier runs for comparison
  mm_chart            Michaelis-Menten curve v vs [S]
  lb_chart            Lineweaver-Burk double-reciprocal plot
  temperature_chart   activity vs temperature (denaturation zone shaded)
  ph_chart            activity vs pH (stress zones shaded)
  compare_chart       Michaelis-Menten curves of every registered enzyme
  sparkline           the tiny curve on the Overview page
"""

import numpy as np
import plotly.graph_objects as go

from bioforge import kinetics as kin
from bioforge.plot_style import base_layout, mix, style_axes, with_alpha

# ---------------------------------------------------------------------------
# Reaction vessel
# ---------------------------------------------------------------------------
NECK_X, SHOULDER_Y, BODY_X, BODY_Y = 0.16, 0.70, 0.60, 0.14
LIQUID_LEVEL = 0.44
FLASK_PATH = (
    f"M {-NECK_X} 1.06 L {-NECK_X} {SHOULDER_Y} L {-BODY_X} {BODY_Y} "
    f"Q -0.66 0.04 -0.52 0.04 L 0.52 0.04 Q 0.66 0.04 {BODY_X} {BODY_Y} "
    f"L {NECK_X} {SHOULDER_Y} L {NECK_X} 1.06"
)


def _wall_x(y):
    """x position of the flask's right wall at height y (body section)."""
    return NECK_X + (SHOULDER_Y - y) / (SHOULDER_Y - BODY_Y) * (BODY_X - NECK_X)


def vessel_figure(progress_pct, kinetics, stirring_rate, temp_c, ph, optimal_ph, vmax,
                  active, pal, frame=0):
    """Draw the flask. The liquid colour follows the reaction progress.

    active = True while a run is playing or has finished (shows bubbles).
    """
    fig = go.Figure()
    denatured = kinetics["denatured"]
    stressed = kinetics["ph_stressed"]

    # soft glow behind the flask: teal = healthy, red = denatured, blue = pH stress
    glow = pal["red"] if denatured else (pal["blue"] if stressed else pal["primary"])
    fig.add_shape(type="circle", x0=-0.8, x1=0.8, y0=-0.06, y1=1.24,
                  fillcolor=glow, opacity=0.10, line_width=0, layer="below")

    # liquid colour: pale substrate -> emerald product
    p = progress_pct / 100
    liquid = mix("#CFFAFE", "#5EEAD4", min(1, p * 2)) if p < 0.5 else mix("#5EEAD4", "#10B981", (p - 0.5) * 2)
    if stressed and not denatured:
        liquid = mix(liquid, "#A855F7" if ph < optimal_ph else "#3B82F6", 0.35)
    if denatured:
        liquid = "#FDE68A"   # cloudy, curdled protein

    # stirring makes a vortex dip in the liquid surface
    dip = 0.015 * stirring_rate
    xl = _wall_x(LIQUID_LEVEL) - 0.01
    liquid_path = (
        f"M {-xl} {LIQUID_LEVEL} Q 0 {LIQUID_LEVEL - 2 * dip} {xl} {LIQUID_LEVEL} "
        f"L {BODY_X - 0.01} {BODY_Y} Q 0.65 0.05 0.52 0.05 L -0.52 0.05 "
        f"Q -0.65 0.05 {-BODY_X + 0.01} {BODY_Y} Z"
    )
    fig.add_shape(type="path", path=liquid_path, fillcolor=liquid, opacity=0.9, line_width=0, layer="below")

    # amber glow of product forming at the bottom
    if not denatured and p > 0:
        fig.add_shape(type="circle", x0=-0.42, x1=0.42, y0=0.02, y1=0.30,
                      fillcolor="#EAB308", opacity=0.12 * p, line_width=0, layer="below")

    # glass outline, rim and highlights
    fig.add_shape(type="path", path=FLASK_PATH, line=dict(color="#94A3B8", width=4))
    fig.add_shape(type="line", x0=-0.21, x1=0.21, y0=1.06, y1=1.06,
                  line=dict(color="#94A3B8", width=7))
    fig.add_shape(type="line", x0=-0.11, x1=-0.11, y0=0.98, y1=0.74,
                  line=dict(color="white", width=3), opacity=0.55)
    fig.add_shape(type="line", x0=-0.21, x1=-0.47, y0=0.62, y1=0.29,
                  line=dict(color="white", width=3), opacity=0.55)
    for y in (0.22, 0.32, 0.42, 0.52):   # volume graduations
        xw = _wall_x(y)
        fig.add_shape(type="line", x0=xw - 0.12, x1=xw - 0.04, y0=y, y1=y,
                      line=dict(color="#94A3B8", width=1.5))

    # magnetic stir bar
    fig.add_shape(type="rect", x0=-0.13, x1=0.13, y0=0.065, y1=0.095,
                  fillcolor="#E2E8F0", line=dict(color="#64748B", width=1))

    # bubbles - more of them when the enzyme works faster
    rng = np.random.default_rng(frame)
    if denatured:
        n_bubbles = 2
    elif active:
        n_bubbles = 4 + int(14 * min(1.0, kinetics["effective_rate"] / max(vmax, 1)))
    else:
        n_bubbles = 3
    ys = rng.uniform(0.10, LIQUID_LEVEL - 0.05, n_bubbles)
    xs = [rng.uniform(-(_wall_x(y) - 0.10), _wall_x(y) - 0.10) for y in ys]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers", hoverinfo="skip",
        marker=dict(size=rng.uniform(6, 13, n_bubbles), color="rgba(255,255,255,0.8)",
                    line=dict(color="rgba(13,148,136,0.7)", width=1.2)),
    ))

    # denatured protein clumps
    if denatured:
        fig.add_trace(go.Scatter(
            x=[-0.30, 0.22, -0.08, 0.34, -0.40, 0.05], y=[0.10, 0.12, 0.20, 0.24, 0.18, 0.09],
            mode="markers", hoverinfo="skip",
            marker=dict(size=[18, 22, 14, 16, 12, 20], color="#FFFFFF", opacity=0.95,
                        line=dict(color="#D97706", width=1.5)),
        ))

    # steam from the neck when warm
    if temp_c >= 38:
        steam_opacity = 0.55 if temp_c >= 55 else 0.28
        fig.add_trace(go.Scatter(
            x=[-0.05, 0.07, -0.02], y=[1.14, 1.20, 1.27], mode="markers", hoverinfo="skip",
            marker=dict(size=[22, 28, 20], color=pal["gray"], opacity=steam_opacity),
        ))

    fig.update_layout(
        template="none", height=320, showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[-0.85, 0.85], visible=False, fixedrange=True),
        yaxis=dict(range=[-0.02, 1.34], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Reaction progress over time
# ---------------------------------------------------------------------------
def progress_chart(runs, current_run_id, pal, colors):
    """runs = list of dicts {id, label, df}. The current run is drawn boldest."""
    fig = go.Figure()
    fig.add_hline(y=kin.MAX_YIELD_PCT, line_width=1.5, line_dash="dot", line_color=pal["gray"])
    fig.add_annotation(x=0.3, y=kin.MAX_YIELD_PCT, xanchor="left", yanchor="bottom",
                       text="Vmax ceiling (max yield 98.5%)", showarrow=False,
                       font=dict(size=11, color=pal["text2"]))

    for run in runs:
        color = colors[(run["id"] - 1) % len(colors)]
        is_current = run["id"] == current_run_id
        df = run["df"]
        fig.add_trace(go.Scatter(
            x=df["time_s"], y=df["progress_pct"], mode="lines",
            name=run["label"] + ("  (current)" if is_current else ""),
            line=dict(color=color, width=3 if is_current else 1.8),
            opacity=1.0 if is_current else 0.75,
            fill="tozeroy" if is_current else None,
            fillcolor=with_alpha(color, 0.10) if is_current else None,
            hovertemplate="%{y:.1f}% at %{x:.1f} s<extra>Run " + str(run["id"]) + "</extra>",
        ))
        if is_current:
            last = df.iloc[-1]
            fig.add_trace(go.Scatter(
                x=[last["time_s"]], y=[last["progress_pct"]], mode="markers+text",
                marker=dict(size=10, color=color, line=dict(width=2, color=pal["surface"])),
                text=[f"{last['progress_pct']:.1f}%"], textposition="bottom left",
                textfont=dict(color=pal["text"], size=12), showlegend=False, hoverinfo="skip",
            ))

    if not runs:
        fig.add_annotation(x=10, y=50, text="Press ▶ Start Simulation to record a run",
                           showarrow=False, font=dict(size=14, color=pal["text2"]))

    base_layout(fig, pal, height=360, top_margin=20)
    style_axes(fig, pal)
    fig.update_xaxes(title_text="Time (s)", range=[0, 20.5], dtick=5)
    fig.update_yaxes(title_text="Reaction progress (%)", range=[0, 105])
    return fig


def partial_run(df, upto_s):
    """Rows of a run up to a given time (used for the playback animation)."""
    return df[df["time_s"] <= upto_s + 1e-9]


# ---------------------------------------------------------------------------
# Michaelis-Menten & Lineweaver-Burk
# ---------------------------------------------------------------------------
def mm_chart(km, vmax, pal, s_max=60.0, conditions=None, current_s=None):
    """Michaelis-Menten curve. conditions = kinetics dict for the 'current' curve."""
    s = np.linspace(0, s_max, 241)
    v = kin.michaelis_menten(s, vmax, km)
    y_top = vmax * 1.18

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s, y=v, mode="lines", name="Ideal enzyme (optimal conditions)",
        line=dict(color=pal["primary"], width=2.5), fill="tozeroy",
        fillcolor=with_alpha(pal["primary"], 0.10),
        hovertemplate="[S] = %{x:.1f} mM<br>v = %{y:.2f} µmol/s<extra></extra>",
    ))

    if conditions is not None:
        factor = conditions["temp_factor"] * conditions["ph_factor"] * conditions["stir_factor"]
        v_now = v * factor
        if conditions["denatured"]:
            v_now = np.minimum(v_now, vmax * 0.04)
        fig.add_trace(go.Scatter(
            x=s, y=v_now, mode="lines", name="At your temperature, pH & stirring",
            line=dict(color=pal["blue"], width=2),
            hovertemplate="[S] = %{x:.1f} mM<br>v = %{y:.2f} µmol/s<extra></extra>",
        ))
        y_top = max(y_top, float(v_now.max()) * 1.1)
        if current_s is not None:
            v_here = kin.michaelis_menten(current_s, vmax, km) * factor
            if conditions["denatured"]:
                v_here = min(v_here, vmax * 0.04)
            fig.add_trace(go.Scatter(
                x=[current_s], y=[v_here], mode="markers+text", name="Your [S]",
                marker=dict(size=11, color=pal["blue"], line=dict(width=2, color=pal["surface"])),
                text=[f"  v = {v_here:.2f}"], textposition="middle right",
                textfont=dict(color=pal["text"]), showlegend=False,
                hovertemplate="Your [S] = %{x:.0f} mM<br>v = %{y:.2f} µmol/s<extra></extra>",
            ))

    # Vmax ceiling and the (Km, Vmax/2) point
    fig.add_hline(y=vmax, line_dash="dash", line_width=1.5, line_color=pal["red"])
    fig.add_annotation(x=s_max, y=vmax, xanchor="right", yanchor="bottom", showarrow=False,
                       text=f"Vmax = {vmax:.1f} µmol/s", font=dict(size=12, color=pal["text"]))
    km_x = min(km, s_max)
    fig.add_shape(type="line", x0=0, x1=km_x, y0=vmax / 2, y1=vmax / 2,
                  line=dict(color=pal["text2"], width=1, dash="dot"))
    fig.add_shape(type="line", x0=km_x, x1=km_x, y0=0, y1=vmax / 2,
                  line=dict(color=pal["text2"], width=1, dash="dot"))
    fig.add_trace(go.Scatter(
        x=[km_x], y=[vmax / 2], mode="markers+text", showlegend=False,
        marker=dict(size=10, color=pal["text"], line=dict(width=2, color=pal["surface"])),
        text=[f"  ½ Vmax ({vmax / 2:.1f}) at Km = {km:.1f} mM"], textposition="middle right",
        textfont=dict(color=pal["text"], size=12),
        hovertemplate="Km = %{x:.1f} mM<br>½ Vmax = %{y:.2f}<extra></extra>",
    ))

    base_layout(fig, pal, height=380, top_margin=20)
    style_axes(fig, pal)
    fig.update_xaxes(title_text="Substrate concentration [S] (mM)", range=[0, s_max])
    fig.update_yaxes(title_text="Reaction rate v (µmol/s)", range=[0, y_top])
    return fig


def lb_chart(km, vmax, pal):
    """Lineweaver-Burk plot: 1/v against 1/[S] is a straight line."""
    s_points = np.array([2.0, 3.0, 5.0, 8.0, 12.0, 20.0, 35.0, 60.0])
    inv_s, inv_v = kin.lineweaver_burk(s_points, vmax, km)
    x_line = np.linspace(-1 / km, inv_s.max() * 1.05, 100)
    y_line = (km / vmax) * x_line + 1 / vmax

    fig = go.Figure()
    fig.add_vline(x=0, line_width=1, line_color=pal["axis"])
    fig.add_hline(y=0, line_width=1, line_color=pal["axis"])
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line, mode="lines", name="1/v = (Km/Vmax)·1/[S] + 1/Vmax",
        line=dict(color=pal["primary"], width=2),
        hovertemplate="1/[S] = %{x:.3f}<br>1/v = %{y:.3f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=inv_s, y=inv_v, mode="markers", name="Rates at [S] = 2 … 60 mM",
        marker=dict(size=9, color=pal["primary"], line=dict(width=2, color=pal["surface"])),
        hovertemplate="1/[S] = %{x:.3f} mM⁻¹<br>1/v = %{y:.3f} s/µmol<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[0, -1 / km], y=[1 / vmax, 0], mode="markers+text", showlegend=False,
        marker=dict(size=10, color=pal["text"], line=dict(width=2, color=pal["surface"])),
        text=[f"  1/Vmax = {1 / vmax:.3f}", f"−1/Km = {-1 / km:.3f}  "],
        textposition=["middle right", "top left"], textfont=dict(color=pal["text"], size=12),
        hoverinfo="skip",
    ))
    base_layout(fig, pal, height=380, top_margin=20, hovermode="closest")
    style_axes(fig, pal)
    fig.update_xaxes(title_text="1 / [S]  (mM⁻¹)")
    fig.update_yaxes(title_text="1 / v  (s/µmol)", rangemode="tozero")
    fig.add_annotation(x=0.98, y=0.04, xref="paper", yref="paper", xanchor="right", showarrow=False,
                       text=f"slope = Km/Vmax = {km / vmax:.3f}", font=dict(color=pal["text2"], size=12))
    return fig


# ---------------------------------------------------------------------------
# Temperature & pH activity profiles
# ---------------------------------------------------------------------------
def temperature_chart(optimal_temp, current_temp, pal):
    temps = np.arange(10, 80.5, 0.5)
    activity = np.array([kin.temperature_factor(t, optimal_temp) for t in temps]) * 100
    fig = go.Figure()
    fig.add_vrect(x0=kin.DENATURATION_TEMP_C, x1=80, fillcolor=pal["red"], opacity=0.10, line_width=0)
    fig.add_annotation(x=67.5, y=100, text="Denaturation zone", showarrow=False,
                       font=dict(size=11, color=pal["text2"]))
    fig.add_trace(go.Scatter(x=temps, y=activity, mode="lines", line=dict(color=pal["primary"], width=2),
                             hovertemplate="%{x:.1f} °C → %{y:.0f}% activity<extra></extra>"))
    now = kin.temperature_factor(current_temp, optimal_temp) * 100
    fig.add_trace(go.Scatter(
        x=[current_temp], y=[now], mode="markers+text", text=[f"{current_temp:g} °C: {now:.0f}%"],
        textposition="top center", textfont=dict(color=pal["text"]),
        marker=dict(size=11, color=pal["blue"], line=dict(width=2, color=pal["surface"])),
        hoverinfo="skip",
    ))
    base_layout(fig, pal, height=300, top_margin=20, hovermode="closest")
    fig.update_layout(showlegend=False)
    style_axes(fig, pal)
    fig.update_xaxes(title_text="Temperature (°C)", range=[10, 80])
    fig.update_yaxes(title_text="Relative activity (%)", range=[0, 112])
    return fig


def ph_chart(optimal_ph, current_ph, pal):
    phs = np.arange(2.0, 12.01, 0.05)
    activity = np.array([kin.ph_factor(p, optimal_ph) for p in phs]) * 100
    low, high = optimal_ph - kin.PH_STRESS_LIMIT, optimal_ph + kin.PH_STRESS_LIMIT
    fig = go.Figure()
    fig.add_vrect(x0=2, x1=max(2, low), fillcolor=pal["blue"], opacity=0.08, line_width=0)
    fig.add_vrect(x0=min(12, high), x1=12, fillcolor=pal["blue"], opacity=0.08, line_width=0)
    fig.add_annotation(x=(min(12, high) + 12) / 2, y=100, text="pH stress", showarrow=False,
                       font=dict(size=11, color=pal["text2"]))
    fig.add_trace(go.Scatter(x=phs, y=activity, mode="lines", line=dict(color=pal["primary"], width=2),
                             hovertemplate="pH %{x:.1f} → %{y:.0f}% activity<extra></extra>"))
    now = kin.ph_factor(current_ph, optimal_ph) * 100
    fig.add_trace(go.Scatter(
        x=[current_ph], y=[now], mode="markers+text", text=[f"pH {current_ph:.1f}: {now:.0f}%"],
        textposition="top center", textfont=dict(color=pal["text"]),
        marker=dict(size=11, color=pal["blue"], line=dict(width=2, color=pal["surface"])),
        hoverinfo="skip",
    ))
    base_layout(fig, pal, height=300, top_margin=20, hovermode="closest")
    fig.update_layout(showlegend=False)
    style_axes(fig, pal)
    fig.update_xaxes(title_text="pH", range=[2, 12])
    fig.update_yaxes(title_text="Relative activity (%)", range=[0, 112])
    return fig


# ---------------------------------------------------------------------------
# Comparing all enzymes & the landing-page sparkline
# ---------------------------------------------------------------------------
def compare_chart(enzymes, pal, colors, s_max=60.0):
    s = np.linspace(0, s_max, 241)
    fig = go.Figure()
    for i, enzyme in enumerate(list(enzymes.values())[: len(colors)]):
        fig.add_trace(go.Scatter(
            x=s, y=kin.michaelis_menten(s, enzyme["vmax"], enzyme["km"]), mode="lines",
            name=enzyme["name"], line=dict(color=colors[i], width=2),
            hovertemplate="%{y:.2f} µmol/s<extra>" + enzyme["name"] + "</extra>",
        ))
    base_layout(fig, pal, height=380, top_margin=20)
    style_axes(fig, pal)
    fig.update_xaxes(title_text="Substrate concentration [S] (mM)", range=[0, s_max])
    fig.update_yaxes(title_text="Reaction rate v (µmol/s)", rangemode="tozero")
    return fig


def sparkline(score, pal):
    x = np.linspace(0, 1, 60)
    y = (score / 100) * (1 - np.exp(-4 * x))
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines", line=dict(color=pal["primary"], width=2.5),
                               fill="tozeroy", fillcolor=with_alpha(pal["primary"], 0.10),
                               hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[x[-1]], y=[y[-1]], mode="markers", hoverinfo="skip",
                             marker=dict(size=9, color=pal["primary"], line=dict(width=2, color=pal["surface"]))))
    fig.update_layout(
        template="none", height=90, showlegend=False, margin=dict(l=4, r=8, t=6, b=4),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[0, 1.03]), yaxis=dict(visible=False, range=[0, 1.05]),
    )
    return fig
