"""
plot_style.py - one shared look for every Plotly chart in BioForge.

Transparent backgrounds (so charts sit nicely on light AND dark pages),
thin solid gridlines, readable axis text and a hover tooltip.
"""

# Plotly toolbar settings: no logo, and "download as PNG" saves a sharp image
CHART_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "scale": 3, "filename": "bioforge_chart"},
}
STATIC_CONFIG = {"staticPlot": True, "displayModeBar": False}


def base_layout(fig, pal, height=380, hovermode="x unified", top_margin=60):
    fig.update_layout(
        template="none",
        height=height,
        margin=dict(l=10, r=10, t=top_margin, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13, color=pal["text"]),
        hovermode=hovermode,
        hoverlabel=dict(bgcolor=pal["surface"], font_color=pal["text"], bordercolor=pal["axis"]),
        legend=dict(
            orientation="h", yanchor="top", y=-0.26, xanchor="left", x=0,
            font=dict(color=pal["text2"]),
        ),
    )
    return fig


def style_axes(fig, pal):
    common = dict(
        showgrid=True, gridcolor=pal["grid"], gridwidth=1, zeroline=False,
        showline=True, linecolor=pal["axis"], ticks="outside", tickcolor=pal["axis"],
        title_font=dict(color=pal["text2"]), tickfont=dict(color=pal["text2"]),
        automargin=True,
    )
    fig.update_xaxes(**common)
    fig.update_yaxes(**common)
    return fig


def with_alpha(hex_color, alpha):
    """'#10B981', 0.1  ->  'rgba(16,185,129,0.1)'"""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def mix(hex_a, hex_b, amount):
    """Blend two hex colours. amount = 0 gives hex_a, 1 gives hex_b."""
    a = [int(hex_a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(hex_b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    amount = max(0.0, min(1.0, amount))
    blended = [round(x + (y - x) * amount) for x, y in zip(a, b)]
    return "#" + "".join(f"{v:02X}" for v in blended)
