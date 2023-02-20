import base64
import datetime
import io

import plotly.graph_objects as go
import pgeocode
import geopandas as gpd
from geopandas import GeoDataFrame

from funcs import clean_currency
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
                                     options=['All', 'Time Series', 'Bar Chart', 'Pie Chart', 'Box Plot',
                                              'Geo-Location']),
                    ]
                ),
                # INPUT DROP DOWN FOR RANKED EXPENSES
                html.Div(
                    children=[
                        html.Div(children="Ranked Expenses", className="menu-title"),
                        dcc.Dropdown(
                            id="ranked",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=10,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Button(id="submit-button",
                                    children="Create Graph",
                                    style={"min-width": "150px",
                                           "font-weight": "bold",
                                           "color": "#079A82",
                                           "height": "50px",
                                           "margin-top": "5px",
                                           "margin-left": "5px"}),
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
              )
def make_graphs(n, data, analysis_type, ranked):
    if n is None:
        return dash.no_update
    else:
        df = pd.DataFrame(data)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Removes Unnamed columns
        df['Amount'] = df['Amount'].apply(clean_currency).astype('float')
        df['Date'] = pd.to_datetime(df['Date'])

        if analysis_type == 'Time Series':
            time_fig1 = px.line(df, 'Date', 'Amount', markers=True,
                                hover_name="Category", title="What does a time series of my expenses look like?")
            time_fig1.update_traces(line_color='#17B897')

            scatter_2df = df.groupby(['Category', 'Date'])['Amount'].sum().to_frame().reset_index()
            scatter_2df['Year'] = pd.DatetimeIndex(scatter_2df['Date']).year
            scatter_fig2 = px.scatter(scatter_2df, 'Date', 'Amount', color='Category',
                                      title="What does a plot of my transactions by category look like?")
            scatter_fig2.update_traces(mode='markers', marker_line_width=2, marker_size=10)

            print(scatter_2df)

            return dcc.Graph(figure=time_fig1), dcc.Graph(figure=scatter_fig2)

        elif analysis_type == 'Bar Chart':
            # TOP RANKINGS
            cat_vs_amount_df1 = pd.DataFrame().assign(Category=df['Category'], Amount=df[
                'Amount'])  # (columns=["Description", "Address", "City/State", "Zip Code", "Country", ])
            cat_vs_amount_df1 = cat_vs_amount_df1.groupby(cat_vs_amount_df1['Category'])[
                'Amount'].sum().to_frame().reset_index()
            cat_vs_amount_df1 = cat_vs_amount_df1.sort_values('Amount', ascending=False).head(ranked)
            bar_fig1 = px.bar(cat_vs_amount_df1, 'Category', 'Amount', color='Category',
                              title="What are your top " + str(ranked) + " rankings?")

            # BOTTOM RANKINGS
            cat_vs_amount_df2 = cat_vs_amount_df1.sort_values('Amount', ascending=True).head(ranked)
            bar_fig2 = px.bar(cat_vs_amount_df2, 'Category', 'Amount', color='Category',
                              title="What are your bottom " + str(ranked) + " rankings?")

            # Transform x variable to group by day of the week
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df['Day_of_Week'] = df['Date'].dt.day_name()
            df['Day_of_Week'] = pd.Categorical(df['Day_of_Week'], categories=days_of_week, ordered=True)
            bar3_df = df.groupby(df['Day_of_Week'])['Amount'].count().to_frame().reset_index()
            bar_fig3 = px.bar(bar3_df, 'Day_of_Week', 'Amount', color='Day_of_Week',
                              title="What are your total transactions by day?")

            return dcc.Graph(figure=bar_fig1), dcc.Graph(figure=bar_fig2), dcc.Graph(figure=bar_fig3)

        elif analysis_type == 'Pie Chart':
            pie_df = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])  # Remove cols
            pie_df['Type'] = np.where(df['Category'].isin(
                ['Car Insurance', 'Car Loan', 'Car Maintenance', 'Electric Bill', 'Gas', 'Gas Bill', 'Groceries',
                 'Health Care', 'Housing', 'Internet Bill']), True, False)

            pie_df['Type'] = pie_df['Type'].replace({True: "Necessities", False: "Non-essentials"})
            pie_df = pie_df.groupby(pie_df['Type'])['Amount'].sum().to_frame().reset_index()
            colors = {'Necessities': '#17B897', 'Non-essentials': '#ff7f0e'}

            pie_fig_1 = px.pie(pie_df, values='Amount', names='Type', color='Type',
                               color_discrete_map=colors,
                               title='What does my expense breakdown by necessities and non-essentials look like?')

            return dcc.Graph(figure=pie_fig_1)

        elif analysis_type == 'Box Plot':
            box_plot = px.box(df, x="Category", y='Amount', color="Category", points="suspectedoutliers",
                              hover_name="Date", title='What outlier transactions can we detect?')
            box_plot.update_traces(quartilemethod="exclusive")
            return dcc.Graph(figure=box_plot)

        elif analysis_type == 'Geo-Location':
            nomi = pgeocode.Nominatim('us')  # Interpret zipcodes as US
            df['Latitude'] = nomi.query_postal_code(
                df['Zip Code'].tolist()).latitude  # Create column that loads in the latitude based on Zip Code
            df['Longitude'] = nomi.query_postal_code(
                df['Zip Code'].tolist()).longitude  # Create column that loads in the longitude based on Zip Code

            map_fig = go.Figure(data=go.Scattergeo(
                lon=df['Longitude'],
                lat=df['Latitude'],
                text=df['City/State'],
                mode='markers',
                marker_color=df['Amount'],
                marker=dict(
                    size=4,
                    opacity=0.8,
                    reversescale=True,
                    autocolorscale=False,
                    symbol='square',
                    line=dict(
                        width=4,
                        color='#B31942'
                    ),
                ))
            )
            map_fig.update_layout(
                geo=dict(
                    showland=True,
                    landcolor="#0A3161",
                    subunitcolor="rgb(255, 255, 255)",
                    showsubunits=True,
                    resolution=50,
                    lonaxis=dict(
                        showgrid=True,
                        gridwidth=0.5,
                        range=[-140.0, -55.0],
                        dtick=5
                    ),
                    lataxis=dict(
                        showgrid=True,
                        gridwidth=0.5,
                        range=[20.0, 60.0],
                        dtick=5
                    )
                ),
                title='Where are your purchases?',
                geo_scope='usa',
                width=1400,
                height=600,
            )
            return dcc.Graph(figure=map_fig)

        elif analysis_type == 'All':
            # TIME SERIES
            time_fig1 = px.line(df, 'Date', 'Amount', markers=True,
                                hover_name="Category", title="What does a time series of my expenses look like?")
            time_fig1.update_traces(line_color='#17B897')

            # SCATTER PLOT
            scatter_2df = df.groupby(['Category', 'Date'])['Amount'].sum().to_frame().reset_index()
            scatter_fig2 = px.scatter(scatter_2df, 'Date', 'Amount', color='Category',
                                      title="What does a plot of my transactions by category look like?")
            scatter_fig2.update_traces(mode='markers', marker_line_width=2, marker_size=10)

            # BAR CHART
            cat_vs_amount_df1 = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])
            cat_vs_amount_df1 = cat_vs_amount_df1.groupby(cat_vs_amount_df1['Category'])[
                'Amount'].sum().to_frame().reset_index()
            cat_vs_amount_df1 = cat_vs_amount_df1.sort_values('Amount', ascending=False).head(ranked)
            bar_fig1 = px.bar(cat_vs_amount_df1, 'Category', 'Amount', color='Category',
                              title="What are your top " + str(ranked) + " rankings?")

            # BOTTOM RANKINGS
            cat_vs_amount_df2 = cat_vs_amount_df1.sort_values('Amount', ascending=True).head(ranked)
            bar_fig2 = px.bar(cat_vs_amount_df2, 'Category', 'Amount', color='Category',
                              title="What are your top " + str(ranked) + " rankings?")

            # Transform x variable to group by day of the week
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df['Day_of_Week'] = df['Date'].dt.day_name()
            df['Day_of_Week'] = pd.Categorical(df['Day_of_Week'], categories=days_of_week, ordered=True)
            bar3_df = df.groupby(df['Day_of_Week'])['Amount'].count().to_frame().reset_index()
            bar_fig3 = px.bar(bar3_df, 'Day_of_Week', 'Amount', color='Day_of_Week',
                              title="What are your total transactions by day?")

            # PIE CHART
            pie_df = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])  # Remove cols
            pie_df['Type'] = np.where(df['Category'].isin(
                ['Car Insurance', 'Car Loan', 'Car Maintenance', 'Electric Bill', 'Gas', 'Gas Bill', 'Groceries',
                 'Health Care', 'Housing', 'Internet Bill']), True, False)

            pie_df['Type'] = pie_df['Type'].replace({True: "Necessities", False: "Non-essentials"})
            pie_df = pie_df.groupby(pie_df['Type'])['Amount'].sum().to_frame().reset_index()
            colors = {'Necessities': '#17B897', 'Non-essentials': '#ff7f0e'}

            pie_fig_1 = px.pie(pie_df, values='Amount', names='Type', color='Type',
                               color_discrete_map=colors,
                               title='What does my expense breakdown by necessities and non-essentials look like?')

            # BOX PLOT
            box_plot = px.box(df, x="Category", y='Amount', color="Category", points="suspectedoutliers",
                              hover_name="Date", title='What outlier transactions can we detect?')
            box_plot.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default

            # GEO-LOCATION
            nomi = pgeocode.Nominatim('us')  # Interpret zipcodes as US
            df['Latitude'] = nomi.query_postal_code(
                df['Zip Code'].tolist()).latitude  # Create column that loads in the latitude based on Zip Code
            df['Longitude'] = nomi.query_postal_code(
                df['Zip Code'].tolist()).longitude  # Create column that loads in the longitude based on Zip Code

            map_fig = go.Figure(data=go.Scattergeo(
                lon=df['Longitude'],
                lat=df['Latitude'],
                text=df['City/State'],
                mode='markers',
                marker_color=df['Amount'],
                marker=dict(
                    size=4,
                    opacity=0.8,
                    reversescale=True,
                    autocolorscale=False,
                    symbol='square',
                    line=dict(
                        width=4,
                        color='#B31942'
                    ),
                ))
            )
            map_fig.update_layout(
                geo=dict(
                    showland=True,
                    landcolor="#0A3161",
                    subunitcolor="rgb(255, 255, 255)",
                    showsubunits=True,
                    resolution=50,
                    lonaxis=dict(
                        showgrid=True,
                        gridwidth=0.5,
                        range=[-140.0, -55.0],
                        dtick=5
                    ),
                    lataxis=dict(
                        showgrid=True,
                        gridwidth=0.5,
                        range=[20.0, 60.0],
                        dtick=5
                    )
                ),
                title='Where are your purchases?',
                geo_scope='usa',
                width=1400,
                height=600,
            )

            # TABLE
            # avg_df = df.groupby(df['Category'])['Amount'].mean().to_frame().reset_index()
            df2 = df.loc[:, ['Date', 'Category', 'Amount']]
            # df2.rename(columns={'level_1': 'SMA7'})

            # avg_df_fig = go.Figure(data=[go.Table(
            #     header=dict(values=list(avg_df.columns),
            #                 fill_color='#17becf',
            #                 align='left'),
            #     cells=dict(values=[avg_df.Category, avg_df.Amount],
            #                fill_color='lavender',
            #                align='left'))
            # ]
            # )

            df2_fig = go.Figure(data=[go.Table(
                header=dict(values=list(df2.columns),
                            fill_color='#17becf',
                            align='left'),
                cells=dict(values=[df.Date, df2.Category, df2.Amount],
                           fill_color='lavender',
                           align='left'))
            ]
            )
            return dcc.Graph(figure=time_fig1), dcc.Graph(figure=scatter_fig2), dcc.Graph(figure=bar_fig1), dcc.Graph(
                figure=bar_fig2), dcc.Graph(figure=bar_fig3), dcc.Graph(figure=pie_fig_1), dcc.Graph(
                figure=box_plot), dcc.Graph(figure=map_fig), dcc.Graph(figure=df2_fig)


if __name__ == '__main__':
    app.run_server(debug=True)
