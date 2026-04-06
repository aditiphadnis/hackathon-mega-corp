from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

WELCOME = (
    "Good morning, CEO. I have full access to Mega-Corp's order data and your calendar.\n\n"
    "Ask me to analyse sales, generate charts, schedule customer meetings, or look up "
    "meeting notes from Notion. What would you like to know first?"
)

# ── Small components ──────────────────────────────────────────────────────────

def stat_card(label: str, value: str, sub: str) -> html.Div:
    return html.Div(className="stat-card", children=[
        html.Div(label, className="sc-label"),
        html.Div(value, className="sc-value"),
        html.Div(sub,   className="sc-sub"),
    ])


def quick_btn(icon: str, label: str, index: int) -> html.Button:
    icon_el = (
        html.Span("X", className="warn-icon")
        if icon == "X"
        else html.Span(icon, style={"fontSize": "14px", "marginRight": "6px"})
    )
    return html.Button(
        [icon_el, label],
        className="quick-btn", n_clicks=0,
        id={"type": "quick-btn", "index": index},
    )


# Lookup table — index must match the order quick_btn() calls appear in _sidebar()
QUICK_QUERIES: dict[int, str] = {
    # Analytics
    0: "Show me a bar chart of top 10 customers by completed orders",
    1: "Give me a pie chart of payment methods used across all orders",
    2: "Show me a bar chart of number of sales by product",
    3: "What is our refund rate? Show me a bar chart of the top 10 products by number of refunds.",
    4: "Show me a bar chart of the top 10 customers by number of payment failures. Use the session_details table where `Interaction History` = 'Payment Failed'.",
    5: "Show me a bar chart of sales by region",
    # Meetings
    6: "Schedule a meeting with Lex Luthor tomorrow at 2pm",
    7: "Schedule a meeting with Aragorn next Monday at 10am",
    8: "List all my scheduled meetings",
    # Deep Dives
    9:  "Give me a full analysis of Ross Geller — orders, products, payment methods, and refunds.",
    10: "Who are my customers from the Krypton Core region and what have they been buying?",
    # Meeting Notes (Vector Search)
    11: "What was discussed about payment failures?",
    12: "Find notes related to Krypton Core",
    13: "What are the action items from the Ross Geller meeting?",
    14: "What decisions were made about refunds?",
}


def bubble(role: str, text: str) -> html.Div:
    if role == "user":
        return html.Div(className="msg msg-user", children=text)
    if role == "system":
        return html.Div(className="msg msg-system", children=text)
    return html.Div(className="msg msg-ai", children=[
        html.Div("MEGA-CORP AI · CHIEF OF STAFF", className="msg-sender"),
        html.Span(text, style={"whiteSpace": "pre-wrap"}),
    ])


# ── Sections ──────────────────────────────────────────────────────────────────

def _header() -> html.Header:
    return html.Header(
        style={"gridArea": "header", "display": "flex", "alignItems": "center",
               "gap": "16px", "padding": "0 24px",
               "background": "#111118", "borderBottom": "1px solid #2a2a3a"},
        children=[
            html.Div([
                html.Span("MEGA-CORP", style={"fontFamily": "Bebas Neue", "fontSize": "26px",
                                               "letterSpacing": "3px", "color": "#e8c468"}),
                html.Span("// CEO COMMAND CENTER", style={"fontFamily": "DM Mono", "fontSize": "13px",
                                                           "letterSpacing": "1px", "color": "#6b6b80",
                                                           "marginLeft": "8px"}),
            ]),
            html.Div(
                style={"marginLeft": "auto", "display": "flex", "alignItems": "center",
                       "gap": "6px", "color": "#4caf7d", "fontFamily": "DM Mono", "fontSize": "11px"},
                children=[
                    html.Div(style={"width": "6px", "height": "6px", "borderRadius": "50%",
                                    "background": "#4caf7d", "animation": "pulse 2s infinite"}),
                    "AI CHIEF OF STAFF · ONLINE",
                ],
            ),
        ],
    )


def _sidebar() -> html.Aside:
    return html.Aside(
        style={"gridArea": "sidebar", "background": "#111118",
               "borderRight": "1px solid #2a2a3a", "padding": "20px 16px", "overflowY": "auto"},
        children=[
            html.Div("Quick Stats", className="sidebar-label"),
            stat_card("Total Customers", "23",   "Across 6 universe regions"),
            stat_card("Data Range",      "13K+", "Sessions · Jan–Mar 2026"),

            html.Div(style={"marginTop": "16px"}),
            html.Div("Ask the AI", className="sidebar-label"),
            quick_btn("📊", "Top customers chart",       0),
            quick_btn("💳", "Payment methods breakdown", 1),
            quick_btn("📦", "Sales by product",          2),
            quick_btn("↩️", "Refund analysis",           3),
            quick_btn("X",  "Failed payments",           4),
            quick_btn("🌍", "Sales by region",           5),

            html.Div(style={"marginTop": "16px"}),
            html.Div("Meetings", className="sidebar-label"),
            quick_btn("📅", "Meet Lex Luthor",   6),
            quick_btn("📅", "Meet Aragorn",      7),
            quick_btn("🗓️", "View all meetings", 8),

            html.Div(style={"marginTop": "16px"}),
            html.Div("Deep Dives", className="sidebar-label"),
            quick_btn("🔍", "Ross Geller deep dive",   9),
            quick_btn("🚀", "Krypton Core customers", 10),

            # ── Meeting Notes (Vector Search) ─────────────────────────────
            html.Div(style={"marginTop": "16px"}),
            html.Div([
                html.Span("Meeting Notes", className="sidebar-label",
                          style={"display": "inline-block", "marginBottom": "0"}),
                html.Span(" · VECTOR SEARCH", style={
                    "fontFamily": "DM Mono", "fontSize": "8px", "color": "#7b5ea7",
                    "background": "#1e1428", "border": "1px solid #7b5ea7",
                    "borderRadius": "20px", "padding": "1px 6px", "marginLeft": "6px",
                    "verticalAlign": "middle",
                }),
            ], style={"marginBottom": "10px"}),
            quick_btn("🧠", "Payment failure discussions", 11),
            quick_btn("🌌", "Krypton Core notes",          12),
            quick_btn("👤", "Ross Geller action items",    13),
            quick_btn("↩️", "Refund decisions",            14),
        ],
    )


def _main_panel() -> html.Main:
    return html.Main(
        style={"gridArea": "main", "overflowY": "auto", "padding": "24px", "background": "#0a0a0f"},
        children=[
            html.Div([
                html.Span("LIVE CHART", id="tab-chart-btn", className="chart-tab active", n_clicks=0),
                html.Span("HOW TO USE",  id="tab-info-btn",  className="chart-tab",        n_clicks=0),
            ], style={"marginBottom": "16px"}),

            html.Div(id="chart-area", style={
                "background": "#111118", "border": "1px solid #2a2a3a",
                "borderRadius": "10px", "padding": "20px", "minHeight": "380px",
                "display": "flex", "flexDirection": "column",
                "alignItems": "center", "justifyContent": "center",
            }, children=[
                html.Div(id="chart-placeholder", children=[
                    html.Div("MC", style={"fontFamily": "Bebas Neue", "fontSize": "48px",
                                          "color": "#2a2a3a", "textAlign": "center"}),
                    html.P("Ask the AI to generate a chart and it will appear here.",
                           style={"textAlign": "center", "color": "#6b6b80"}),
                    html.P('Try: "Show me a bar chart of top customers"',
                           style={"textAlign": "center", "fontSize": "11px", "color": "#444"}),
                ]),
                dcc.Loading(
                    type="circle", color="#e8c468",
                    children=html.Div(id="chart-output"),
                ),
            ]),

            html.Div(id="info-panel", style={
                "display": "none", "background": "#111118",
                "border": "1px solid #2a2a3a", "borderRadius": "10px", "padding": "24px",
            }, children=[
                html.H2("MEGA-CORP CEO ASSISTANT",
                        style={"fontFamily": "Bebas Neue", "letterSpacing": "2px",
                               "color": "#e8c468", "marginBottom": "16px"}),
                html.P("Your AI Chief of Staff has access to 13,000+ order sessions from Jan–Mar 2026 "
                       "across 23 customers from Middle-earth, Krypton, Gotham, and the Friends universe.",
                       style={"color": "#6b6b80", "lineHeight": "1.7", "marginBottom": "12px"}),
                dbc.Row([
                    dbc.Col(_info_card("📊 ANALYTICS",  "Sales, top customers, refunds, payment methods, Plotly charts")),
                    dbc.Col(_info_card("📅 MEETINGS",   "Schedule meetings, manage Google Calendar via API")),
                    dbc.Col(_info_card("🧠 NOTES",      "Semantic search across meeting notes via Vertex AI Vector Search")),
                ]),
            ]),
        ],
    )


def _info_card(title: str, body: str) -> html.Div:
    return html.Div(
        style={"background": "#18181f", "border": "1px solid #2a2a3a",
               "borderRadius": "8px", "padding": "14px"},
        children=[
            html.Div(title, style={"fontFamily": "Bebas Neue", "letterSpacing": "1px",
                                    "color": "#e8c468", "marginBottom": "6px"}),
            html.Div(body,  style={"color": "#6b6b80", "fontSize": "12px", "lineHeight": "1.5"}),
        ],
    )


def _chat_panel() -> html.Div:
    return html.Div(
        id="chat-panel",
        style={
            "gridArea": "chat", "background": "#111118", "borderLeft": "1px solid #2a2a3a",
            "display": "flex", "flexDirection": "column",
            "minHeight": "0", "height": "100%",
        },
        children=[
            html.Div(
                style={"flexShrink": "0", "padding": "14px 18px",
                       "borderBottom": "1px solid #2a2a3a",
                       "display": "flex", "alignItems": "center", "gap": "10px"},
                children=[
                    html.Span("AI CHIEF OF STAFF",
                              style={"fontFamily": "Bebas Neue", "fontSize": "15px",
                                     "letterSpacing": "2px", "color": "#e8c468"}),
                    html.Span("GEMINI 2.5 FLASH · ADK",
                              style={"fontFamily": "DM Mono", "fontSize": "9px", "padding": "2px 8px",
                                     "borderRadius": "20px", "background": "#1e1428",
                                     "border": "1px solid #7b5ea7", "color": "#7b5ea7",
                                     "marginLeft": "auto"}),
                ],
            ),
            dcc.Loading(
                id="chat-loading",
                type="circle",
                color="#e8c468",
                overlay_style={"visibility": "visible", "filter": "blur(1px)"},
                parent_style={"flex": "1", "minHeight": "0", "overflow": "hidden",
                              "display": "flex", "flexDirection": "column"},
                children=html.Div(
                    id="message-list",
                    style={
                        "flex": "1", "minHeight": "0",
                        "overflowY": "auto",
                        "padding": "16px",
                        "display": "flex", "flexDirection": "column",
                    },
                    children=[bubble("ai", WELCOME)],
                ),
            ),
            html.Div(
                style={"flexShrink": "0", "padding": "14px",
                       "borderTop": "1px solid #2a2a3a",
                       "display": "flex", "flexDirection": "column", "gap": "8px"},
                children=[
                    dcc.Textarea(
                        id="chat-input",
                        placeholder="Ask your Chief of Staff anything...",
                        rows=2,
                        style={"width": "100%", "background": "#18181f",
                               "border": "1px solid #2a2a3a", "borderRadius": "8px",
                               "color": "#e8e8f0", "fontFamily": "DM Sans",
                               "fontSize": "13px", "padding": "10px 14px",
                               "resize": "none", "outline": "none"},
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px", "alignItems": "center"},
                        children=[
                            html.Span(id="session-label",
                                      style={"fontFamily": "DM Mono", "fontSize": "9px",
                                             "color": "#6b6b80"}),
                            html.Button("SEND", id="send-btn", n_clicks=0, style={
                                "background": "#e8c468", "border": "none", "borderRadius": "6px",
                                "color": "#0a0a0f", "fontFamily": "Bebas Neue", "fontSize": "14px",
                                "letterSpacing": "1px", "padding": "8px 18px",
                                "cursor": "pointer", "marginLeft": "auto",
                            }),
                        ],
                    ),
                ],
            ),
        ],
    )


# ── Root layout ───────────────────────────────────────────────────────────────

def build_layout() -> html.Div:
    return html.Div(
        style={
            "height": "100vh", "display": "grid",
            "gridTemplateRows": "56px 1fr",
            "gridTemplateColumns": "280px 1fr 380px",
            "gridTemplateAreas": '"header header header" "sidebar main chat"',
            "overflow": "hidden", "background": "#0a0a0f",
        },
        children=[
            _header(),
            _sidebar(),
            _main_panel(),
            _chat_panel(),
            dcc.Store(id="session-store"),
        ],
    )