import dash
from dash import dcc
from dash import html
from funcs import clean_currency
import pandas as pd
from dash.dependencies import Output, Input

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
                        html.Div(children="Top-Ranked Expenses", className="menu-title"),
                        dcc.Dropdown(
                            id="top_n",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=10,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Bottom-Ranked Expenses", className="menu-title"),
                        dcc.Dropdown(
                            id="bottom_n",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=10,
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
                        id="bar-chart-1",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="bar-chart-2",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                )
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    [Output("line-chart", "figure"), Output("bar-chart-1", "figure"), Output("bar-chart-2", "figure")],
    [
        Input("top_n", "value"),
        Input("bottom_n", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(top_rankings, bottom_rankings, start_date, end_date):
    # nLargest and nSmallest
    cat_amount_top_n = cat_amount.sort_values('Amount', ascending=False).head(top_rankings)  # Top N
    cat_amount_bottom_n = cat_amount.sort_values('Amount', ascending=True).head(bottom_rankings)  # Bottom N

    mask = (
        (df['Date'] >= start_date)
        & (df['Date'] <= end_date)
    )
    dff = df.loc[mask, :]
    line_chart_figure = {
        "data": [
            {
                "x": dff["Date"],
                "y": dff["Amount"],
                "type": "lines",
                "hover-template": "$%{y:.2f}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Transaction Time Series",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True, "gridcolor": '#afafae'},
            "colorway": ["#17B897"],
        },
    }

    bar_chart_figure_1 = {
        "data": [
            {
                "x": cat_amount_top_n["Category"],
                "y": cat_amount_top_n["Amount"],
                "type": "bar",
            },
        ],
        "layout": {
            "title": {"text": "Top Expense Categories", "x": 0.05, "xanchor": "left"},
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True, "gridcolor": '#afafae'},
            "colorway": ["#17B897"],
        },
    }
    bar_chart_figure_2 = {
        "data": [
            {
                "x": cat_amount_bottom_n["Category"],
                "y": cat_amount_bottom_n["Amount"],
                "type": "bar",
            },
        ],
        "layout": {
            "title": {"text": "Bottom Expense Categories", "x": 0.05, "xanchor": "left"},
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True, "gridcolor": '#afafae'},
            "colorway": ["#17B897"],
        },
    }
    return line_chart_figure, bar_chart_figure_1, bar_chart_figure_2


if __name__ == "__main__":
    app.run_server(debug=True)
