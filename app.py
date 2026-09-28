"""
BioForge - Enzyme Reaction Simulator & Bioreactor Lab (Python Edition)

Run it with:
    pip install -r requirements.txt
    streamlit run app.py

This file only sets up the page, the shared memory (session state) and the
top navigation bar. Each page lives in bioforge/views/.
"""

from pathlib import Path

import streamlit as st

from bioforge import state
from bioforge.ui import footer
from bioforge.views import bioreactor_lab, build_enzyme, overview, simulate, specifications

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="BioForge · Enzyme & Bioreactor Lab",
    page_icon="\U0001f9ea",
    layout="wide",
)

state.init_state()
st.logo(str(ASSETS / "logo.svg"), size="large")

# The five pages, in the same order as the original website's navbar (+ Bioreactor)
PAGES = {
    "overview": st.Page(overview.render, title="Overview", icon=":material/home:",
                        url_path="overview", default=True),
    "simulate": st.Page(simulate.render, title="Simulate", icon=":material/science:",
                        url_path="simulate"),
    "build": st.Page(build_enzyme.render, title="Build Enzyme", icon=":material/biotech:",
                     url_path="build-enzyme"),
    "specifications": st.Page(specifications.render, title="Specifications", icon=":material/functions:",
                              url_path="specifications"),
    "bioreactor": st.Page(bioreactor_lab.render, title="Bioreactor", icon=":material/microbiology:",
                          url_path="bioreactor"),
}
state.PAGES.update(PAGES)

current_page = st.navigation(list(PAGES.values()), position="top")
current_page.run()
footer()
