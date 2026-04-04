from __future__ import annotations

import json
import re

import plotly.graph_objects as go

_PLOTLY_RE = re.compile(r"```(?:plotly|json)\s*(\{[\s\S]*?})\s*```", re.IGNORECASE)

_COLORS = ["#7b5ea7", "#e8c468", "#4caf7d", "#e05555",
           "#5ea7b5", "#e07b5e", "#a7e07b", "#5e7be0"]


def extract_plotly(text: str) -> tuple[dict | None, str]:
    """Pull the first ```plotly JSON block out of agent text.

    Returns (chart_dict, cleaned_text). If no block is found both the
    dict is None and the original text is returned unchanged.
    """
    m = _PLOTLY_RE.search(text)
    if not m:
        return None, text
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None, text
    clean = _PLOTLY_RE.sub("[Chart generated above ↑]", text).strip()
    return data, clean


def build_figure(data: dict) -> go.Figure:
    """Turn a chart spec dict into a styled Plotly Figure."""
    chart_type = data.get("chart_type", "bar")
    x = data.get("x", data.get("labels", []))
    y = data.get("y", data.get("values", []))
    title = data.get("title", "")

    if chart_type == "pie":
        trace = go.Pie(
            labels=x, values=y, hole=0.4,
            marker_colors=_COLORS,
            textfont=dict(family="DM Mono", size=11),
        )
    elif chart_type == "line":
        trace = go.Scatter(
            x=x, y=y, mode="lines+markers",
            line=dict(color="#e8c468", width=2),
            marker=dict(color="#e8c468", size=6),
        )
    else:
        trace = go.Bar(
            x=x, y=y,
            marker=dict(color="#7b5ea7", line=dict(color="#e8c468", width=0.5)),
            text=y, textposition="outside",
            textfont=dict(family="DM Mono", size=10, color="#e8c468"),
        )

    layout = go.Layout(
        title=dict(text=title, font=dict(family="Bebas Neue", size=18, color="#e8c468")),
        paper_bgcolor="#111118", plot_bgcolor="#0a0a0f",
        font=dict(family="DM Sans", color="#e8e8f0", size=12),
        margin=dict(t=50, b=80, l=60, r=20),
        xaxis=dict(gridcolor="#2a2a3a", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#2a2a3a", tickfont=dict(size=11)),
        showlegend=(chart_type == "pie"),
        legend=dict(font=dict(size=11), bgcolor="#111118"),
    )
    return go.Figure(data=[trace], layout=layout)