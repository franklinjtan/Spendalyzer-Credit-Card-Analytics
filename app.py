from tabulate import tabulate
from IPython.display import display
import numpy as np
import dash
from dash import dcc
from dash import html
from funcs import clean_currency
import pandas as pd

# Load original data
df = pd.read_csv('data/transactions.csv')

# Cleaning original data
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Removes Unnamed columns
df['Amount'] = df['Amount'].apply(clean_currency).astype('float')
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')

print(df.dtypes)

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Bank Statement Analytics: Understand Your Personal Finances!"

# Create new df with only category and amount columns
cat_amount = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])  # Remove cols
cat_amount = cat_amount.groupby(cat_amount['Category'])['Amount'].sum().to_frame().reset_index()

# nLargest and nSmallest
cat_amount_top_n = cat_amount.nlargest(5, 'Amount')  # Top N
cat_amount_bottom_n = cat_amount.nsmallest(5, 'Amount')  # Bottom N

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
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
                html.Div(
                    children=[
                        html.Div(children="Top N Rankings", className="menu-title"),
                        dcc.Dropdown(
                            id="top_n",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=5,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Bottom N Rankings", className="menu-title"),
                        dcc.Dropdown(
                            id="top_n",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=5,
                            clearable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range", className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=df.Date.min().date(),
                            max_date_allowed=df.Date.max().date(),
                            start_date=df.Date.min().date(),
                            end_date=df.Date.max().date(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="line-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="bar-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)