import base64
import datetime
import io

import plotly.graph_objects as go
import pgeocode
import geopandas as gpd
from geopandas import GeoDataFrame

from funcs import clean_currency, create_forecast_recommendations_flagged, create_forecast_recommendations_all, \
    create_time_series, create_pie_chart, create_box_plot, create_geo_location_plot, \
    create_bar_chart_top_rankings, \
    create_bar_chart_bottom_rankings, create_bar_chart_days_analysis, create_line_plot, create_spending_by_location
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import plotly.express as px

import numpy as np
import pandas as pd

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family= Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)
server = app.server
app.title = "Bank Statement Analytics: Understand Your Personal Finances!"

app.layout = html.Div([  # this code section taken from Dash docs https://dash.plotly.com/dash-core-components/upload
    html.Div(
        children=[
            html.P(children="🏦", className="header-emoji"),
            html.H1(
                children="Bank Statement Analytics", className="header-title"
            ),
            html.P(
                children="Analyze purchase history and behavior",
                className="header-description",
            ),
        ],
        className="header",
    ),
    html.Div(
        children=[
            html.Div(children="", className="menu-title"),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Upload .csv file'
                ]),
                style={
                    'width': '10%',
                    'height': '10%',
                    'display': 'flex',
                    'lineHeight': '60px',
                    'justify-content': 'space-evenly',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '-140px auto 40px auto',
                    'background-color': '#FFFFFF'
                },
                # Allow multiple files to be uploaded
                multiple=True
            ),
            html.Div(id='output-data-upload'),
        ],
        className="upload",
    ),

    html.Div(
        children=[
            # OUTPUT
            html.Div(
                id='output-datatable',
                className="card",
            ),
            html.Div(
                id='output-div',
                className="card",
            ),
        ],
        className="wrapper",
    ),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' or 'CSV' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))

            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Removes Unnamed columns
        elif 'xls' or 'xlsx' in filename:
            # Assume that the user uploaded an Excel file
            df = pd.read_excel(io.BytesIO(decoded))

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.Div(
            children=[
                # INPUT TYPE OF ANALYSIS
                html.Div(
                    children=[
                        html.Div(children="Type of Analysis Performed", className="menu-title"),
                        dcc.Dropdown(id='analysis-type',
                                     options=['All', 'SMA + ES Forecast', 'Time Series', 'Bar Chart',
                                              'Pie Chart', 'Box Plot',
                                              'Geo-Location', 'Spending by Location']),
                    ]
                ),

                # INPUT DROP DOWN FOR RANKED EXPENSES
                html.Div(
                    children=[
                        html.Div(children="Ranked Expenses", className="menu-title"),
                        dcc.Dropdown(
                            id="ranked",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=5,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),

                # INPUT ZIP CODE
                html.Div(
                    children=[
                        html.Div(children="Enter Zip Code", className="menu-title"),
                        dcc.Input(
                            id="zipcode",
                            className="dropdown",
                            style={
                                'width': '60%',
                                'height': '60%'}
                        ),
                    ]
                ),

                html.Div(
                    children=[
                        html.Button(id="submit-button", className='app-btn',
                                    children="Generate"),
                    ],
                ),
            ],
            className="menu",
        ),

        html.Div(
            children=[
                html.H4("File: " + filename),

                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in df.columns],
                    page_size=5
                ),
                dcc.Store(id='stored-data', data=df.to_dict('records')),

            ],
            className="wrapper",
        ),
    ])


@app.callback(Output('output-datatable', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


@app.callback(Output('output-div', 'children'),
              Input('submit-button', 'n_clicks'),
              State('stored-data', 'data'),
              State('analysis-type', 'value'),
              State('ranked', 'value'),
              State('zipcode', 'value')
              )
def make_graphs(n, data, analysis_type, ranked, zipcode):
    if n is None:
        return dash.no_update
    else:
        df = pd.DataFrame(data)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Removes Unnamed columns
        df['Amount'] = df['Amount'].apply(clean_currency).astype('float')
        df['Date'] = pd.to_datetime(df['Date'])

        if analysis_type == 'SMA + ES Forecast':
            return create_forecast_recommendations_all(df), create_forecast_recommendations_flagged(df)

        elif analysis_type == 'Time Series':
            return create_time_series(df), create_line_plot(df, ranked)

        elif analysis_type == 'Bar Chart':
            return create_bar_chart_top_rankings(df, ranked), \
                create_bar_chart_bottom_rankings(df, ranked), \
                create_bar_chart_days_analysis(df)

        elif analysis_type == 'Pie Chart':
            return create_pie_chart(df)

        elif analysis_type == 'Box Plot':
            return create_box_plot(df)

        elif analysis_type == 'Geo-Location':
            return create_geo_location_plot(df)

        elif analysis_type == 'Spending by Location':
            return create_spending_by_location(df, zipcode)

        elif analysis_type == 'All':
            return create_forecast_recommendations_all(df),\
                create_forecast_recommendations_flagged(df), \
                create_time_series(df), \
                create_line_plot(df, ranked), \
                create_bar_chart_top_rankings(df, ranked), \
                create_bar_chart_bottom_rankings(df, ranked), \
                create_bar_chart_days_analysis(df), \
                create_pie_chart(df), \
                create_box_plot(df), \
                create_geo_location_plot(df)
                create_spending_by_location(df, zipcode)

if __name__ == '__main__':
    app.run_server(debug=True)