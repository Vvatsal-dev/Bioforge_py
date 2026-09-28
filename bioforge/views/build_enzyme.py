"""Build Enzyme page - design a custom enzyme and preview its kinetics live."""

import streamlit as st

from bioforge import catalog, charts, kinetics, state, theme
from bioforge.plot_style import CHART_CONFIG
from bioforge.ui import show_python

RESET_VALUES = {
    "b_name": "Syn-Hydrolase Beta", "b_substrate": "Cellulose", "b_product": "Cellobiose",
    "b_km": 7.5, "b_vmax": 12.0, "b_temp": 45, "b_ph": 6.0,
}


# ---------------------------------------------------------------- callbacks
def _load_preset():
    ss = st.session_state
    preset = ss.enzymes.get(ss.b_preset)
    if preset:
        ss.b_name = f"Engineered {preset['name']}"
        ss.b_substrate = preset["substrate"]
        ss.b_product = preset["product"]
        ss.b_km = float(preset["km"])
        ss.b_vmax = float(preset["vmax"])
        ss.b_temp = int(preset["optimal_temp"])
        ss.b_ph = float(preset["optimal_ph"])
    ss.b_preset = None       # show the placeholder again


def _reset_form():
    for key, value in RESET_VALUES.items():
        st.session_state[key] = value
    st.session_state.b_saved_id = None


def _set(key, value):
    st.session_state[key] = value


def _save_construct():
    """Create the enzyme from the form and add it to the shared library."""
    ss = st.session_state
    enzyme = catalog.create_custom_enzyme(
        ss.b_name, ss.b_substrate, ss.b_product, ss.b_km, ss.b_vmax, ss.b_temp, ss.b_ph,
        existing_ids=ss.enzymes.keys(),
    )
    state.add_enzyme(enzyme)
    ss.b_saved_id = enzyme["id"]
    return enzyme["id"]


# ---------------------------------------------------------------- the page
def render():
    ss = st.session_state
    pal = theme.palette()
    enzymes = ss.enzymes
    if ss.pop("b_toast", False) and ss.b_saved_id in enzymes:
        st.toast(f"Saved \u201c{enzymes[ss.b_saved_id]['name']}\u201d to your enzyme library",
                 icon=":material/check_circle:")

    head_l, head_r = st.columns([1.4, 1.6], vertical_alignment="bottom")
    with head_l:
        st.badge("Biocatalyst Studio v2.4", icon=":material/biotech:", color="green")
        st.title("Custom Enzyme Builder")
        st.markdown("Design a custom enzyme by configuring core kinetic parameters: binding affinity "
                    "and catalytic turnover speed.")
    with head_r:
        with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="bottom"):
            st.selectbox(
                "Load preset", list(enzymes), key="b_preset", index=None, on_change=_load_preset,
                placeholder="Load Preset Enzyme...", label_visibility="collapsed", width=260,
                format_func=lambda i: f"{enzymes[i]['name']} (Km: {enzymes[i]['km']:g}, Vmax: {enzymes[i]['vmax']:g})",
            )
            st.button("Reset", on_click=_reset_form, key="b_reset")
            if st.button("Test in Simulator", type="primary", icon=":material/play_arrow:", key="b_test_top"):
                state.go("simulate", _save_construct())

    # success banner after saving
    saved_id = ss.b_saved_id
    if saved_id and saved_id in enzymes:
        with st.container(border=True, horizontal=True, vertical_alignment="center"):
            st.success(
                f"**Enzyme \"{enzymes[saved_id]['name']}\" saved successfully!** This custom construct is now "
                "available in the Simulate workbench dropdown and the Specifications table.",
                icon=":material/check_circle:", width="stretch",
            )
            if st.button("Simulate Now", icon=":material/arrow_forward:", icon_position="right", key="b_sim_now"):
                state.go("simulate", saved_id)

    left, right = st.columns(2, border=True, gap="large")

    # ------------------------------------------------------------ the form
    with left:
        st.subheader(":material/counter_1: Kinetic Parameters Form")
        st.text_input("Enzyme Construct Name", key="b_name", placeholder="e.g., Synthetic Amylase-X")
        c1, c2 = st.columns(2)
        c1.text_input("Substrate Name", key="b_substrate", placeholder="e.g., Ethanol")
        c2.text_input("Product Name", key="b_product", placeholder="e.g., Acetaldehyde")

        with st.container(border=True):
            st.slider("Binding Affinity (Km) — Michaelis Constant", 0.5, 30.0, step=0.5, key="b_km",
                      format="%.1f mM")
            st.caption("Concentration of [S] needed for 50% max speed. Lower = tighter grip!")
            with st.container(horizontal=True):
                st.button("Super Sticky (1.5 mM)", on_click=_set, args=("b_km", 1.5), key="b_km1", type="tertiary")
                st.button("Balanced (8.0 mM)", on_click=_set, args=("b_km", 8.0), key="b_km2", type="tertiary")
                st.button("Loose (22.0 mM)", on_click=_set, args=("b_km", 22.0), key="b_km3", type="tertiary")

        with st.container(border=True):
            st.slider("Max Velocity (Vmax) — Catalytic Ceiling", 2.0, 35.0, step=0.5, key="b_vmax",
                      format="%.1f µmol/s")
            st.caption("Maximum theoretical conversion rate when all active sites are saturated.")
            with st.container(horizontal=True):
                st.button("Relaxed (5.0 µmol/s)", on_click=_set, args=("b_vmax", 5.0), key="b_v1", type="tertiary")
                st.button("Steady Worker (15.0 µmol/s)", on_click=_set, args=("b_vmax", 15.0), key="b_v2", type="tertiary")
                st.button("Turbo-Charged (30.0 µmol/s)", on_click=_set, args=("b_vmax", 30.0), key="b_v3", type="tertiary")

        c3, c4 = st.columns(2, border=True)
        with c3:
            st.slider("Optimal Temp", 20, 65, key="b_temp", format="%d°C")
            st.caption("Human Body ~37°C")
        with c4:
            st.slider("Optimal pH", 2.0, 11.0, step=0.1, key="b_ph", format="pH %.1f")
            st.caption("Neutral ~7.0")

        st.info(
            "**The Master Chef Analogy** — Think of **Km** as how easily the chef grabs an onion "
            "(lower = faster pick up), and **Vmax** as how quickly they can chop it once it's in their hand.",
            icon=":material/psychology:",
        )

    # ---------------------------------------------------- live preview
    km, vmax = ss.b_km, ss.b_vmax
    with right:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader(":material/counter_2: Live Performance Preview")
            st.badge("Construct Active", color="green")
        tab_mm, tab_lb = st.tabs(["Michaelis-Menten Curve: v vs [S]", "Lineweaver-Burk: 1/v vs 1/[S]"])
        with tab_mm:
            st.latex(r"v = \frac{V_{max}\,[S]}{K_m + [S]}")
            st.plotly_chart(charts.mm_chart(km, vmax, pal), config=CHART_CONFIG, key="b_mm")
        with tab_lb:
            st.latex(r"\frac{1}{v} = \frac{K_m}{V_{max}}\cdot\frac{1}{[S]} + \frac{1}{V_{max}}")
            st.plotly_chart(charts.lb_chart(km, vmax, pal), config=CHART_CONFIG, key="b_lb")

        m1, m2, m3 = st.columns(3)
        m1.metric("Target Grip", kinetics.affinity_label(km), border=True)
        m2.metric("Turnover Speed", kinetics.turnover_label(vmax), border=True)
        m3.metric("Specificity", f"{kinetics.specificity_constant(vmax, km):.2f}", border=True,
                  help="Vmax / Km: higher means the enzyme is both grippy and fast")

        if st.button("Save Enzyme Construct", type="primary", icon=":material/save:", width="stretch", key="b_save"):
            _save_construct()
            ss.b_toast = True
            st.rerun()
        if st.button("Send to Simulation Workbench", icon=":material/open_in_new:", width="stretch", key="b_send"):
            state.go("simulate", _save_construct())

    show_python(
        "\U0001f40d The Python behind the builder",
        kinetics.michaelis_menten, kinetics.lineweaver_burk, catalog.create_custom_enzyme,
    )
