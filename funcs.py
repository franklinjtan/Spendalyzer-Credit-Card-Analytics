import datetime

import plotly.graph_objects as go
import pgeocode
import geopandas as gpd
from geopandas import GeoDataFrame

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import plotly.express as px

import numpy as np
import pandas as pd


def clean_currency(x):
    """ If the value is a string, then remove currency symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(x, str):
        return x.replace('$', '').replace(',', '')
    return (x)


def create_forecast_recommendations_all(df):
    df = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country"])

    avg_df = df.groupby(['Category'])['Amount'].mean().to_frame().reset_index()
    avg_df = avg_df.rename(columns={'Amount': 'Average'})

    # creating new dataframes for sma and es forecasts
    sma_df = df
    exp_smooth_df = df

    # simple moving average forecast of each category
    sma_df = df.groupby(['Category'])['Amount'].rolling(window=4).mean().to_frame().reset_index()
    sma_df.columns = ['Category', 'level_1', 'SMA']

    most_recent_sma_df = sma_df.groupby('Category').tail(1)

    forecasts = pd.merge(most_recent_sma_df, avg_df, on="Category", how="left")
    forecasts = forecasts.reindex(columns=['Category', 'level_1', 'Average', 'SMA'])

    # exponential smoothing forecast of each category

    # define alpha value
    alpha = 0.2

    # group transactions by category
    grouped = exp_smooth_df.groupby('Category')

    # create a new empty column for the exponential smoothed amounts

    # iterate through each group
    for group_name, group_data in grouped:
        # get the indices for the current group
        group_indices = group_data.index

        # perform exponential smoothing on the amount column for the current group
        smoothed = group_data['Amount'].ewm(alpha=alpha).mean()

        # update the smoothed amounts for the current group in the main dataframe
        exp_smooth_df.loc[group_indices, 'ES'] = smoothed

    exp_smooth_df = exp_smooth_df.groupby('Category').tail(1)

    # merge back with forecast
    forecasts = pd.merge(forecasts, exp_smooth_df[['Category', 'ES']], on="Category", how="inner")

    forecasts['Flagged_SMA'] = np.where(forecasts['SMA'] > forecasts['Average'], 'Yes', 'No')
    forecasts['Flagged_ES'] = np.where(forecasts['ES'] > forecasts['Average'], 'Yes', 'No')

    flagged_categories = forecasts[(forecasts['Flagged_SMA'] == 'Yes') & (forecasts['Flagged_ES'] == 'Yes')][
        ['Category', 'Average', 'SMA', 'ES', 'Flagged_SMA', 'Flagged_ES']]

    # calculate percentage change from SMA and average to average for every category
    forecasts['pct_change_SMA'] = (forecasts['SMA'] - forecasts['Average']) / \
                                  forecasts['Average'] * 100
    forecasts['pct_change_ES'] = (forecasts['ES'] - forecasts['Average']) / \
                                 forecasts['Average'] * 100

    # round all int values to 2 decimal places
    forecasts[['Average', 'SMA', 'ES', 'pct_change_SMA', 'pct_change_ES']] = forecasts[
        ['Average', 'SMA', 'ES', 'pct_change_SMA', 'pct_change_ES']].round(2)

    forecasts = forecasts.drop(columns='level_1')
    # TABLE
    all_categories_fig = go.Figure(data=[go.Table(
        header=dict(values=list(forecasts.columns),
                    fill_color='#004c6d',
                    font_color='white',
                    align='left'),
        cells=dict(
            values=[forecasts.Category, forecasts.Average, forecasts.SMA,
                    forecasts.ES, forecasts.Flagged_SMA, forecasts.Flagged_ES,
                    forecasts.pct_change_SMA, forecasts.pct_change_ES],
            fill_color='#a7b8c6',
            font_color='black',
            align='left')),
    ])

    return dcc.Graph(figure=all_categories_fig)


def create_forecast_recommendations_flagged(df):
    df = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country"])

    avg_df = df.groupby(['Category'])['Amount'].mean().to_frame().reset_index()
    avg_df = avg_df.rename(columns={'Amount': 'Average'})

    # creating new dataframes for sma and es forecasts
    sma_df = df
    exp_smooth_df = df

    # simple moving average forecast of each category
    sma_df = df.groupby(['Category'])['Amount'].rolling(window=4).mean().to_frame().reset_index()
    sma_df.columns = ['Category', 'level_1', 'SMA']

    most_recent_sma_df = sma_df.groupby('Category').tail(1)

    forecasts = pd.merge(most_recent_sma_df, avg_df, on="Category", how="left")
    forecasts = forecasts.reindex(columns=['Category', 'level_1', 'Average', 'SMA'])

    # exponential smoothing forecast of each category

    # define alpha value
    alpha = 0.2

    # group transactions by category
    grouped = exp_smooth_df.groupby('Category')

    # create a new empty column for the exponential smoothed amounts

    # iterate through each group
    for group_name, group_data in grouped:
        # get the indices for the current group
        group_indices = group_data.index

        # perform exponential smoothing on the amount column for the current group
        smoothed = group_data['Amount'].ewm(alpha=alpha).mean()

        # update the smoothed amounts for the current group in the main dataframe
        exp_smooth_df.loc[group_indices, 'ES'] = smoothed

    exp_smooth_df = exp_smooth_df.groupby('Category').tail(1)

    # merge back with forecast
    forecasts = pd.merge(forecasts, exp_smooth_df[['Category', 'ES']], on="Category", how="inner")

    forecasts['Flagged_SMA'] = np.where(forecasts['SMA'] > forecasts['Average'], 'Yes', 'No')
    forecasts['Flagged_ES'] = np.where(forecasts['ES'] > forecasts['Average'], 'Yes', 'No')

    flagged_categories = forecasts[(forecasts['Flagged_SMA'] == 'Yes') & (forecasts['Flagged_ES'] == 'Yes')][
        ['Category', 'Average', 'SMA', 'ES', 'Flagged_SMA', 'Flagged_ES']]

    # calculate percentage change from SMA and average to average for every category
    forecasts['pct_change_SMA'] = (forecasts['SMA'] - forecasts['Average']) / \
                                  forecasts['Average'] * 100
    forecasts['pct_change_ES'] = (forecasts['ES'] - forecasts['Average']) / \
                                 forecasts['Average'] * 100

    flagged_categories['pct_change_SMA'] = (flagged_categories['SMA'] - flagged_categories['Average']) / \
                                           flagged_categories['Average'] * 100
    flagged_categories['pct_change_ES'] = (flagged_categories['ES'] - flagged_categories['Average']) / \
                                          flagged_categories['Average'] * 100

    # round all int values to 2 decimal places
    forecasts[['Average', 'SMA', 'ES', 'pct_change_SMA', 'pct_change_ES']] = forecasts[
        ['Average', 'SMA', 'ES', 'pct_change_SMA', 'pct_change_ES']].round(2)

    flagged_categories[['Average', 'SMA', 'ES', 'pct_change_SMA', 'pct_change_ES']] = flagged_categories[
        ['Average', 'SMA', 'ES', 'pct_change_SMA', 'pct_change_ES']].round(2)

    forecasts = forecasts.drop(columns='level_1')
    # TABLE

    flagged_fig = go.Figure(data=[go.Table(
        header=dict(values=list(flagged_categories.columns),
                    fill_color='#004c6d',
                    font_color='white',
                    align='left'),
        cells=dict(
            values=[flagged_categories.Category, flagged_categories.Average, flagged_categories.SMA,
                    flagged_categories.ES, flagged_categories.Flagged_SMA, flagged_categories.Flagged_ES,
                    flagged_categories.pct_change_SMA, flagged_categories.pct_change_ES],
            fill_color='#a7b8c6',
            font_color='black',
            align='left')),
    ])
    message = ""

    for index, row in flagged_categories.iterrows():
        message += "Flagged Category: {}<br>SMA and the ES forecasts are projected to surpass the average of ${}. SMA and ES Forecasts indicate an increase of {:.2f}% and {:.2f}%, respectively.<br><br>".format(
            row['Category'], row['Average'], row['pct_change_SMA'], row['pct_change_ES'])

    flagged_fig.update_layout(
        title='SMA and ES Forecasts',
        height=800,
        annotations=[
            go.layout.Annotation(
                x=0,
                y=0.05,
                align="left",
                showarrow=False,
                text=message,
                xref="paper",
                yref="paper",
                font=dict(
                    family="Arial",
                    size=14,
                    color="black"
                )
            )
        ]
    )

    return dcc.Graph(figure=flagged_fig)


def create_time_series(df):
    time_fig1 = px.line(df, 'Date', 'Amount', markers=True,
                        hover_name="Category", title="What does a time series of my expenses look like?")
    time_fig1.update_traces(line_color='#004c6d')
    return dcc.Graph(figure=time_fig1)


def create_line_plot(df, ranked):
    line_2df = df.groupby(['Category', 'Date'])['Amount'].sum().to_frame().reset_index()
    top_categories = line_2df.groupby('Category')['Amount'].sum().sort_values(ascending=False).index[:ranked]
    line_2df = line_2df[line_2df['Category'].isin(top_categories)]
    line_fig2 = px.line(line_2df, 'Date', 'Amount', color='Category',
                        title="What does a plot of my transactions by category look like? (Top " + str(
                            ranked) + " rankings)",
                        color_discrete_sequence=['#004c6d', '#9f1853', '#198038', '#b28600', '#8a3800', '#1192e8',
                                                 '#ff7c43', '#005d5d', '#009d9a', '#012749'])
    # color_discrete_sequence=px.colors.qualitative.Safe)
    line_fig2.update_traces(mode='lines+markers', marker_line_width=2, marker_size=10)
    return dcc.Graph(figure=line_fig2)


def create_bar_chart_top_rankings(df, ranked):
    # TOP RANKINGS
    cat_vs_amount_df1 = pd.DataFrame().assign(Category=df['Category'], Amount=df[
        'Amount'])  # (columns=["Description", "Address", "City/State", "Zip Code", "Country", ])
    cat_vs_amount_df1 = cat_vs_amount_df1.groupby(cat_vs_amount_df1['Category'])[
        'Amount'].sum().to_frame().reset_index()
    cat_vs_amount_df1 = cat_vs_amount_df1.sort_values('Amount', ascending=False).head(ranked)
    bar_fig1 = px.bar(cat_vs_amount_df1, 'Category', 'Amount', color='Category',
                      title="What are your top " + str(ranked) + " rankings?",
                      color_discrete_sequence=['#004c6d', '#155b79', '#2b6a85', '#407992', '#55889e', '#6a97aa',
                                               '#80a6b6', '#95b4c2', '#aac3ce', '#bfd2db'])

    return dcc.Graph(figure=bar_fig1)


def create_bar_chart_bottom_rankings(df, ranked):
    cat_vs_amount_df1 = pd.DataFrame().assign(Category=df['Category'], Amount=df[
        'Amount'])  # (columns=["Description", "Address", "City/State", "Zip Code", "Country", ])
    cat_vs_amount_df1 = cat_vs_amount_df1.groupby(cat_vs_amount_df1['Category'])[
        'Amount'].sum().to_frame().reset_index()

    # BOTTOM RANKINGS
    cat_vs_amount_df2 = cat_vs_amount_df1.sort_values('Amount', ascending=True).head(ranked)
    bar_fig2 = px.bar(cat_vs_amount_df2, 'Category', 'Amount', color='Category',
                      title="What are your bottom " + str(ranked) + " rankings?",
                      color_discrete_sequence=['#004c6d', '#155b79', '#2b6a85', '#407992', '#55889e', '#6a97aa',
                                               '#80a6b6', '#95b4c2', '#aac3ce', '#bfd2db'])

    return dcc.Graph(figure=bar_fig2)


def create_bar_chart_days_analysis(df):
    # Transform x variable to group by day of the week
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['Day_of_Week'] = df['Date'].dt.day_name()
    df['Day_of_Week'] = pd.Categorical(df['Day_of_Week'], categories=days_of_week, ordered=True)
    bar3_df = df.groupby(df['Day_of_Week'])['Amount'].count().to_frame().reset_index()
    bar3_df = bar3_df.sort_values(by='Amount', ascending=False)
    bar_fig3 = px.bar(bar3_df, 'Day_of_Week', 'Amount', color='Day_of_Week',
                      color_discrete_sequence=['#004c6d', '#29617d', '#46778d', '#618d9e', '#7da3af', '#9abac1',
                                               '#b8d1d5'],
                      title="What are your total transactions by day?")

    return dcc.Graph(figure=bar_fig3)


def create_heatmap(df):
    # Create a pivot table with categories as rows, months as columns and the sum of amounts as values
    df_pivot = pd.pivot_table(df, values='Amount', index='Category', columns=df['Date'].dt.strftime('%Y-%m'),
                              aggfunc=np.sum)

    # Create a heatmap using Plotly
    heatmap_fig = px.imshow(df_pivot.values,
                            labels=dict(x="Month", y="Category", color="Amount"),
                            x=df_pivot.columns,
                            y=df_pivot.index,
                            color_continuous_scale='Blues'
                            )

    heatmap_fig.update_layout(
        title='Transactions by Category and Month',
        xaxis_nticks=len(df_pivot.columns),
        yaxis_nticks=len(df_pivot.index),
        coloraxis=dict(colorbar=dict(title='Sum of Amounts'))
    )

    return dcc.Graph(figure=heatmap_fig)


def create_pie_chart(df):
    pie_df = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])  # Remove cols
    pie_df['Type'] = np.where(df['Category'].isin(
        ['Car Insurance', 'Car Loan', 'Car Maintenance', 'Electric Bill', 'Gas', 'Gas Bill', 'Groceries',
         'Health Care', 'Housing', 'Internet Bill']), True, False)

    pie_df['Type'] = pie_df['Type'].replace({True: "Necessities", False: "Non-essentials"})
    pie_df = pie_df.groupby(pie_df['Type'])['Amount'].sum().to_frame().reset_index()
    colors = {'Necessities': '#003f5c', 'Non-essentials': '#8a3800'}

    pie_fig_1 = px.pie(pie_df, values='Amount', names='Type', color='Type',
                       color_discrete_map=colors,
                       title='What does my expense breakdown by necessities and non-essentials look like?')

    return dcc.Graph(figure=pie_fig_1)


def create_box_plot(df):
    box_plot = px.box(df, x="Category", y='Amount', color="Category", points="suspectedoutliers",
                      color_discrete_sequence=['#004c6d', '#155b79', '#2b6a85', '#407992', '#55889e', '#6a97aa',
                                               '#80a6b6', '#95b4c2', '#aac3ce', '#bfd2db'],
                      hover_name="Date", title='What outlier transactions can we detect?', )
    box_plot.update_traces(quartilemethod="exclusive")
    return dcc.Graph(figure=box_plot)


def create_geo_location_plot(df):
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
            landcolor="#004c6d",
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


def create_spending_by_location(df, zipcode):
    if len(zipcode) >= 5:
        df['PrimaryZip'] = np.where(df['Zip Code'] == zipcode, 'Primary Zip Code', 'Not Primary Zip Code')
        box_plot = px.box(df, x="PrimaryZip", y='Amount', color="PrimaryZip", points="suspectedoutliers",
                          color_discrete_sequence=['#004c6d'],
                          hover_name="Amount", title='What does spending look like outside our home address?',
                          labels="Primary Zip Code vs. Other Zip Code")
        box_plot.update_traces(quartilemethod="exclusive")
        return dcc.Graph(figure=box_plot)
    else:
        return 'Zipcode must be at least 5 characters long'
