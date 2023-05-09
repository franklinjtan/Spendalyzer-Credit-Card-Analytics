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
    create_bar_chart_bottom_rankings, create_bar_chart_days_analysis, create_line_plot, create_spending_by_location, \
    create_heatmap
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import plotly.express as px

import numpy as np
import pandas as pd

from nbfuncs import nb_classifier_prediction
from csv_3d_test import create_3D_scatter

import dash_bootstrap_components as dbc

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import plotly.express as px

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family= Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
    dbc.themes.BOOTSTRAP,  # add the Bootstrap theme
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)
server = app.server
app.title = "Bank Statement Analytics"

app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Container(html.Div("🏦 Spendalyzer", className="header-title"), className="my-3",
                                      style={"height": "5vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Analyze your purchase history", className="header-description"),
                                      className="my-3", style={"height": "4vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div(dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Upload .CSV'
                            ]),
                            style={
                                'height': '10%',
                                'display': 'flex',
                                'lineHeight': '40px',
                                'justify-content': 'space-evenly',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'background-color': '#FFFFFF'
                            },
                            # Allow multiple files to be uploaded
                            multiple=True
                        )), className="my-3",
                            style={"height": "5vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div(), className="my-3",
                                      style={"background-color": "#ffffff", "height": "25vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div(""), className="my-3",
                                      style={"height": "25vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div(), className="my-3",
                                      style={"height": "7.5vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Column 1 - Row 7"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "7.5vh", "padding": "2% 2%"}),
                    ],
                    width=2,
                    style={"background-color": "#151639", "padding": "2% 2%"},
                ),
                dbc.Col(
                    [
                        dbc.Container(html.Div("Column 2 - Row 1"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Column 2 - Row 2"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Column 2 - Row 3"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "65vh", "padding": "2% 2%"}),
                    ],
                    width=3,
                    style={"background-color": "#517590", "height": "100vh", "padding": "2% 2%"},
                ),
                dbc.Col(
                    [
                        dbc.Container(html.Div("Column 3 - Row 1"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Column 3 - Row 2"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "24vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Column 3 - Row 3"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "24vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Column 3 - Row 4"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "24vh", "padding": "2% 2%"}),
                    ],
                    width=3,
                    style={"background-color": "#517590", "height": "100vh", "padding": "2% 2%"},
                ),
                dbc.Col(
                    [
                        dbc.Container(html.Div("Column 4 - Row 1"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div(
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
                            ]
                        ), className="my-3",
                            style={"background-color": "#ffffff", "height": "50vh", "padding": "2% 2%"}),
                        dbc.Container(html.Div("Column 4 - Row 2"), className="my-3",
                                      style={"background-color": "#ffffff", "height": "25vh", "padding": "2% 2%"}),
                    ],
                    width=4,
                    style={"background-color": "#517590", "height": "100vh", "padding": "2% 2%"},
                ),
            ]
        ),
    ]
)


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

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Container(html.Div("🏦 Spendalyzer", className="header-title"), className="my-3",
                                          style={"height": "5vh", "padding": "2% 2%"}),
                            dbc.Container(html.Div("Analyze your purchase history", className="header-description"),
                                          className="my-3", style={"height": "4vh", "padding": "2% 2%"}),
                            dbc.Container(html.Div(dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    'Upload .CSV'
                                ]),
                                style={
                                    'height': '10%',
                                    'display': 'flex',
                                    'lineHeight': '40px',
                                    'justify-content': 'space-evenly',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'background-color': '#FFFFFF'
                                },
                                # Allow multiple files to be uploaded
                                multiple=True
                            )), className="my-3",
                                style={"height": "5vh", "padding": "2% 2%"}),
                            dbc.Container(html.Div(children=[
                                html.Div(children="Type of Analysis Performed", className="menu-title"),
                                dcc.Dropdown(id='analysis-type',
                                             options=['All', 'Recommendations',
                                                      'Naive Bayes Text Classifier - Necessities', 'Time Series',
                                                      'Bar Chart', 'Heat Map', 'Pie Chart', 'Box Plot', 'Geo-Location',
                                                      'Spending by Location', '3-D Scatter']),
                            ]), className="my-3",
                                style={"background-color": "#ffffff", "height": "25vh", "padding": "2% 2%"}),
                            dbc.Container(html.Div(children=[
                                html.Div(children="Ranked Expenses", className="menu-title"),
                                dcc.Dropdown(
                                    id="ranked",
                                    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                    value=5,
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ]), className="my-3",
                                style={"background-color": "#ffffff", "height": "25vh", "padding": "2% 2%"}),
                            dbc.Container(html.Div(children=[
                                html.Div(children="Enter Zip Code", className="menu-title"),
                                dcc.Input(
                                    id="zipcode",
                                    className="dropdown",
                                    style={
                                        'width': '80%',
                                        'height': '25%'}
                                ),
                            ]), className="my-3",
                                style={"background-color": "#ffffff", "height": "7.5vh", "padding": "2% 2%"}),
                            dbc.Container(html.Div(children=[
                                html.Button(id="submit-button", className='app-btn',
                                            children="Generate"),
                            ]), className="my-3",
                                style={"background-color": "#ffffff", "height": "7.5vh", "padding": "2% 2%"}),
                        ],
                        width=2,
                        style={"background-color": "#151639", "padding": "2% 2%"},
                    ),
                    dbc.Col(
                        [
                            dbc.Container(html.Div(children=[
                                html.H4("File: " + filename),

                                dash_table.DataTable(
                                    data=df.to_dict('records'),
                                    columns=[{'name': i, 'id': i} for i in df.columns],
                                    page_size=5
                                ),
                                dcc.Store(id='stored-data', data=df.to_dict('records')),

                            ]), className="my-3",
                                style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
                        ],
                        width=10,
                        style={"background-color": "#517590", "height": "100vh", "padding": "2% 2%"},
                    ),
                ]
            )
        ]
    )


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

        if analysis_type == 'Recommendations':
            return create_forecast_recommendations_flagged(df)

        elif analysis_type == 'Naive Bayes Text Classifier - Necessities':
            return nb_classifier_prediction(df)

        elif analysis_type == 'Time Series':
            return create_time_series(df), create_line_plot(df, ranked)

        elif analysis_type == 'Bar Chart':
            return create_bar_chart_top_rankings(df, ranked), \
                create_bar_chart_bottom_rankings(df, ranked), \
                create_bar_chart_days_analysis(df)

        elif analysis_type == 'Heat Map':
            return create_heatmap(df)

        elif analysis_type == 'Pie Chart':
            return create_pie_chart(df)

        elif analysis_type == 'Box Plot':
            return create_box_plot(df)

        elif analysis_type == 'Geo-Location':
            return create_geo_location_plot(df)

        elif analysis_type == 'Spending by Location':
            return create_spending_by_location(df, zipcode)

        elif analysis_type == '3-D Scatter':
            return create_3D_scatter(df)

        elif analysis_type == 'All':
            return create_forecast_recommendations_flagged(df), \
                create_time_series(df), \
                create_line_plot(df, ranked), \
                create_bar_chart_top_rankings(df, ranked), \
                create_bar_chart_bottom_rankings(df, ranked), \
                create_heatmap(df),\
                create_bar_chart_days_analysis(df), \
                create_pie_chart(df), \
                create_box_plot(df), \
                create_geo_location_plot(df), \

if __name__ == '__main__':
    app.run_server(debug=True)

# app.layout = html.Div(
#     [
#         dbc.Row(
#             [
#                 dbc.Col(
#                     [
#                         dbc.Container(html.Div("🏦 Spendalyzer", className="header-title"), className="my-3",
#                                       style={"height": "5vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Analyze your purchase history", className="header-description"),
#                                       className="my-3", style={"height": "4vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div(dcc.Upload(
#                             id='upload-data',
#                             children=html.Div([
#                                 'Upload .CSV'
#                             ]),
#                             style={
#                                 'height': '10%',
#                                 'display': 'flex',
#                                 'lineHeight': '40px',
#                                 'justify-content': 'space-evenly',
#                                 'borderWidth': '1px',
#                                 'borderStyle': 'dashed',
#                                 'borderRadius': '5px',
#                                 'textAlign': 'center',
#                                 'background-color': '#FFFFFF'
#                             },
#                             # Allow multiple files to be uploaded
#                             multiple=True
#                         )), className="my-3",
#                             style={"height": "5vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div(), className="my-3",
#                             style={"background-color": "#ffffff", "height": "25vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 1 - Row 5"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "25vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 1 - Row 6"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "7.5vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 1 - Row 7"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "7.5vh", "padding": "2% 2%"}),
#                     ],
#                     width=2,
#                     style={"background-color": "#151639", "padding": "2% 2%"},
#                 ),
#                 dbc.Col(
#                     [
#                         dbc.Container(html.Div("Column 2 - Row 1"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 2 - Row 2"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 2 - Row 3"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "65vh", "padding": "2% 2%"}),
#                     ],
#                     width=2,
#                     style={"background-color": "#517590", "height": "100vh", "padding": "2% 2%"},
#                 ),
#                 dbc.Col(
#                     [
#                         dbc.Container(html.Div("Column 3 - Row 1"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 3 - Row 2"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "24vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 3 - Row 3"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "24vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 3 - Row 4"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "24vh", "padding": "2% 2%"}),
#                     ],
#                     width=3,
#                     style={"background-color": "#517590", "height": "100vh", "padding": "2% 2%"},
#                 ),
#                 dbc.Col(
#                     [
#                         dbc.Container(html.Div("Column 4 - Row 1"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "10vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div(
#                             children=[
#                                 # OUTPUT
#                                 html.Div(
#                                     id='output-datatable',
#                                     className="card",
#                                 ),
#                                 html.Div(
#                                     id='output-div',
#                                     className="card",
#                                 ),
#                             ]
#                         ), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "50vh", "padding": "2% 2%"}),
#                         dbc.Container(html.Div("Column 4 - Row 2"), className="my-3",
#                                       style={"background-color": "#ffffff", "height": "25vh", "padding": "2% 2%"}),
#                     ],
#                     width=4,
#                     style={"background-color": "#517590", "height": "100vh", "padding": "2% 2%"},
#                 ),
#             ]
#         ),
#     ]
# )
