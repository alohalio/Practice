import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output

class TimeSeriesSplit:
    def __init__(self, data: pd.DataFrame, intervals: list):
        self.data = data
        self.intervals = intervals
        self.split_data = {}

    def split_by_intervals(self):
        for year in self.intervals:
            since, till = f'{year}-01-01', f'{year}-12-31'
            self.split_data[f'{year}_data'] = self.data.loc[since:till]
        return self.split_data

class TechnicalIndicator:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.intervals = [9, 12, 21, 30, 50, 80, 100, 200]
        for interval in self.intervals:
            col_ema = f'ema_{interval}'
            self.data[col_ema] = self.calc_ema(interval)
    
    def calc_ema(self, spans: int):
        return self.data['close'].ewm(span=spans).mean()

# Load and preprocess data
df = pd.read_csv('btc_hourly_data.csv')
df['date'] = pd.to_datetime(df['date'])  # Ensure date column is in datetime format
df = df.set_index('date')

# Initialize technical indicators
TechnicalIndicator(df)

years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
indicator_columns = [col for col in df.columns if 'ema_' in col or 'sma_' in col or 'macd_' in col]
color_palettes = ['orange', 'purple', 'brown', 'blue', 'olive']

# Split data by years
splitter = TimeSeriesSplit(df, years)
split_data = splitter.split_by_intervals()

# Initialize Dash app
app = Dash(__name__)

app.layout = html.Div(id='main-container', children=[
    html.H1('Dashboard', id='headers'),
    dcc.Checklist(
        id='dark-mode-toggle',
        options=[{'label': 'Dark Mode', 'value': 'dark'}],
        value=[],
        style={'float': 'right', 'margin': '10px', 'display': 'inline-block', 'verticalAlign': 'middle'}
    ),

    html.Button('Toggle Indicators Menu', id='menu-toggle-button', n_clicks=0, style={
        'float': 'right',
        'margin': '10px',
        'padding': '10px 20px',
        'backgroundColor': '#007bff',
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer'
    }),

    html.Div(
        id='indicator-menu',
        style={'display': 'none', 'position': 'absolute', 'right': '10px', 'top': '70px', 'backgroundColor': 'white', 'padding': '10px', 'border': '1px solid #ddd', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'zIndex': '1000'},
        children=[
            dcc.Checklist(
                id='indicator-selector',
                options=[{'label': col, 'value': col} for col in indicator_columns],
                value=[],
                inline=True
            )
        ]
    ),

    html.Div(
        children=[
            dcc.Dropdown(
                id='year-selector',
                options=[{'label': str(year), 'value': str(year)} for year in years],
                value='2017',
                style={'width': '200px', 'margin': '10px'}
            ),
        ],
        style={'float': 'right', 'display': 'inline-block', 'verticalAlign': 'middle'}
    ),

    dcc.Graph(id='graph')
])

@app.callback(
    [Output("graph", "figure"),
     Output("main-container", "className")],
    [Input("dark-mode-toggle", "value"),
     Input("indicator-selector", "value"),
     Input("year-selector", "value")]
)
def display_candlestick(dark_mode, selected_indicators, selected_year):
    year_data = split_data[f'{selected_year}_data']

    fig = go.Figure(go.Candlestick(
        x=year_data.index,
        open=year_data.open,
        high=year_data.high,
        low=year_data.low,
        close=year_data.close,
        name='Candlestick',
    ))

    for i, indicator_col in enumerate(selected_indicators[:5]):  # Limit to 5 indicator columns
        fig.add_trace(go.Scatter(
            x=year_data.index,
            y=year_data[indicator_col],
            mode='lines',
            name=indicator_col,
            line=dict(color=color_palettes[i % len(color_palettes)])
        ))

    if 'dark' in dark_mode:
        fig.update_layout(
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            height=800,
        )
        container_class = 'dark-mode'
    else:
        fig.update_layout(
            template='plotly',
            xaxis_rangeslider_visible=False,
            height=800,
        )
        container_class = 'light-mode'

    return fig, container_class

@app.callback(
    Output('indicator-menu', 'style'),
    [Input('menu-toggle-button', 'n_clicks')]
)
def toggle_indicator_menu(n_clicks):
    if n_clicks % 2 == 1:  # Toggle visibility
        return {'display': 'block', 'position': 'absolute', 'right': '10px', 'top': '70px', 'backgroundColor': 'white', 'padding': '10px', 'border': '1px solid #ddd', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'zIndex': '1000'}
    else:
        return {'display': 'none'}

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                box-sizing: border-box;
                outline: 1px solid red;
            }
            .dark-mode {
                background-color: #333;
                color: white;
                height: 100vh;
                width: 100vw;
                margin: 0;
                padding: 0;
            }
            .light-mode {
                background-color: white;
                color: black;
                height: 100vh;
                width: 100vw;
                margin: 0;
                padding: 0;
            }
            #headers {
                padding: 20px;
            }
            #indicator-menu {
                padding: 10px;
                background: #f8f9fa;
                border: 1px solid #ddd;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 9999;  /* Ensures menu is above other elements */
            }
        </style>
    </head>
    <body class="light-mode">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=False)