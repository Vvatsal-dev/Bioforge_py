"""Bioreactor page - fermentation dataset, time filter, averages, peak growth, charts."""

import numpy as np
import pandas as pd
import streamlit as st

from bioforge import bioreactor as br
from bioforge import theme
from bioforge.plot_style import CHART_CONFIG
from bioforge.ui import show_python

BUILT_IN = "Built-in dataset"
UPLOAD = "Upload my own CSV"


@st.cache_data
def _builtin():
    return br.load_builtin_dataset()


@st.cache_data
def _template_csv():
    return _builtin()[br.ALL_COLUMNS].to_csv(index=False)


def _get_dataset():
    """Return (DataFrame, name, is_builtin) based on the user's choice."""
    ss = st.session_state
    if ss.br_source == UPLOAD:
        up_col, tpl_col = st.columns([3, 1], vertical_alignment="bottom")
        with up_col:
            file = st.file_uploader("Upload a fermentation CSV", type=["csv"], key="br_file",
                                    help="Required columns: " + ", ".join(br.REQUIRED_COLUMNS))
        with tpl_col:
            st.download_button("Download CSV template", _template_csv(), "bioforge_fermentation_template.csv",
                               mime="text/csv", icon=":material/download:", width="stretch", key="br_tpl")
        if file is None:
            st.info("No file yet, so the built-in E. coli dataset is shown. Your CSV needs the columns "
                    f"`{'`, `'.join(br.REQUIRED_COLUMNS)}` (and optionally `{br.MU}`).",
                    icon=":material/upload_file:")
            return _builtin(), "E. coli K-12 batch (built-in)", True
        try:
            df, notes = br.parse_uploaded_csv(file)
        except br.DatasetError as err:
            st.error(f"**{file.name}** could not be used: {err}. Showing the built-in dataset instead.",
                     icon=":material/error:")
            return _builtin(), "E. coli K-12 batch (built-in)", True
        st.success(f"Loaded **{file.name}**: {len(df)} readings from {df[br.TIME].min():g} h "
                   f"to {df[br.TIME].max():g} h.", icon=":material/check_circle:")
        for note in notes:
            st.caption(f":material/info: {note}")
        return df, file.name, False
    return _builtin(), "E. coli K-12 batch (built-in)", True


def _fmt(value, decimals, unit=""):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    return f"{value:.{decimals}f}{(' ' + unit) if unit else ''}"


def render():
    ss = st.session_state
    pal = theme.palette()

    # ------------------------------------------------------------ header
    head_l, head_r = st.columns([3, 1.3], vertical_alignment="center")
    with head_l:
        st.badge("NEW · Microbial Kinetics Suite", icon=":material/microbiology:", color="green")
        st.title("Bioreactor Fermentation & Microbial Kinetics")
        st.markdown("A 24-hour aerobic batch culture of *Escherichia coli* K-12. Filter the readings by "
                    "time, average dissolved oxygen or glucose, and pinpoint the moment of fastest growth.")
    with head_r:
        with st.container(border=True):
            st.markdown("#### :material/functions: Growth maths")
            st.latex(r"\mu = \frac{d\ln X}{dt} \qquad \frac{dX}{dt} \approx \frac{\Delta OD_{600}}{\Delta t}")

    # ------------------------------------------------------------ dataset
    with st.container(border=True):
        st.subheader(":material/counter_1: Dataset")
        st.segmented_control("Data source", [BUILT_IN, UPLOAD], key="br_source", required=True,
                             label_visibility="collapsed")
        df, name, is_builtin = _get_dataset()
        with st.expander("About this dataset", icon=":material/info:"):
            if is_builtin:
                info_col, cols_col = st.columns(2, gap="large")
                with info_col:
                    st.markdown("**Experiment set-up**")
                    st.markdown("\n".join(f"- **{k}:** {v}" for k, v in br.EXPERIMENT_INFO.items()))
                    st.caption("Generated with scipy from a Monod growth model with a Baranyi lag phase, an "
                               "oxygen mass balance (kLa = 220 h⁻¹) and slow cell lysis after "
                               "starvation, then sampled every 30 min with realistic sensor noise.")
                with cols_col:
                    st.markdown("**Columns**")
                    st.markdown(
                        f"- `{br.TIME}`: hours since inoculation\n"
                        f"- `{br.OD}`: optical density at 600 nm (biomass ≈ OD × {br.OD_TO_DCW} g/L)\n"
                        f"- `{br.DO}`: dissolved oxygen, % of air saturation\n"
                        f"- `{br.GLUCOSE}`: residual glucose (g/L)\n"
                        f"- `{br.MU}`: d ln(OD)/dt (h⁻¹)"
                    )
            st.dataframe(df[br.ALL_COLUMNS], hide_index=True, height=220, width="stretch")

    # ----------------------------------------------------------- controls
    t_min, t_max = float(df[br.TIME].min()), float(df[br.TIME].max())
    steps = np.diff(df[br.TIME].to_numpy(dtype=float))
    step = float(np.round(np.median(steps), 3)) if len(steps) else 0.5
    if not (t_min <= ss.br_cutoff <= t_max):
        ss.br_cutoff = t_min

    with st.container(border=True):
        st.subheader(":material/counter_2: Interactive Controls")
        c1, c2, c3 = st.columns([2.2, 1.6, 1], gap="large")
        with c1:
            cutoff = st.slider("Filter Readings After Time Point (t_cutoff)", t_min, t_max, step=step,
                               key="br_cutoff", format="%.1f h",
                               help="Only readings with time ≥ t_cutoff are used for the averages below.")
        with c2:
            param = st.radio("Parameter to observe", list(br.PARAMETERS), key="br_param", horizontal=True)
        with c3:
            layout = st.segmented_control("Chart layout", ["Overlay", "Stacked"], key="br_layout", required=True,
                                          help="Overlay = one chart with a second y-axis. Stacked = two aligned panels.")

    info = br.PARAMETERS[param]
    column, unit, short = info["column"], info["unit"], info["short"]

    # ---------------------------------------------------------- analytics
    avg_after, avg_all, n_window = br.post_cutoff_average(df, column, cutoff)
    peak = br.find_peak_growth(df)
    mu_max = br.find_mu_max(df)
    phases = br.detect_phases(df)
    events = br.key_events(df)
    yield_xs = br.biomass_yield(df)

    st.subheader(":material/counter_3: Core Analytics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        f"Avg {short} for t ≥ {cutoff:g} h", _fmt(avg_after, info["decimals"], unit),
        delta=None if np.isnan(avg_after) else f"{avg_after - avg_all:+.{info['decimals']}f} {unit} vs whole-run avg ({avg_all:.{info['decimals']}f})",
        delta_color="off", border=True,
        help="Mean of every reading at or after the cutoff, compared with the mean of the whole run.",
    )
    m2.metric(
        "Peak growth time (max ΔOD600/Δt)", f"{peak['time']:.1f} h",
        delta=f"{peak['rate']:.2f} OD/h at OD {peak['od']:.2f}", delta_color="off", delta_arrow="off",
        border=True, help="The reading where the absolute growth rate dOD600/dt is highest.",
    )
    m3.metric(
        "Max specific growth rate μmax", f"{mu_max['mu']:.2f} h⁻¹",
        delta=f"at {mu_max['time']:.1f} h · doubling ≈ {mu_max['doubling_min']:.0f} min",
        delta_color="off", delta_arrow="off", border=True,
        help="μ = d ln(OD)/dt. Doubling time = ln 2 / μmax.",
    )
    m4.metric(
        "Readings in filtered window", f"{n_window} / {len(df)}",
        delta=f"{cutoff:g} h → {t_max:g} h", delta_color="off", delta_arrow="off", border=True,
    )

    # ------------------------------------------------------------- charts
    with st.container(border=True):
        st.markdown(f"**Biomass (OD600) vs time with {param.lower()}**  ·  {name}")
        fig = br.growth_chart(df, cutoff, param, peak, phases, pal, layout=layout)
        st.plotly_chart(fig, config=CHART_CONFIG, key="br_main")
        st.caption("Grey area: readings excluded by your filter · dashed line: t_cutoff · "
                   "★ peak growth rate · phase names along the top are detected automatically.")

    r1, r2 = st.columns(2, border=True, gap="medium")
    with r1:
        st.markdown("**Absolute growth rate  dOD600/dt**")
        st.plotly_chart(br.rate_chart(df, br.GROWTH_RATE, peak, pal, "OD/h"), config=CHART_CONFIG, key="br_rate")
    with r2:
        st.markdown("**Specific growth rate  μ = d ln(OD600)/dt**")
        st.plotly_chart(br.rate_chart(df, br.MU, mu_max, pal, "h⁻¹", color_key="blue"),
                        config=CHART_CONFIG, key="br_mu")
    depleted = events["glucose_depleted_at"]
    ending = (", just before the glucose runs out." if depleted is not None and peak["time"] <= depleted else ".")
    st.caption(
        f"Why two different peaks? dX/dt = μ · X. μ (how fast each cell divides) peaks at "
        f"{mu_max['time']:.1f} h, but the absolute rate keeps climbing while the population grows, so it peaks "
        f"at {peak['time']:.1f} h{ending}"
    )

    # ------------------------------------------------ phases + insights
    p1, p2 = st.columns([1.2, 1], border=True, gap="medium")
    with p1:
        st.markdown("**Growth phases (auto-detected)**")
        st.dataframe(
            pd.DataFrame(phases), hide_index=True, width="stretch",
            column_config={
                "Start (h)": st.column_config.NumberColumn(format="%.1f"),
                "End (h)": st.column_config.NumberColumn(format="%.1f"),
                "Duration (h)": st.column_config.NumberColumn(format="%.1f"),
                "Mean μ (1/h)": st.column_config.NumberColumn(format="%.3f"),
            },
        )
    with p2:
        st.markdown("**Process insights**")
        lines = []
        if events["glucose_depleted_at"] is not None:
            lines.append(f"Glucose was exhausted (< {br.GLUCOSE_DEPLETED_GL} g/L) at **{events['glucose_depleted_at']:.1f} h**.")
        lines.append(f"Dissolved oxygen fell to its minimum of **{events['do_min']:.1f}%** at {events['do_min_time']:.1f} h, "
                     "when the cells were respiring fastest.")
        if events["do_spike_time"] is not None:
            lines.append(f"DO spiked by **+{events['do_spike_size']:.0f} points** at {events['do_spike_time']:.1f} h: the "
                         "classic signal that the carbon source has run out.")
        lines.append(f"Maximum cell density: **OD {events['od_max']:.2f}** at {events['od_max_time']:.1f} h "
                     f"(≈ {events['od_max'] * br.OD_TO_DCW:.2f} g dry cells/L).")
        if not np.isnan(yield_xs):
            lines.append(f"Biomass yield Yₓ/ₛ ≈ **{yield_xs:.2f} g cells per g glucose** "
                         "(aerobic E. coli on glucose is typically 0.4–0.5).")
        st.markdown("\n".join(f"- {line}" for line in lines))

    # --------------------------------------------------- filtered table
    filtered = br.filter_after(df, cutoff)
    with st.container(border=True):
        top_l, top_r = st.columns([3, 1], vertical_alignment="center")
        top_l.markdown(f"**Filtered readings (t ≥ {cutoff:g} h)** · {len(filtered)} rows")
        top_r.download_button("Download filtered CSV", filtered[br.ALL_COLUMNS + [br.GROWTH_RATE]].to_csv(index=False),
                              f"bioreactor_after_{cutoff:g}h.csv", mime="text/csv", icon=":material/download:",
                              width="stretch", key="br_dl")
        st.dataframe(
            filtered, hide_index=True, width="stretch", height=280,
            column_config={
                br.TIME: st.column_config.NumberColumn("Time (h)", format="%.1f"),
                br.OD: st.column_config.NumberColumn("OD600", format="%.3f"),
                br.DO: st.column_config.ProgressColumn("DO (%)", format="%.1f", min_value=0, max_value=100),
                br.GLUCOSE: st.column_config.NumberColumn("Glucose (g/L)", format="%.3f"),
                br.MU: st.column_config.NumberColumn("μ (1/h)", format="%.3f"),
                br.GROWTH_RATE: st.column_config.NumberColumn("dOD/dt (OD/h)", format="%.3f"),
            },
        )

    show_python(
        "\U0001f40d The Python behind these numbers",
        br.filter_after, br.post_cutoff_average, br.add_growth_rates, br.find_peak_growth, br.detect_phases,
    )
