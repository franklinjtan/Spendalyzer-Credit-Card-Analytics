from matplotlib import pyplot as plt
from tabulate import tabulate
from IPython.display import display
import dash
import inline as inline
import matplotlib as matplotlib
from dash import dcc
from dash import html
import seaborn as sns
from funcs import clean_currency
import pandas as pd

# Load original data
df = pd.read_csv('data/transactions.csv')

# Cleaning original data
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Removes Unnamed columns
df['Amount'] = df['Amount'].apply(clean_currency).astype('float')

# Create new df with only category and amount columns
cat_amount = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])  # Remove cols
cat_amount = cat_amount.groupby(cat_amount['Category'])['Amount'].sum().to_frame().reset_index()

# nLargest and nSmallest
cat_amount_top_n = cat_amount.nlargest(5, 'Amount')  # Top N
cat_amount_bottom_n = cat_amount.nsmallest(5, 'Amount')  # Bottom N

print(cat_amount_top_n)
print("-----")
print(cat_amount_bottom_n)

