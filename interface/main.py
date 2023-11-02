import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import io
import sys

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://fonts.googleapis.com/css2?family=Roboto:wght@900&display=swap']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = dbc.Container(
    [
        html.H1("TEXT2STRUC", className="text-center mt-4", style={'font-family': 'Roboto', 'color': 'red', 'font-size': '48px'}),
        html.H2("Viktoriia Baibakova, Weike Ye, Steven Torrisi", className="text-center", style={'font-family': 'Roboto', 'color': 'black', 'font-size': '24px'}),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Textarea(id='my-input', value='initial value', style={'width': '100%', 'height': '150px'}),
                        html.Button('Submit', id='my-button', className="mt-2"),
                        html.Button('For BB', id='bb-button', className="mt-2"),
                    ], 
                    width=4,
                ),
                dbc.Col(
                    [
                        html.Div(id='my-output', style={'width': '100%', 'height': '150px', 'border': '1px solid', 'padding': '10px'}),
                        html.Div(id='bb-output', style={'width': '100%', 'height': '150px', 'border': '1px solid', 'padding': '10px'}),
                    ], 
                    width=4,
                ),
                dbc.Col(
                    [
                        html.Div(id='eval-output', style={'width': '100%', 'height': '150px', 'border': '1px solid', 'padding': '10px'}),
                        html.Div(id='bb_eval-output', style={'width': '100%', 'height': '150px', 'border': '1px solid', 'padding': '10px'}),
                        
                    ],
                    width=4,
                )
            ],
            className="align-items-center mt-4"
        )
    ], 
    fluid=True,
)

@app.callback(
    [Output('my-output', 'children'), Output('eval-output', 'children')],
    [Input('my-button', 'n_clicks')],
    [State('my-input', 'value')]
)
def update_output(n_clicks, value):
    if n_clicks is None:
        # button has not been clicked yet
        return '', ''
    else:
        # Return a python script that prints the input string
        script = "print('{}')".format(value)
        code_out = io.StringIO()
        sys.stdout = code_out
        exec(script)
        sys.stdout = sys.__stdout__
        return script, code_out.getvalue()
        return "Lol", "Three"
    
@app.callback(
    [Output('bb-output', 'children'), Output('bb_eval-output', 'children')],
    [Input('bb-button', 'n_clicks')],
    [State('my-input', 'value')]
)
def update_b(n_clicks, value):
    if n_clicks is None:
        # button has not been clicked yet
        return '', ''
    else:
        # Return a python script that prints the input string
        return 'a', 'b'

if __name__ == '__main__':
    app.run_server(debug=True)