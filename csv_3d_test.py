import plotly.express as px
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
def column_names(filename):
    column_names = ['Date', 'Description', 'Amount', 'Address',
                    'City/State', 'Zip Code', 'Country', 'Category']
    df = pd.read_csv(
        io.StringIO(decoded.decode('utf-8')), names=column_names)
    df = df.drop(df.index[0])
    return df

def create_3D_scatter(df):
    line_2df = df.groupby(['Category', 'Date', 'Zip Code'])['Amount'].sum().to_frame().reset_index()
    _3dscatter_fig = px.scatter_3d(line_2df, x = 'Date', y = 'Zip Code', z = 'Amount', color='Category',
        title="What does a plot of my transactions by category look like?",
            color_discrete_sequence=['#004c6d', '#9f1853', '#198038', '#b28600', '#8a3800', '#1192e8',
                                    '#ff7c43', '#005d5d', '#009d9a', '#012749'])
    return dcc.Graph(figure=  _3dscatter_fig)