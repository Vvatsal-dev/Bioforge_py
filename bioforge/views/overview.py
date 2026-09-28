"""Overview page - hero, 3-step interactive demo, features and call to action."""

import pandas as pd
import streamlit as st

from bioforge import bioreactor, catalog, charts, kinetics, state, theme
from bioforge.plot_style import STATIC_CONFIG
from bioforge.specs import EQUATIONS
from bioforge.ui import ASSETS


@st.cache_data
def _dataset():
    return bioreactor.load_builtin_dataset()


def _reset_teaser():
    """When a new catalyst is chosen, move the demo sliders to its optimum."""
    enzyme = st.session_state.enzymes[st.session_state.ov_enzyme]
    st.session_state.ov_temp = int(enzyme["optimal_temp"])
    st.session_state.ov_ph = float(enzyme["optimal_ph"])


def render():
    ss = st.session_state
    pal = theme.palette()
    enzymes = ss.enzymes

    # ------------------------------------------------------------------ hero
    left, right = st.columns([1.15, 1], gap="large", vertical_alignment="center")
    with left:
        st.badge("BioForge Molecular Engine", icon=":material/biotech:", color="green")
        st.title("Design, Simulate, and Optimize :green[Enzyme Reactions.]")
        st.markdown(
            "Explore biological reactions in seconds. No lab coat required. Intuitive visual "
            "modeling built especially for budding biochemists and curious students, now "
            "with a full **bioreactor fermentation** lab."
        )
        with st.container(horizontal=True):
            if st.button("Start Simulation", type="primary", icon=":material/arrow_forward:",
                         icon_position="right", key="ov_hero_sim"):
                state.go("simulate", ss.ov_enzyme)
            if st.button("Build Custom Enzyme", icon=":material/biotech:", key="ov_hero_build"):
                state.go("build")
            if st.button("Open Bioreactor", icon=":material/microbiology:", key="ov_hero_bio"):
                state.go("bioreactor")

        st.space("small")
        m1, m2, m3 = st.columns(3)
        m1.metric("Benchmark enzymes", len(catalog.BUILT_IN_IDS), border=True)
        m2.metric("Kinetic equations", len(EQUATIONS), border=True)
        m3.metric("Fermentation readings", len(_dataset()), border=True)

    with right:
        st.image(str(ASSETS / "hero-beaker.svg"), width="stretch")
        with st.container(horizontal=True, horizontal_alignment="center"):
            st.badge("Active Site: Open", icon=":material/radio_button_checked:", color="green")
            st.badge("Efficiency 98.4% Peak", icon=":material/bolt:", color="primary")
            st.badge("pH 7.0 Optimal", icon=":material/water_drop:", color="blue")
            st.badge("Substrate [Glc-6P] Ready", color="gray")

    st.space("large")

    # --------------------------------------------------- 3-step interactive demo
    with st.container(border=True):
        st.caption("HANDS-ON BIOCHEMISTRY", text_alignment="center")
        st.header("How BioForge Works in 3 Simple Steps", text_alignment="center")
        st.markdown("Try selecting an enzyme and tweaking conditions below to preview real-time kinetic calculations.",
                    text_alignment="center")

        step1, step2, step3 = st.columns(3, border=True, gap="medium")
        with step1:
            st.badge("Step 1", color="green")
            st.subheader("Choose Catalyst")
            st.caption("Select a foundational enzyme to load baseline kinetic parameters.")
            ids = catalog.BUILT_IN_IDS
            st.radio(
                "Catalyst", ids, key="ov_enzyme", on_change=_reset_teaser,
                format_func=lambda i: enzymes[i]["name"],
                captions=[enzymes[i]["equation"] for i in ids],
                label_visibility="collapsed",
            )

        profile = enzymes[ss.ov_enzyme]
        with step2:
            st.badge("Step 2", color="blue")
            st.subheader("Adjust Conditions")
            st.caption("Observe how thermal energy and ionization change conformation.")
            st.slider("Temperature", 10, 75, key="ov_temp", format="%d°C")
            st.caption(f"10°C (Cold) · **{profile['optimal_temp']}°C (Opt)** · 75°C (Denature)")
            st.slider("Acidity (pH)", 2.0, 12.0, step=0.1, key="ov_ph", format="pH %.1f")
            st.caption(f"pH 2.0 (Acidic) · **pH {profile['optimal_ph']:.1f}** · pH 12.0 (Basic)")

        score, velocity = kinetics.teaser_activity(
            ss.ov_temp, ss.ov_ph, profile["optimal_temp"], profile["optimal_ph"], profile["vmax"]
        )
        with step3:
            st.badge("Step 3", color="green")
            st.subheader("Live Velocity (Vmax)")
            st.caption("Instant kinetic output calculated through Michaelis-Menten curve.")
            if score > 75:
                st.badge("Optimal Activity", icon=":material/check_circle:", color="green")
            elif score > 35:
                st.badge("Moderate Velocity", icon=":material/speed:", color="blue")
            elif ss.ov_temp > kinetics.DENATURATION_TEMP_C:
                st.badge("Denatured Heat", icon=":material/local_fire_department:", color="red")
            else:
                st.badge("Low Catalytic Rate", icon=":material/trending_down:", color="gray")
            st.metric("Reaction Rate", f"{score}%")
            st.progress(score / 100)
            st.plotly_chart(charts.sparkline(score, pal), config=STATIC_CONFIG, key="ov_spark")
            st.caption(f"Velocity product curve: **{velocity:.2f} mmol / min**")
            if st.button("Open Full Workbench", type="primary", width="stretch", key="ov_open_bench"):
                state.go("simulate", ss.ov_enzyme)

    st.space("large")

    # ------------------------------------------------------------- features
    st.caption("ENGINEERED FOR CLARITY")
    st.header("Designed to build confidence, not confusion.")
    features = [
        (":material/visibility:", "Zero Clutter",
         "Learn kinetics and enzyme mechanics visually. Plain-language summaries explain active "
         "sites, inhibitors, and cofactors without dense algebraic jargon.",
         "Read plain glossary", "specifications"),
        (":material/cyclone:", "Instant Results",
         "Run continuous virtual assays in real time. Watch conformational shifts and molecular "
         "turnover without waiting 45 minutes for a centrifuge spin.",
         "Explore live bindings", "simulate"),
        (":material/school:", "Classroom & Lab Ready",
         "Export clean reports, high-res reaction graphs, and presentation-ready parameter cards "
         "with one simple click for your lab notebook or team project.",
         "View sample lab specs", "specifications"),
        (":material/microbiology:", "Bioreactor Analytics",
         "Analyse a real-style 24 h E. coli fermentation: filter readings by time, average dissolved "
         "oxygen or glucose, and pinpoint the moment of fastest growth.",
         "Open the bioreactor", "bioreactor"),
    ]
    cols = st.columns(4, border=True, gap="medium")
    for col, (icon, title, text, link, target) in zip(cols, features):
        with col:
            st.markdown(f"## {icon}")
            st.subheader(title)
            st.markdown(text)
            if st.button(link, type="tertiary", icon=":material/arrow_forward:",
                         icon_position="right", key=f"ov_feat_{title}"):
                state.go(target)

    st.space("large")

    # ---------------------------------------------------- the Python edition
    with st.container(border=True):
        left, right = st.columns([1, 1.3], gap="large")
        with left:
            st.badge("Python Edition", icon=":material/code:", color="blue")
            st.header("Built 100% in Python")
            st.markdown(
                "Every screen, slider, chart and calculation in this app is written in Python. "
                "No HTML, CSS or JavaScript files: the biology stays the same, the code is now "
                "pure computational thinking."
            )
        with right:
            libraries = pd.DataFrame(
                [
                    ("streamlit", "Pages, navigation, sliders, buttons, metric cards"),
                    ("numpy", "Michaelis-Menten curves, growth-rate derivatives (np.gradient)"),
                    ("pandas", "Fermentation dataset, filtering t ≥ t_cutoff, averages, CSV export"),
                    ("scipy", "solve_ivp integrates the Monod growth equations for the bioreactor data"),
                    ("plotly", "Interactive charts and the animated reaction flask"),
                ],
                columns=["Library", "What it does in BioForge"],
            )
            st.dataframe(libraries, hide_index=True, width="stretch")

    st.space("large")

    # ------------------------------------------------------ call to action
    with st.container(border=True, horizontal_alignment="center"):
        st.badge("Free for Students & Classrooms", color="green")
        st.header("Ready to see enzymes in action?", text_alignment="center")
        st.markdown(
            "Jump right into interactive experiments. Choose an enzyme, slide temperature and pH "
            "controls, and watch how living chemistry works in real time.",
            text_alignment="center",
        )
        with st.container(horizontal=True, horizontal_alignment="center"):
            if st.button("Launch BioForge Lab", type="primary", key="ov_cta_lab"):
                state.go("simulate")
            if st.button("Read Specifications", key="ov_cta_specs"):
                state.go("specifications")
