"""Reusable wrapper around the existing validated cleaning pipeline."""
from ml.clean_data import clean_csv

def preprocess(source, destination):
    return clean_csv(source, destination)
