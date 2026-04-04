from __future__ import annotations

import dash
import dash_bootstrap_components as dbc

from .callbacks import register
from .layout import build_layout

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Mega-Corp · CEO Command Center",
    # Dash auto-serves every file in assets/ — style.css is picked up here.
    assets_folder="assets",
)

app.layout = build_layout

register(app)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)