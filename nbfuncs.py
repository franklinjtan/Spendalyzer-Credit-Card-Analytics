import pandas as pd
import numpy as np
from dash import dcc
from nltk.probability import FreqDist
from nltk.corpus import stopwords
from nltk.classify import NaiveBayesClassifier
from nltk.tokenize import word_tokenize
import plotly.graph_objects as go

import nltk

nltk.download('stopwords')
nltk.download('punkt')


def nb_classifier_prediction(df):
    learn_df = pd.read_csv('data/transactions.csv')
    cleaned_df = learn_df.drop(columns=["Address", "City/State", "Zip Code", "Country", "Amount"])  # Remove cols
    cleaned_df['Necessity'] = np.where(learn_df['Category'].isin(
        ['Car Insurance', 'Car Loan', 'Car Maintenance', 'Electric Bill', 'Gas', 'Gas Bill', 'Groceries',
         'Health Care', 'Housing', 'Internet Bill']), True, False)

    # Define the stop words
    stop_words = set(stopwords.words('english'))

    # Define the necessary categories
    necessary_categories = ['Car Insurance', 'Car Loan', 'Car Maintenance', 'Electric Bill', 'Gas', 'Gas Bill',
                            'Groceries', 'Health Care', 'Housing', 'Internet Bill']

    # Clean the text
    cleaned_text = []
    for text in learn_df['Description']:
        # Tokenize the text
        words = word_tokenize(text)
        # Remove stop words and punctuation
        words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]
        cleaned_text.append(words)

    # Get the frequency distribution of the words
    all_words = []
    for words in cleaned_text:
        all_words += words
    fd = FreqDist(all_words)

    # Define a feature extractor function that returns a dictionary of word frequencies
    def document_features(document):
        document_words = set(document)
        features = {}
        for word in fd.keys():
            features['contains({})'.format(word)] = (word in document_words)
        return features

    # Create a labeled feature set
    featuresets = [(document_features(text), category in necessary_categories) for text, category in
                   zip(cleaned_text, learn_df['Category'])]

    # Split the data into training and testing sets
    train_set, test_set = featuresets[100:], featuresets[:100]

    # Train the classifier
    classifier = NaiveBayesClassifier.train(train_set)

    # Test the classifier
    accuracy = nltk.classify.util.accuracy(classifier, test_set)
    print('Accuracy:', accuracy)

    # Load new data
    data_new = df
    df_new = pd.DataFrame(data_new)

    # Clean the text
    cleaned_text_new = []
    for text in df_new['Description']:
        # Tokenize the text
        words = word_tokenize(text)
        # Remove stop words and punctuation
        words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]
        cleaned_text_new.append(words)

    # Get the predictions for the new data
    predictions = []
    for text in cleaned_text_new:
        predictions.append(classifier.classify(document_features(text)))

    # Create a new DataFrame that includes the predicted values
    results_df = pd.DataFrame({'Description': df_new['Description'], 'Predicted_Necessity': predictions})

    predictions_fig = go.Figure(data=[go.Table(
        header=dict(values=list(results_df.columns),
                    fill_color='#004c6d',
                    font_color='white',
                    align='left'),
        cells=dict(values=[results_df.Description, results_df.Predicted_Necessity],
                   fill_color='#a7b8c6',
                   font_color='black',
                   align='left'))
    ])
    return dcc.Graph(figure=predictions_fig)
