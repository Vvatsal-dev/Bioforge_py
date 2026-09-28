"""
ui.py - small reusable building blocks for the pages.
"""

import inspect
from pathlib import Path

import streamlit as st

from bioforge import state

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def page_header(title, badge=None, badge_icon=None, badge_color="green", subtitle=None):
    """Badge + big title + one line of description (top of every page)."""
    if badge:
        st.badge(badge, icon=badge_icon, color=badge_color)
    st.title(title)
    if subtitle:
        st.markdown(subtitle)


def labelled(label, value):
    """A small grey label with a bold value underneath (used in info cards)."""
    st.caption(label.upper())
    st.markdown(f"**{value}**")


def show_python(title, *functions):
    """An expander that prints the real source code of the given functions.

    Great for presentations: the maths on screen IS the code that runs.
    """
    with st.expander(title, icon=":material/code:"):
        st.caption("This is the actual Python code running behind this page.")
        for func in functions:
            st.code(inspect.getsource(func), language="python")


def footer():
    st.divider()
    left, right = st.columns([3, 2], vertical_alignment="center")
    with left:
        st.markdown(
            "**BioForge Platform** v3.0 · Educational Enzyme Reaction Simulator & "
            "Computational Kinetics · *Python Edition*"
        )
        st.caption("Built with Streamlit · pandas · NumPy · SciPy · Plotly")
    with right:
        with st.container(horizontal=True, horizontal_alignment="right"):
            if state.PAGES:
                st.page_link(state.PAGES["specifications"], label="Kinetic Specs")
                st.page_link(state.PAGES["simulate"], label="Virtual Lab")
                st.page_link(state.PAGES["build"], label="Custom Enzyme Studio")
                st.page_link(state.PAGES["bioreactor"], label="Bioreactor")
        st.caption("© 2026 BioForge Biosystems")
