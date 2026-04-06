from __future__ import annotations

import json
import os
import re
import uuid

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import requests
from dash import Input, Output, State, callback_context, dcc, html, no_update

# ── Config ────────────────────────────────────────────────────────────────────
ADK_API_URL = os.getenv("ADK_API_URL", "http://localhost:8000")
APP_NAME    = "megacorp_ceo"

# ── ADK session helpers ───────────────────────────────────────────────────────

def _create_session(user_id: str, session_id: str) -> None:
    """Create an ADK session (idempotent — 409 is fine)."""
    url = f"{ADK_API_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}"
    try:
        requests.post(url, timeout=10)
    except requests.RequestException:
        pass


def _run_agent(user_id: str, session_id: str, message: str) -> str:
    """Send a message to the ADK API and return the final text response."""
    url = f"{ADK_API_URL}/run"
    payload = {
        "app_name": APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": message}],
        },
        "streaming": False,
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    events = resp.json()

    # Walk events in reverse to find the last model text response
    for event in reversed(events):
        content = event.get("content", {})
        if content.get("role") == "model":
            for part in content.get("parts", []):
                if text := part.get("text", "").strip():
                    return text
    return "No response received from agent."


# ── Plotly data extraction ────────────────────────────────────────────────────

_PLOTLY_RE = re.compile(r"```plotly\s*(\{[\s\S]*?})\s*```", re.IGNORECASE)


def _extract_plotly(text: str) -> tuple[dict | None, str]:
    """Pull the first ```plotly JSON block out of the response text."""
    m = _PLOTLY_RE.search(text)
    if not m:
        return None, text
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None, text
    clean = _PLOTLY_RE.sub("[Chart generated ↑]", text).strip()
    return data, clean


def _build_figure(data: dict) -> go.Figure:
    """Convert the plotly JSON blob from the agent into a go.Figure."""
    chart_type = data.get("chart_type", "bar")
    title      = data.get("title", "")
    x          = data.get("x", data.get("labels", []))
    y          = data.get("y", data.get("values", []))

    COLORS = ["#7b5ea7", "#e8c468", "#4caf7d", "#e05555",
              "#5ea7b5", "#e07b5e", "#a7e07b", "#5e7be0"]

    if chart_type == "pie":
        trace = go.Pie(
            labels=x, values=y, hole=0.4,
            marker_colors=COLORS,
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
        paper_bgcolor="#111118",
        plot_bgcolor="#0a0a0f",
        font=dict(family="DM Sans", color="#e8e8f0", size=12),
        margin=dict(t=50, b=80, l=60, r=20),
        xaxis=dict(gridcolor="#2a2a3a", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#2a2a3a", tickfont=dict(size=11)),
        showlegend=(chart_type == "pie"),
        legend=dict(font=dict(size=11), bgcolor="#111118"),
    )
    return go.Figure(data=[trace], layout=layout)


# ── CSS injected into <head> ──────────────────────────────────────────────────
EXTERNAL_STYLESHEETS = [dbc.themes.BOOTSTRAP]

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
  --bg: #0a0a0f; --surface: #111118; --surface2: #18181f;
  --border: #2a2a3a; --accent: #e8c468; --accent2: #7b5ea7;
  --danger: #e05555; --success: #4caf7d;
  --text: #e8e8f0; --muted: #6b6b80;
}
* { box-sizing: border-box; }
body, html { background: var(--bg) !important; color: var(--text); font-family: 'DM Sans', sans-serif; height: 100vh; overflow: hidden; }
#_dash-app-content, .container-fluid { height: 100%; padding: 0 !important; }

/* scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* stat card */
.stat-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; }
.stat-card .sc-label { color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-family: 'DM Mono', monospace; }
.stat-card .sc-value { font-family: 'Bebas Neue', sans-serif; font-size: 28px; color: var(--accent); letter-spacing: 1px; line-height: 1.1; margin-top: 2px; }
.stat-card .sc-sub { color: var(--muted); font-size: 10px; margin-top: 2px; }

/* quick btns */
.quick-btn { display: block; width: 100%; background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 12px;
  padding: 9px 12px; text-align: left; cursor: pointer; margin-bottom: 6px; transition: all .15s; line-height: 1.4; }
.quick-btn:hover { border-color: var(--accent); color: var(--accent); background: #1a1a10; }

/* sidebar label */
.sidebar-label { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 2px;
  color: var(--muted); text-transform: uppercase; margin-bottom: 10px; }

/* chat messages */
.msg { max-width: 92%; padding: 10px 14px; border-radius: 10px; font-size: 13px; line-height: 1.55; margin-bottom: 10px; }
.msg-user { background: #1e1e2e; border: 1px solid var(--border); margin-left: auto; border-bottom-right-radius: 3px; }
.msg-ai { background: #141420; border: 1px solid #22223a; border-bottom-left-radius: 3px; }
.msg-system { background: #0f1a12; border: 1px solid #2a3a2a; color: var(--success);
  font-family: 'DM Mono', monospace; font-size: 11px; text-align: center;
  border-radius: 6px; padding: 6px 12px; margin: 0 auto; max-width: 80%; }
.msg-sender { font-family: 'DM Mono', monospace; font-size: 9px; color: var(--accent); letter-spacing: 1px; margin-bottom: 5px; }
.tool-step { background: #0e0e18; border-left: 2px solid var(--accent2); padding: 4px 8px;
  border-radius: 0 4px 4px 0; font-family: 'DM Mono', monospace; font-size: 10px;
  color: var(--accent2); margin: 2px 0; }

/* chart tab */
.chart-tab { background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
  color: var(--muted); font-family: 'DM Mono', monospace; font-size: 11px;
  padding: 6px 12px; cursor: pointer; transition: all .15s; display: inline-block; margin-right: 8px; }
.chart-tab.active, .chart-tab:hover { border-color: var(--accent); color: var(--accent); }
"""

# ── Reusable small components ─────────────────────────────────────────────────

def stat_card(label: str, value: str, sub: str) -> html.Div:
    return html.Div(className="stat-card", children=[
        html.Div(label, className="sc-label"),
        html.Div(value, className="sc-value"),
        html.Div(sub,   className="sc-sub"),
    ])


def quick_btn(icon: str, label: str, query: str) -> html.Button:
    return html.Button(
        [html.Span(icon, style={"fontSize": "14px", "marginRight": "6px"}), label],
        className="quick-btn",
        n_clicks=0,
        id={"type": "quick-btn", "query": query},
    )


def chat_message(role: str, text: str) -> html.Div:
    if role == "user":
        return html.Div(className="msg msg-user", children=text)
    if role == "system":
        return html.Div(className="msg msg-system", children=text)
    return html.Div(className="msg msg-ai", children=[
        html.Div("MEGA-CORP AI · CHIEF OF STAFF", className="msg-sender"),
        html.Span(text, style={"whiteSpace": "pre-wrap"}),
    ])


# ── Layout ────────────────────────────────────────────────────────────────────

def layout() -> html.Div:
    return html.Div(style={"height": "100vh", "display": "grid",
                            "gridTemplateRows": "56px 1fr",
                            "gridTemplateColumns": "280px 1fr 380px",
                            "gridTemplateAreas": '"header header header" "sidebar main chat"',
                            "overflow": "hidden",
                            "background": "#0a0a0f"}, children=[

        # ── header ────────────────────────────────────────────────────────────
        html.Header(style={"gridArea": "header", "display": "flex", "alignItems": "center",
                            "gap": "16px", "padding": "0 24px",
                            "background": "#111118", "borderBottom": "1px solid #2a2a3a"}, children=[
            html.Div([
                html.Span("MEGA-CORP", style={"fontFamily": "Bebas Neue", "fontSize": "26px",
                                               "letterSpacing": "3px", "color": "#e8c468"}),
                html.Span("// CEO COMMAND CENTER", style={"fontFamily": "DM Mono", "fontSize": "13px",
                                                           "letterSpacing": "1px", "color": "#6b6b80",
                                                           "marginLeft": "8px"}),
            ]),
            html.Div(style={"marginLeft": "auto", "display": "flex", "alignItems": "center",
                             "gap": "6px", "color": "#4caf7d",
                             "fontFamily": "DM Mono", "fontSize": "11px"}, children=[
                html.Div(style={"width": "6px", "height": "6px", "borderRadius": "50%",
                                "background": "#4caf7d", "animation": "pulse 2s infinite"}),
                "AI CHIEF OF STAFF · ONLINE",
            ]),
        ]),

        # ── sidebar ───────────────────────────────────────────────────────────
        html.Aside(style={"gridArea": "sidebar", "background": "#111118",
                           "borderRight": "1px solid #2a2a3a",
                           "padding": "20px 16px", "overflowY": "auto"}, children=[
            html.Div("Quick Stats", className="sidebar-label"),
            stat_card("Total Customers", "23",   "Across 6 universe regions"),
            stat_card("Data Range",      "13K+", "Sessions · Jan–Mar 2026"),

            html.Div(style={"marginTop": "16px"}),
            html.Div("Ask the AI", className="sidebar-label"),
            quick_btn("📊", "Top customers chart",
                      "Show me a bar chart of top 10 customers by completed orders"),
            quick_btn("💳", "Payment methods breakdown",
                      "Give me a pie chart of payment methods used across all orders"),
            quick_btn("📦", "Sales by product",
                      "Show me a bar chart of number sales by product"),
            quick_btn("↩️", "Refund analysis",
                      "What is our refund rate and which products have the most refunds?"),
            quick_btn("⚠️", "Failed payments",
                      "Which customers had payment failures? Show me a bar chart."),
            quick_btn("🌍", "Sales by region",
                      "Show me sales breakdown by universe region as a bar chart"),

            html.Div(style={"marginTop": "16px"}),
            html.Div("Meetings", className="sidebar-label"),
            quick_btn("📅", "Meet Lex Luthor",
                      "Schedule a meeting with Lex Luthor tomorrow at 2pm to discuss his abandoned cart items"),
            quick_btn("📅", "Meet Aragorn",
                      "Schedule a meeting with Aragorn next Monday at 10am to review his order history"),
            quick_btn("🗓️", "View all meetings",
                      "List all my scheduled meetings"),

            html.Div(style={"marginTop": "16px"}),
            html.Div("Deep Dives", className="sidebar-label"),
            quick_btn("🔍", "Ross Geller deep dive + meeting",
                      "Give me a full analysis of Ross Geller — his orders, products purchased, "
                      "payment methods, and any refunds. Then schedule a follow-up meeting with him "
                      "this Friday at 3pm."),
            quick_btn("🚀", "Krypton Core customers",
                      "Who are my customers from the Krypton Core region and what have they been buying?"),
        ]),

        # ── main ──────────────────────────────────────────────────────────────
        html.Main(style={"gridArea": "main", "overflowY": "auto",
                          "padding": "24px", "background": "#0a0a0f"}, children=[
            html.Div([
                html.Span("LIVE CHART", id="tab-chart-btn", className="chart-tab active",
                          n_clicks=0),
                html.Span("HOW TO USE", id="tab-info-btn", className="chart-tab",
                          n_clicks=0),
            ], style={"marginBottom": "16px"}),

            html.Div(id="chart-area", style={
                "background": "#111118", "border": "1px solid #2a2a3a",
                "borderRadius": "10px", "padding": "20px",
                "minHeight": "380px", "display": "flex",
                "flexDirection": "column", "alignItems": "center", "justifyContent": "center",
            }, children=[
                html.Div(id="chart-placeholder", style={"textAlign": "center", "color": "#6b6b80"}, children=[
                    html.Div("MC", style={"fontFamily": "Bebas Neue", "fontSize": "48px", "color": "#2a2a3a"}),
                    html.P("Ask the AI to generate a chart and it will appear here."),
                    html.P('Try: "Show me a bar chart of top customers"',
                           style={"marginTop": "8px", "fontSize": "11px", "color": "#444"}),
                ]),
                dcc.Graph(id="plotly-chart", style={"display": "none", "width": "100%"},
                          config={"displayModeBar": False}),
            ]),

            html.Div(id="info-panel", style={"display": "none",
                "background": "#111118", "border": "1px solid #2a2a3a",
                "borderRadius": "10px", "padding": "24px"}, children=[
                html.H2("MEGA-CORP CEO ASSISTANT",
                        style={"fontFamily": "Bebas Neue", "letterSpacing": "2px",
                               "color": "#e8c468", "marginBottom": "16px"}),
                html.P("Your AI Chief of Staff has access to 13,000+ order sessions from Jan–Mar 2026 "
                       "across 23 customers from Middle-earth, Krypton, Gotham, and the Friends universe.",
                       style={"color": "#6b6b80", "lineHeight": "1.7", "marginBottom": "12px"}),
                dbc.Row([
                    dbc.Col(html.Div(style={"background": "#18181f", "border": "1px solid #2a2a3a",
                                            "borderRadius": "8px", "padding": "14px"}, children=[
                        html.Div("📊 ANALYTICS", style={"fontFamily": "Bebas Neue",
                                                         "letterSpacing": "1px", "color": "#e8c468",
                                                         "marginBottom": "6px"}),
                        html.Div("Sales analysis, top customers, refunds, payment methods, Plotly charts",
                                 style={"color": "#6b6b80", "fontSize": "12px", "lineHeight": "1.5"}),
                    ])),
                    dbc.Col(html.Div(style={"background": "#18181f", "border": "1px solid #2a2a3a",
                                            "borderRadius": "8px", "padding": "14px"}, children=[
                        html.Div("📅 MEETINGS", style={"fontFamily": "Bebas Neue",
                                                        "letterSpacing": "1px", "color": "#e8c468",
                                                        "marginBottom": "6px"}),
                        html.Div("Schedule meetings, manage Google Calendar via MCP",
                                 style={"color": "#6b6b80", "fontSize": "12px", "lineHeight": "1.5"}),
                    ])),
                    dbc.Col(html.Div(style={"background": "#18181f", "border": "1px solid #2a2a3a",
                                            "borderRadius": "8px", "padding": "14px"}, children=[
                        html.Div("📝 NOTES", style={"fontFamily": "Bebas Neue",
                                                     "letterSpacing": "1px", "color": "#e8c468",
                                                     "marginBottom": "6px"}),
                        html.Div("Retrieve and analyse meeting notes from Notion via MCP",
                                 style={"color": "#6b6b80", "fontSize": "12px", "lineHeight": "1.5"}),
                    ])),
                ]),
            ]),
        ]),

        # ── chat panel ────────────────────────────────────────────────────────
        html.Div(id="chat-panel", style={"gridArea": "chat", "background": "#111118",
                                          "borderLeft": "1px solid #2a2a3a",
                                          "display": "flex", "flexDirection": "column",
                                          "height": "100%"}, children=[
            html.Div(style={"padding": "14px 18px", "borderBottom": "1px solid #2a2a3a",
                             "display": "flex", "alignItems": "center", "gap": "10px"}, children=[
                html.Span("AI CHIEF OF STAFF",
                          style={"fontFamily": "Bebas Neue", "fontSize": "15px",
                                 "letterSpacing": "2px", "color": "#e8c468"}),
                html.Span("GEMINI 2.5 FLASH · ADK",
                          style={"fontFamily": "DM Mono", "fontSize": "9px",
                                 "padding": "2px 8px", "borderRadius": "20px",
                                 "background": "#1e1428", "border": "1px solid #7b5ea7",
                                 "color": "#7b5ea7", "marginLeft": "auto"}),
            ]),

            # message list
            html.Div(id="message-list", style={
                "flex": "1", "overflowY": "auto", "padding": "16px",
                "display": "flex", "flexDirection": "column",
            }, children=[
                chat_message("ai",
                    "Good morning, CEO. I have full access to Mega-Corp's order data and your calendar.\n\n"
                    "Ask me to analyse sales, generate charts, schedule customer meetings, or look up "
                    "meeting notes from Notion. What would you like to know first?"),
            ]),

            # input area
            html.Div(style={"padding": "14px", "borderTop": "1px solid #2a2a3a",
                             "display": "flex", "flexDirection": "column", "gap": "8px"}, children=[
                dcc.Textarea(
                    id="chat-input",
                    placeholder="Ask your Chief of Staff anything...",
                    rows=2,
                    style={"width": "100%", "background": "#18181f", "border": "1px solid #2a2a3a",
                           "borderRadius": "8px", "color": "#e8e8f0",
                           "fontFamily": "DM Sans", "fontSize": "13px",
                           "padding": "10px 14px", "resize": "none", "outline": "none"},
                ),
                html.Div(style={"display": "flex", "gap": "8px", "alignItems": "center"}, children=[
                    html.Span(id="session-label", style={"fontFamily": "DM Mono",
                                                          "fontSize": "9px", "color": "#6b6b80"}),
                    html.Button("SEND", id="send-btn", n_clicks=0,
                                style={"background": "#e8c468", "border": "none",
                                       "borderRadius": "6px", "color": "#0a0a0f",
                                       "fontFamily": "Bebas Neue", "fontSize": "14px",
                                       "letterSpacing": "1px", "padding": "8px 18px",
                                       "cursor": "pointer", "marginLeft": "auto"}),
                ]),
            ]),
        ]),

        # ── hidden stores ─────────────────────────────────────────────────────
        dcc.Store(id="session-store"),   # {"user_id": ..., "session_id": ...}
        dcc.Store(id="messages-store",  # list of {"role": ..., "text": ...}
                  data=[{"role": "ai",
                         "text": "Good morning, CEO. I have full access to Mega-Corp's order data "
                                 "and your calendar.\n\nAsk me to analyse sales, generate charts, "
                                 "schedule customer meetings, or look up meeting notes from Notion. "
                                 "What would you like to know first?"}]),
        dcc.Store(id="chart-store"),     # plotly data dict from last AI response
        dcc.Store(id="pending-query"),   # query injected by quick-btn or keyboard
        dcc.Interval(id="send-trigger", interval=100, n_intervals=0, disabled=True),
    ])


# ── App init ──────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    suppress_callback_exceptions=True,
    title="Mega-Corp · CEO Command Center",
)
app.index_string = app.index_string.replace(
    "</head>",
    f"<style>{CUSTOM_CSS}</style>\n<style>@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}</style>\n</head>",
)
app.layout = layout


# ── Callbacks ─────────────────────────────────────────────────────────────────

# 1. Initialise session on first load
@app.callback(
    Output("session-store", "data"),
    Output("session-label", "children"),
    Input("session-store", "data"),
    prevent_initial_call=False,
)
def init_session(existing):
    if existing:
        sid = existing["session_id"]
        return existing, f"SESSION: {sid[:8]}…"
    user_id    = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    _create_session(user_id, session_id)
    return {"user_id": user_id, "session_id": session_id}, f"SESSION: {session_id[:8]}…"


# 2. Quick-btn click → fill pending-query store + enable send-trigger
@app.callback(
    Output("pending-query", "data"),
    Output("send-trigger", "disabled"),
    Input({"type": "quick-btn", "query": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def quick_btn_click(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, True
    prop_id = ctx.triggered[0]["prop_id"]
    query   = json.loads(prop_id.split(".")[0])["query"]
    return query, False


# 3. Keyboard Enter in textarea → set pending-query
@app.callback(
    Output("pending-query", "data", allow_duplicate=True),
    Output("send-trigger", "disabled", allow_duplicate=True),
    Input("chat-input", "n_submit"),
    State("chat-input", "value"),
    prevent_initial_call=True,
)
def enter_key(_, value):
    if not value or not value.strip():
        return no_update, True
    return value.strip(), False


# 4. SEND button click → set pending-query
@app.callback(
    Output("pending-query", "data", allow_duplicate=True),
    Output("send-trigger", "disabled", allow_duplicate=True),
    Input("send-btn", "n_clicks"),
    State("chat-input", "value"),
    prevent_initial_call=True,
)
def send_click(_, value):
    if not value or not value.strip():
        return no_update, True
    return value.strip(), False


# 5. send-trigger fires → call ADK, update messages + chart
@app.callback(
    Output("messages-store",  "data"),
    Output("chart-store",     "data"),
    Output("chat-input",      "value"),
    Output("send-trigger",    "disabled", allow_duplicate=True),
    Input("send-trigger",     "n_intervals"),
    State("pending-query",    "data"),
    State("session-store",    "data"),
    State("messages-store",   "data"),
    prevent_initial_call=True,
)
def call_agent(_, query, session, messages):
    if not query or not session:
        return no_update, no_update, no_update, True

    messages = list(messages or [])
    messages.append({"role": "user", "text": query})

    try:
        raw = _run_agent(session["user_id"], session["session_id"], query)
        plotly_data, display_text = _extract_plotly(raw)
        messages.append({"role": "ai", "text": display_text})
        return messages, plotly_data, "", True
    except Exception as exc:
        messages.append({"role": "system", "text": f"⚠ Agent error: {exc}"})
        return messages, no_update, "", True


# 6. Render message list from store
@app.callback(
    Output("message-list", "children"),
    Input("messages-store", "data"),
)
def render_messages(messages):
    return [chat_message(m["role"], m["text"]) for m in (messages or [])]


# 7. Render chart from store
@app.callback(
    Output("plotly-chart",    "figure"),
    Output("plotly-chart",    "style"),
    Output("chart-placeholder", "style"),
    Input("chart-store", "data"),
)
def render_chart(data):
    hidden   = {"display": "none"}
    visible  = {"display": "block", "width": "100%"}
    ph_shown = {"textAlign": "center", "color": "#6b6b80"}
    ph_hidden = {"display": "none"}

    if not data:
        return go.Figure(), hidden, ph_shown
    fig = _build_figure(data)
    return fig, visible, ph_hidden


# 8. Tab switching
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
    ctx = callback_context
    show_info = ctx.triggered and "tab-info" in ctx.triggered[0]["prop_id"]

    chart_style = {"background": "#111118", "border": "1px solid #2a2a3a",
                   "borderRadius": "10px", "padding": "20px", "minHeight": "380px",
                   "display": "none" if show_info else "flex",
                   "flexDirection": "column", "alignItems": "center", "justifyContent": "center"}
    info_style  = {"display": "block" if show_info else "none",
                   "background": "#111118", "border": "1px solid #2a2a3a",
                   "borderRadius": "10px", "padding": "24px"}

    return (chart_style, info_style,
            "chart-tab" + ("" if show_info else " active"),
            "chart-tab" + (" active" if show_info else ""))


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)