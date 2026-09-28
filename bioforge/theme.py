"""
theme.py - BioForge colours for charts, in light and dark mode.

Streamlit's own colours (buttons, sliders, backgrounds, fonts) are set in
.streamlit/config.toml. This file only holds the colours we pass to Plotly,
chosen so every line stays readable (and colour-blind safe) in both modes.
"""

import streamlit as st

LIGHT = {
    "text": "#0B1C30",
    "text2": "#3D4947",
    "muted": "#6D7A77",
    "grid": "#E3E9EF",
    "axis": "#BCC9C6",
    "surface": "#FFFFFF",
    "primary": "#047857",   # emerald - main series (biomass, reaction progress)
    "blue": "#2A78D6",      # dissolved oxygen, 'current conditions' curves
    "orange": "#EB6834",    # glucose
    "red": "#E34948",       # denaturation zone
    "gray": "#9AA5A3",      # previous runs / reference lines
}

DARK = {
    "text": "#F1F5F9",
    "text2": "#AAB6C6",
    "muted": "#64748B",
    "grid": "#1F2B3E",
    "axis": "#334155",
    "surface": "#0B1220",
    "primary": "#10A377",
    "blue": "#3987E5",
    "orange": "#D95926",
    "red": "#E66767",
    "gray": "#5B6B80",
}

# Eight colour-blind-checked hues for comparing many enzymes on one chart
CATEGORICAL_LIGHT = ["#047857", "#2A78D6", "#EB6834", "#EDA100", "#E87BA4", "#4A3AA7", "#E34948", "#1BAF7A"]
CATEGORICAL_DARK = ["#10A377", "#3987E5", "#D95926", "#C98500", "#D55181", "#9085E9", "#E66767", "#199E70"]


def is_dark():
    """True when the viewer is using Streamlit's dark theme."""
    try:
        return st.context.theme.type == "dark"
    except Exception:  # noqa: BLE001 - older Streamlit or no browser context
        return False


def palette():
    return DARK if is_dark() else LIGHT


def categorical():
    return CATEGORICAL_DARK if is_dark() else CATEGORICAL_LIGHT
