"""Simulate page - the virtual enzyme lab (vessel, controls, progress chart, kinetics)."""

import time

import streamlit as st

from bioforge import catalog, charts, kinetics, state, theme
from bioforge.plot_style import CHART_CONFIG, STATIC_CONFIG
from bioforge.ui import labelled, show_python

TEMP_HELP = "Warmer fluid speeds molecular motion. Exceeding 55°C unravels (denatures) protein bonds."
PH_HELP = "Measures proton concentration. Incorrect pH warps electrostatic charges in active sites."
STIR_HELP = "Agitation prevents reactant depletion zones, ensuring substrate quickly finds open enzyme pockets."
CONC_HELP = "Initial reactant density. Initial velocity scales with [S] until saturation (Vmax)."
FRAME_DELAY_S = 0.06   # playback speed of the animation


# ---------------------------------------------------------------- callbacks
def _set_optimal():
    enzyme = state.active_enzyme()
    ss = st.session_state
    ss.sim_temp = int(enzyme["optimal_temp"])
    ss.sim_ph = float(enzyme["optimal_ph"])
    ss.sim_stir = 2
    ss.sim_conc = 25


def _heat_denature():
    st.session_state.sim_temp = 72


def _reset_experiment():
    ss = st.session_state
    ss.sim_runs = []
    ss.sim_current = None
    ss.sim_run_counter = 0


# ------------------------------------------------------------ text helpers
def _status(k, running, finished):
    if k["denatured"]:
        return "Status: Denatured", "red", ":material/warning:"
    if running:
        return "Status: Reaction Live", "green", ":material/play_circle:"
    if finished:
        return "Status: Completed Run", "primary", ":material/check_circle:"
    return "Status: Idle / Ready to Run", "gray", ":material/radio_button_unchecked:"


def _active_site(k):
    if k["denatured"]:
        return "Active Site: Denatured", "red"
    if k["ph_stressed"]:
        return "Active Site: Warped/Stress", "blue"
    if k["efficiency"] > 75:
        return "Active Site: Peak Binding", "green"
    return "Active Site: Functional", "green"


def _yield_note(k, progress, running):
    if k["denatured"]:
        return ":red[Thermal Arrest]"
    if k["ph_stressed"]:
        return ":blue[Yield Constrained]"
    if progress > 80:
        return ":green[Near Peak Yield]"
    if running:
        return "Active Catalysis"
    return "Awaiting start"


def _evaluation(k, enzyme, temp, ph, progress, running):
    """Plain-language evaluation box (same wording as the website)."""
    if k["denatured"]:
        st.error(
            "Enzyme has denatured due to excessive thermal agitation (>55°C). High heat ruptures "
            "secondary and tertiary hydrogen bonds, collapsing the active catalytic pocket.",
            icon=":material/insights:",
        )
    elif k["ph_stressed"]:
        st.warning(
            f"Sub-optimal pH ({ph:.1f} vs optimal {enzyme['optimal_ph']:.1f}) induces ionic charge "
            "disruption on active-site side chains, reducing binding and yield.",
            icon=":material/insights:",
        )
    elif progress > 85:
        st.success(
            "Excellent conversion efficiency! Substrate has nearly reached equilibrium exhaustion "
            "with high catalytic turnover.",
            icon=":material/insights:",
        )
    elif running:
        st.info(
            f"Steady conversion underway at {temp}°C and pH {ph:.1f}. Substrate is binding "
            f"rapidly to {enzyme['name']} active sites.",
            icon=":material/insights:",
        )
    else:
        st.info(
            "Ready to start. Click 'Start Simulation' to observe catalysis dynamics and product "
            "accumulation over time.",
            icon=":material/insights:",
        )


# ---------------------------------------------------------------- the page
def render():
    ss = st.session_state
    pal = theme.palette()
    run_colors = theme.categorical()
    enzymes = ss.enzymes
    enzyme = state.active_enzyme()

    temp, ph, stir, conc = ss.sim_temp, ss.sim_ph, ss.sim_stir, ss.sim_conc
    k = kinetics.compute_kinetics(enzyme, temp, ph, stir, conc)
    params = {"enzyme_id": enzyme["id"], "temp": temp, "ph": ph, "stir": stir, "conc": conc}
    current = ss.sim_current
    finished = current is not None and current["params"] == params

    # ------------------------------------------------------------ header
    head_l, head_r = st.columns([1.5, 1.5], vertical_alignment="bottom")
    with head_l:
        st.badge("Kinetic Engine v2.4", icon=":material/bolt:", color="green")
        st.title("Enzyme Reaction Simulator")
        st.markdown("Test how temperature, pH, stirring, and concentration change enzymatic conversion in real-time.")
    with head_r:
        with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
            status_slot = st.empty()
            st.button("Reset Experiment", icon=":material/restart_alt:", on_click=_reset_experiment,
                      key="sim_reset")
            start = st.button("Start Simulation", type="primary", icon=":material/play_arrow:",
                              key="sim_start")

    # --------------------------------------------------- three columns
    col1, col2, col3 = st.columns(3, border=True, gap="medium")

    with col1:
        st.subheader(":material/counter_1: Enzyme & Substrate Pair")
        st.selectbox(
            "Select Biochemical Reaction", list(enzymes), key="active_enzyme_id",
            format_func=lambda i: catalog.enzyme_label(enzymes[i]), on_change=state.on_enzyme_changed,
        )
        st.caption(enzyme["subtitle"])
        with st.container(border=True):
            st.caption("REACTION TYPE")
            st.badge(enzyme["reaction_type"], color="green")
            labelled("Optimum range", f"{enzyme['optimal_temp']}°C • pH {enzyme['optimal_ph']:.1f}")
            labelled("Substrate → Product", f"{enzyme['substrate']} → {enzyme['product']}")
            labelled("Enzyme class", enzyme.get("ec_number", "—"))
            st.caption("CATALYTIC MECHANISM")
            st.markdown(enzyme["mechanism"])
        st.info(f"**Beginner Tip** — {enzyme['beginner_tip']}", icon=":material/lightbulb:")

    with col2:
        st.subheader(":material/counter_2: Reaction Vessel (Live)")
        badge_slot = st.empty()
        vessel_slot = st.empty()
        if k["denatured"]:
            st.error("Thermal Denaturation! Protein folded bonds destroyed (>55°C).", icon=":material/warning:")
        progress_slot = st.empty()

    with col3:
        st.subheader(":material/counter_3: Reaction Controls")
        st.slider("Temperature", 10, 80, key="sim_temp", format="%d°C", help=TEMP_HELP)
        st.caption(f"10°C (Cold) · **{enzyme['optimal_temp']}°C (Optimal)** · :red[80°C (Denatures)]")
        st.slider("Acidity (pH)", 2.0, 12.0, step=0.1, key="sim_ph", format="pH %.1f", help=PH_HELP)
        st.caption(f"pH 2.0 (Acidic) · **pH {enzyme['optimal_ph']:.1f} (Optimal)** · pH 12.0 (Basic)")
        st.select_slider("Stirring Rate", options=[1, 2, 3], key="sim_stir",
                         format_func=kinetics.STIR_LABELS.get, help=STIR_HELP)
        st.slider("Substrate Concentration [S]", 5, 50, key="sim_conc", format="%d mM", help=CONC_HELP)
        st.caption("5 mM (Sparse) · **25 mM** · 50 mM (Saturated)")
        b1, b2 = st.columns(2)
        b1.button("⚡ Set Optimal", on_click=_set_optimal, width="stretch", key="sim_opt")
        b2.button("\U0001f525 Heat Denature", on_click=_heat_denature, width="stretch", key="sim_heat")

    # ----------------------------------------------- lower section
    lower_l, lower_r = st.columns([2, 1], border=True, gap="medium")
    with lower_l:
        tab_progress, tab_mm, tab_lb, tab_env = st.tabs(
            ["Reaction Progress", "Michaelis–Menten Curve", "Lineweaver–Burk Plot", "Temperature & pH"]
        )
        with tab_progress:
            st.markdown("**Reaction Progress Over Time**")
            st.caption("Accumulation of catalyzed product molecules across the reaction interval. "
                       "Earlier runs stay on the chart so you can compare conditions.")
            chart_slot = st.empty()
        with tab_mm:
            st.caption("Green: the enzyme at its optimum. Blue: the same enzyme under the conditions "
                       "you set on the right (temperature × pH × stirring modifiers).")
            st.plotly_chart(charts.mm_chart(enzyme["km"], enzyme["vmax"], pal, conditions=k, current_s=conc),
                            config=CHART_CONFIG, key="sim_mm")
        with tab_lb:
            st.caption("Taking 1/v and 1/[S] turns the curve into a straight line: "
                       "the intercepts give Km and Vmax directly.")
            st.plotly_chart(charts.lb_chart(enzyme["km"], enzyme["vmax"], pal), config=CHART_CONFIG, key="sim_lb")
        with tab_env:
            e1, e2 = st.columns(2)
            e1.plotly_chart(charts.temperature_chart(enzyme["optimal_temp"], temp, pal), config=CHART_CONFIG, key="sim_tprof")
            e2.plotly_chart(charts.ph_chart(enzyme["optimal_ph"], ph, pal), config=CHART_CONFIG, key="sim_phprof")
            st.caption(f"Temperature factor × pH factor × stirring factor = "
                       f"{k['temp_factor']:.2f} × {k['ph_factor']:.2f} × {k['stir_factor']:.2f}")

    with lower_r:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader("Experiment Metrics")
            st.badge("Active Run", color="green")
        metrics_slot = st.empty()
        eval_slot = st.empty()
        if finished:
            table = kinetics.export_table(current["df"], enzyme, temp, ph)
            st.download_button(
                "Export Data (CSV / Notebook)", table.to_csv(index=False),
                file_name=f"bioforge_{enzyme['id']}_simulation.csv", mime="text/csv",
                icon=":material/download:", width="stretch", key="sim_export",
            )
        else:
            st.button("Export Data (CSV / Notebook)", icon=":material/download:", width="stretch",
                      disabled=True, key="sim_export_off", help="Run a simulation first")

    # ------------------------------------------------ dynamic drawing
    def draw(progress, elapsed, runs, current_id, running, frame, suffix=""):
        label, color, icon = _status(k, running, finished and not running)
        status_slot.badge(label, color=color, icon=icon)

        site_text, site_color = _active_site(k)
        with badge_slot.container(horizontal=True):
            st.badge(site_text, color=site_color)
            st.badge(f"Chamber: Sealed ({kinetics.STIR_LABELS[stir].split(' ')[0]} {stir}x)", color="gray")
            st.badge(f"V: {k['effective_rate'] if (running or progress > 0) else 0.0:.1f} µmol/s",
                     icon=":material/speed:", color="blue")

        vessel = charts.vessel_figure(progress, k, stir, temp, ph, enzyme["optimal_ph"], enzyme["vmax"],
                                      active=running or progress > 0, pal=pal, frame=frame)
        vessel_slot.plotly_chart(vessel, config=STATIC_CONFIG, key=f"sim_vessel{suffix}")

        remaining = max(0.0, conc * (1 - progress / 100))
        with progress_slot.container():
            st.progress(min(progress, 100) / 100, text=f"**Reaction Progress** — {progress:.1f}% Complete")
            st.caption(f"Substrate: {remaining:.1f} mM · Elapsed: {elapsed:.1f}s / {kinetics.RUN_DURATION_S:.1f}s")

        chart_slot.plotly_chart(charts.progress_chart(runs, current_id, pal, run_colors),
                                config=CHART_CONFIG, key=f"sim_progress{suffix}")

        product = conc * (progress / 100) * kinetics.VESSEL_VOLUME_ML
        with metrics_slot.container():
            m1, m2 = st.columns(2)
            m1.metric("Product Formed (µmol)", f"{product:.1f}", border=True)
            m2.metric("Reaction Yield", f"{progress:.1f}%", border=True)
            m3, m4 = st.columns(2)
            m3.metric("Velocity v₀ (µmol/s)", f"{k['effective_rate']:.2f}", border=True,
                      help="Initial reaction velocity at the current temperature, pH, stirring and [S]")
            m4.metric("Efficiency", f"{k['efficiency']}%", border=True)
            st.caption(f"{enzyme['product'] if progress > 0 else 'Initial phase'} · "
                       f"{_yield_note(k, progress, running)}")
        with eval_slot.container():
            _evaluation(k, enzyme, temp, ph, progress, running)

    # static view (idle, or the finished run)
    history = ss.sim_runs
    if finished:
        last = current["df"].iloc[-1]
        draw(last["progress_pct"], last["time_s"], history, current["id"], running=False, frame=current["id"])
    else:
        draw(0.0, 0.0, history, None, running=False, frame=0)

    # ------------------------------------------ run + animate the experiment
    if start:
        run_df = kinetics.simulate_reaction(enzyme, temp, ph, stir, conc)
        run_id = ss.sim_run_counter + 1
        label = (f"Run {run_id} · {enzyme['name']} · {temp}°C · pH {ph:.1f} · "
                 f"{stir}x · {conc} mM")
        previous = [r for r in history if r["id"] != run_id]
        for frame, row in enumerate(run_df.itertuples(), start=1):
            partial = {"id": run_id, "label": label, "df": charts.partial_run(run_df, row.time_s)}
            draw(row.progress_pct, row.time_s, previous + [partial], run_id, running=True,
                 frame=frame, suffix=f"_f{frame}")
            time.sleep(FRAME_DELAY_S)

        new_run = {"id": run_id, "label": label, "df": run_df, "params": params}
        ss.sim_run_counter = run_id
        ss.sim_current = new_run
        ss.sim_runs = (history + [new_run])[-state.MAX_SAVED_RUNS:]
        st.rerun()

    show_python(
        "\U0001f40d The Python behind this simulator",
        kinetics.compute_kinetics, kinetics.simulate_reaction,
    )
