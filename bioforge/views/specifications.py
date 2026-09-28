"""Specifications page - equation cards and the live table of registered enzymes."""

import pandas as pd
import streamlit as st

from bioforge import charts, kinetics, state, theme
from bioforge.plot_style import CHART_CONFIG
from bioforge.specs import CATEGORIES, EQUATIONS


def _category_label(cat_id):
    if cat_id == "all":
        return f"{CATEGORIES['all']} ({len(EQUATIONS)})"
    return CATEGORIES[cat_id]


def _equation_card(eq):
    with st.container(border=True, height="stretch"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"### :gray[{eq['number']}]")
            st.badge(eq["badge"], color="green")
        st.subheader(eq["title"])
        st.caption(eq["subtitle"])
        st.latex(eq["formula"])
        st.markdown("**Variables breakdown**")
        st.markdown("\n".join(f"- ${sym}$ — {meaning}" for sym, meaning in eq["variables"]))
        st.info(f"**In plain English:** {eq['plain']}", icon=":material/translate:")
        st.caption(f":material/science: **Lab observation:** {eq['example']}")


def _enzyme_card(enz):
    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader(enz["name"])
            if enz.get("is_custom"):
                st.badge("Custom", color="green")
            else:
                st.badge("Built-in", color="gray")
        st.markdown(f":green[**{enz['substrate']} → {enz['product']}**]")
        a, b = st.columns(2)
        a.metric("Michaelis (Km)", f"{enz['km']:.1f} mM")
        b.metric("Max Velocity (Vmax)", f"{enz['vmax']:.1f} µmol/s")
        c, d = st.columns(2)
        c.metric("Optimal Temp", f"{enz['optimal_temp']}°C")
        d.metric("Optimal pH", f"pH {enz['optimal_ph']:.1f}")
        st.caption(f"Specificity Constant (Vmax / Km): **{kinetics.specificity_constant(enz['vmax'], enz['km']):.2f}**")
        if st.button("Simulate in Lab", type="primary", icon=":material/arrow_forward:", icon_position="right",
                     width="stretch", key=f"spec_sim_{enz['id']}"):
            state.go("simulate", enz["id"])


def render():
    ss = st.session_state
    pal = theme.palette()
    enzymes = ss.enzymes

    head_l, head_r = st.columns([3, 1.2], vertical_alignment="center")
    with head_l:
        st.badge("Theoretical Foundations", icon=":material/menu_book:", color="green")
        st.title("Kinetic Specifications & Equations")
        st.markdown("The foundational mathematical and thermodynamic models powering BioForge's "
                    "real-time catalytic engine and bioreactor analytics.")
    with head_r:
        with st.container(border=True):
            st.markdown("#### :material/functions: Standard Formulae")
            st.caption("Michaelis-Menten • Lineweaver-Burk • Arrhenius • Monod")

    # ---------------------------------------------------- equation cards
    choice = st.pills("Filter equations", list(CATEGORIES), key="spec_category",
                      format_func=_category_label, required=True, label_visibility="collapsed")
    shown = EQUATIONS if choice in (None, "all") else [e for e in EQUATIONS if e["category"] == choice]
    for i in range(0, len(shown), 2):
        cols = st.columns(2, gap="medium")
        for col, eq in zip(cols, shown[i:i + 2]):
            with col:
                _equation_card(eq)

    st.space("large")

    # ---------------------------------------- registered enzyme profiles
    with st.container(border=True):
        top_l, top_r = st.columns([3, 1], vertical_alignment="bottom")
        with top_l:
            st.badge("Live Shared Store", color="green")
            st.header("Registered Catalyst Kinetic Profiles")
            st.markdown("Directly bound to the shared enzymes data store. Parameters entered in the Custom "
                        "Enzyme Builder instantly appear here and in the Simulate engine.")
        with top_r:
            if st.button("Add Custom Enzyme", icon=":material/add_circle:", key="spec_add"):
                state.go("build")

        items = list(enzymes.values())
        for i in range(0, len(items), 3):
            cols = st.columns(3, gap="medium")
            for col, enz in zip(cols, items[i:i + 3]):
                with col:
                    _enzyme_card(enz)

        tab_curves, tab_table = st.tabs(["Compare Michaelis-Menten curves", "Kinetic data table"])
        with tab_curves:
            st.plotly_chart(charts.compare_chart(enzymes, pal, theme.categorical()),
                            config=CHART_CONFIG, key="spec_compare")
        with tab_table:
            table = pd.DataFrame(
                [
                    {
                        "Enzyme": e["name"], "Substrate": e["substrate"], "Product": e["product"],
                        "Km (mM)": e["km"], "Vmax (µmol/s)": e["vmax"],
                        "Optimal T (°C)": e["optimal_temp"], "Optimal pH": e["optimal_ph"],
                        "Vmax/Km": round(kinetics.specificity_constant(e["vmax"], e["km"]), 2),
                        "Type": "Custom" if e.get("is_custom") else "Built-in",
                    }
                    for e in enzymes.values()
                ]
            )
            st.dataframe(table, hide_index=True, width="stretch")
            st.download_button("Download table (CSV)", table.to_csv(index=False), "bioforge_enzymes.csv",
                               mime="text/csv", icon=":material/download:", key="spec_dl")

    st.space("large")

    # ---------------------------------------------------------------- CTA
    with st.container(border=True, horizontal=True, vertical_alignment="center"):
        with st.container():
            st.subheader("Want to see these equations in motion?")
            st.markdown("Run real experiments in the simulator, configure custom kinetic profiles, "
                        "or analyse a fermentation run.")
        with st.container(horizontal=True, horizontal_alignment="right", width="content"):
            if st.button("Open Reaction Simulator", type="primary", key="spec_cta_sim"):
                state.go("simulate")
            if st.button("Build Enzyme", key="spec_cta_build"):
                state.go("build")
            if st.button("Bioreactor", key="spec_cta_bio"):
                state.go("bioreactor")
