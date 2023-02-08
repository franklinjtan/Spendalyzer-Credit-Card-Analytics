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
data = pd.read_csv('data/transactions.csv', index_col=False)
df = pd.DataFrame(data)

# Cleaning original data
df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # Removes Unnamed columns
df['Amount'] = df['Amount'].apply(clean_currency).astype('float')

# Create new df with only category and amount columns
cat_amount = df.drop(columns=["Date", "Description", "Address", "City/State", "Zip Code", "Country",]) # Remove cols
cat_amount = cat_amount.groupby(cat_amount['Category'])['Amount'].sum().reset_index()
cat_amount_top_n = cat_amount.sort_values('Amount',ascending = False).head(4) # Top N

sns.barplot(data = cat_amount_top_n, x = 'Category', y = 'Amount', palette = 'deep')
plt.show();

print(cat_amount_top_n)
# print(cat_amount_top_n)

