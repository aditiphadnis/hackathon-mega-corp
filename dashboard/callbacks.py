from __future__ import annotations

import json
import uuid

import dash
from dash import Input, Output, State, callback_context, clientside_callback, dcc, no_update

from .adk_client import create_session, run_agent
from .charts import build_figure, extract_plotly
from .layout import QUICK_QUERIES, bubble


# ── Internal helpers ──────────────────────────────────────────────────────────

def _call_agent(query: str, session: dict, current_bubbles: list) -> tuple[list, dict | None]:
    history = _bubbles_to_history(current_bubbles)
    history.append({"role": "user", "text": query})
    try:
        raw = run_agent(session["user_id"], session["session_id"], query)
        chart_data, display_text = extract_plotly(raw)
        history.append({"role": "ai", "text": display_text})
    except Exception as exc:
        chart_data = None
        history.append({"role": "system", "text": f"⚠ Agent error: {exc}"})
    return [bubble(m["role"], m["text"]) for m in history], chart_data


def _make_chart(chart_data: dict | None) -> tuple:
    if not chart_data:
        return None, {"textAlign": "center", "color": "#6b6b80"}
    fig = build_figure(chart_data)
    return (
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"width": "100%"}),
        {"display": "none"},
    )


def _bubbles_to_history(children: list | None) -> list[dict]:
    history: list[dict] = []
    for item in children or []:
        props = item.get("props", {}) if isinstance(item, dict) else {}
        cls   = props.get("className", "")
        inner = props.get("children", "")

        if "msg-user" in cls:
            history.append({"role": "user", "text": inner if isinstance(inner, str) else ""})
        elif "msg-system" in cls:
            history.append({"role": "system", "text": inner if isinstance(inner, str) else ""})
        elif "msg-ai" in cls:
            parts = inner if isinstance(inner, list) else []
            text  = ""
            if len(parts) >= 2:
                span  = parts[1]
                text  = (span.get("props", {}).get("children", "")
                         if isinstance(span, dict) else "")
            history.append({"role": "ai", "text": text})

    return history


# ── Callback registration ─────────────────────────────────────────────────────

def register(app: dash.Dash) -> None:

    # ── Auto-scroll — runs in the browser whenever message-list changes ───────
    clientside_callback(
        """
        function(children) {
            setTimeout(function() {
                var el = document.getElementById('message-list');
                if (el) { el.scrollTop = el.scrollHeight; }
            }, 50);
            return window.dash_clientside.no_update;
        }
        """,
        Output("message-list", "data-scrolled"),   # dummy attribute, never used
        Input("message-list",  "children"),
    )

    # ── Session init ──────────────────────────────────────────────────────────
    @app.callback(
        Output("session-store", "data"),
        Output("session-label", "children"),
        Input("session-store",  "data"),
        prevent_initial_call=False,
    )
    def init_session(existing: dict | None):
        if existing:
            return no_update, f"SESSION · {existing['user_id'][:8]}…"
        user_id    = str(uuid.uuid4())
        session_id = create_session(user_id)
        return (
            {"user_id": user_id, "session_id": session_id},
            f"SESSION · {user_id[:8]}…",
        )

    # ── Send button ───────────────────────────────────────────────────────────
    @app.callback(
        Output("message-list",      "children",  allow_duplicate=True),
        Output("chart-output",      "children",  allow_duplicate=True),
        Output("chart-placeholder", "style",     allow_duplicate=True),
        Output("chat-input",        "value"),
        Input("send-btn",           "n_clicks"),
        State("chat-input",         "value"),
        State("session-store",      "data"),
        State("message-list",       "children"),
        prevent_initial_call=True,
    )
    def on_send(_, text: str, session: dict, current_bubbles: list):
        if not text or not text.strip() or not session:
            return no_update, no_update, no_update, no_update
        bubbles, chart_data = _call_agent(text.strip(), session, current_bubbles)
        chart_el, placeholder_style = _make_chart(chart_data)
        return bubbles, chart_el, placeholder_style, ""

    # ── Quick buttons ─────────────────────────────────────────────────────────
    @app.callback(
        Output("message-list",      "children", allow_duplicate=True),
        Output("chart-output",      "children", allow_duplicate=True),
        Output("chart-placeholder", "style",    allow_duplicate=True),
        Input({"type": "quick-btn", "index": dash.ALL}, "n_clicks"),
        State("session-store", "data"),
        State("message-list",  "children"),
        prevent_initial_call=True,
    )
    def on_quick_btn(n_clicks_list: list, session: dict, current_bubbles: list):
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list):
            return no_update, no_update, no_update
        try:
            index = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["index"]
            query = QUICK_QUERIES[index]
        except Exception:
            return no_update, no_update, no_update
        bubbles, chart_data = _call_agent(query, session, current_bubbles)
        chart_el, placeholder_style = _make_chart(chart_data)
        return bubbles, chart_el, placeholder_style

    # ── Tab switcher ──────────────────────────────────────────────────────────
    @app.callback(
        Output("chart-area",    "style"),
        Output("info-panel",    "style"),
        Output("tab-chart-btn", "className"),
        Output("tab-info-btn",  "className"),
        Input("tab-chart-btn",  "n_clicks"),
        Input("tab-info-btn",   "n_clicks"),
        prevent_initial_call=False,
    )
    def switch_tab(_, __):
        show_info = (
            callback_context.triggered
            and "tab-info" in callback_context.triggered[0]["prop_id"]
        )
        chart_style = {
            "background": "#111118", "border": "1px solid #2a2a3a",
            "borderRadius": "10px", "padding": "20px", "minHeight": "380px",
            "display": "none" if show_info else "flex",
            "flexDirection": "column", "alignItems": "center", "justifyContent": "center",
        }
        info_style = {
            "display": "block" if show_info else "none",
            "background": "#111118", "border": "1px solid #2a2a3a",
            "borderRadius": "10px", "padding": "24px",
        }
        return (
            chart_style,
            info_style,
            "chart-tab" + ("" if show_info else " active"),
            "chart-tab" + (" active" if show_info else ""),
        )