# Spendalyzer - A Bank Statement Analytics Application

## About
* An interactive web application that allows users to analyze their purchase history, understand their purchasing behavior, and receive recommendations based on advanced scientific forecasts.<br>
* Featured functionality includes ability to read AMEX transaction descriptions and classify, using Naive Bayes whether a transaction is a necessity or not. Currently, users specify which categories are necessities.
* Used pandas, numpy, dash, nltk, and plotly libraries for data wrangling, data visualizations, web application framework, and ML algorithms.
* Next steps in no particular order would be to add new functionalities such as classifying expenses in a category using a ML Algorithm, reading in statement transaction from other banks (using Computer Vision), getting feedback from users, and hosting the site.
![Spendalyzer](/images/Spendalyzer.png)
![Recommendations](/images/SMA-and-ES-Forecasting.png)
![Spending Heatmap](/images/Heatmap-of-Transactions.png)
![Time Series of Spending](/images/time-series-transactions.png)

## Researching Exponential Smoothing vs. Moving Average
* For the application, we use both exponential smoothing and moving average forecasts to identify patterns and trends in the data. While both methods are useful for smoothing out fluctuations in a time series, they differ in how they weight historical data. Moving average is a simple and effective method for identifying trends and removing random fluctuations in the data. We use a fixed number of past data points, referred to as the "window size," to calculate the moving average.
* However, moving average can lag behind the actual data and may not capture sudden changes or sharp turning points. Despite its limitations, moving average is easy to use and understand, making it a valuable tool for our application. Exponential smoothing, on the other hand, is a more complex method that assigns exponentially decreasing weights to past data points. This means that recent data points are given more weight than older data points, allowing the model to adjust more quickly to sudden changes or sharp turning points. This can be especially useful for our application in the current economic conditions where rising interest rates, inflation, and other economic factors can lead to sudden changes in spending patterns. Exponential smoothing can help us capture these changes more quickly and accurately, making it a better choice for our application in some cases.

* Exponential smoothing, on the other hand, is a more sophisticated method that gives more weight to recent data and less weight to older data. This is done by applying a smoothing factor or weight to each historical data point, with the weights declining exponentially as the data gets older. Exponential smoothing can be more accurate in predicting short-term trends and can react more quickly to changes in the data. It can also be adjusted to incorporate seasonality and trend changes. However, it requires more knowledge and experience to implement and tune the smoothing factor.

* In summary, moving average is a good choice for simple, straightforward time series data, while exponential smoothing is better for data with more complexity and volatility. The choice between these methods ultimately depends on the data and the specific goals of the analysis.
