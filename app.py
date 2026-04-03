# app.py
from dash import Dash, html, dcc, Input, Output, State
from orchestrator import orchestrator

app = Dash(__name__)

app.layout = html.Div([
    dcc.Markdown("# Personal Assistant Assistant"),
    dcc.Input(id='user-input', type='text', placeholder='Ask me anything...'),
    html.Button('Submit', id='submit-val'),
    html.Div(id='chat-output'),
    dcc.Graph(id='analytics-chart') # Plotly chart for the Analytics Agent
])

@app.callback(
    Output('chat-output', 'children'),
    Input('submit-val', 'n_clicks'),
    State('user-input', 'value')
)
def update_output(n_clicks, value):
    if n_clicks:
        # The ADK call
        response = orchestrator.run(value)
        return response.text

if __name__ == '__main__':
    app.run_server(debug=True)