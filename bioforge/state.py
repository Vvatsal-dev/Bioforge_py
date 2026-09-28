"""
state.py - everything the app remembers between clicks (st.session_state).

Streamlit re-runs the whole script after every click, so any value that must
survive (the enzyme library, the selected enzyme, slider positions, previous
simulation runs ...) is stored in st.session_state.
"""

import copy

import streamlit as st

from bioforge import catalog

# Filled in by app.py: {"overview": st.Page(...), "simulate": st.Page(...), ...}
PAGES = {}

DEFAULTS = {
    # shared enzyme selection
    "active_enzyme_id": "lactase",
    # Simulate page controls
    "sim_temp": 37,
    "sim_ph": 6.5,
    "sim_stir": 2,
    "sim_conc": 25,
    "sim_runs": [],          # earlier runs kept for comparison (max 6)
    "sim_current": None,     # the most recent finished run
    "sim_run_counter": 0,
    # Overview page teaser
    "ov_enzyme": "catalase",
    "ov_temp": 37,
    "ov_ph": 7.0,
    # Build Enzyme page form
    "b_name": "Syn-Dehydrogenase Alpha",
    "b_substrate": "Ethanol",
    "b_product": "Acetaldehyde + NADH",
    "b_km": 4.2,
    "b_vmax": 14.5,
    "b_temp": 37,
    "b_ph": 7.2,
    "b_preset": None,
    "b_saved_id": None,
    # Specifications page
    "spec_category": "all",
    # Bioreactor page
    "br_source": "Built-in dataset",
    "br_cutoff": 0.0,
    "br_param": "Dissolved Oxygen (%)",
    "br_layout": "Overlay",
}

# Widget keys whose values should be kept when the user switches pages
WIDGET_KEYS = [
    "active_enzyme_id", "sim_temp", "sim_ph", "sim_stir", "sim_conc",
    "ov_enzyme", "ov_temp", "ov_ph",
    "b_name", "b_substrate", "b_product", "b_km", "b_vmax", "b_temp", "b_ph", "b_preset",
    "spec_category", "br_source", "br_cutoff", "br_param", "br_layout",
]

MAX_SAVED_RUNS = 6


def init_state():
    """Create default values once, and keep widget values alive across pages."""
    ss = st.session_state
    if "enzymes" not in ss:
        ss.enzymes = catalog.get_default_catalog()
    for key, value in DEFAULTS.items():
        if key not in ss:
            ss[key] = copy.deepcopy(value)
    # Streamlit forgets the value of a widget that is not on screen.
    # Re-assigning it here keeps it (documented Streamlit pattern).
    for key in WIDGET_KEYS:
        ss[key] = ss[key]


def active_enzyme():
    enzymes = st.session_state.enzymes
    return enzymes.get(st.session_state.active_enzyme_id, enzymes["lactase"])


def select_enzyme(enzyme_id):
    """Make an enzyme active and move the sliders to its optimum (like the website)."""
    ss = st.session_state
    if enzyme_id not in ss.enzymes:
        return
    enzyme = ss.enzymes[enzyme_id]
    ss.active_enzyme_id = enzyme_id
    ss.sim_temp = int(enzyme["optimal_temp"])
    ss.sim_ph = float(enzyme["optimal_ph"])
    ss.sim_current = None


def on_enzyme_changed():
    """Callback for the enzyme drop-down on the Simulate page."""
    select_enzyme(st.session_state.active_enzyme_id)


def add_enzyme(enzyme):
    st.session_state.enzymes[enzyme["id"]] = enzyme


def go(page_id, enzyme_id=None):
    """Jump to another page (optionally selecting an enzyme first)."""
    if enzyme_id is not None:
        select_enzyme(enzyme_id)
    st.switch_page(PAGES[page_id])
