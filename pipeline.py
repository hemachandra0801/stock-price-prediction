# Simplified version using root-level imports
from fetchdata import fetch
from predict import load_latest_model
import torch
from dataeng import scale_input, unscale_predictions

import os

def run_fetch():
    os.makedirs("data/raw", exist_ok=True)  # ensure directory exists
    data = fetch()
    torch.save(data, "data/raw/latest_data.pt")

def run_predict():
    os.makedirs("data/processed", exist_ok=True)  # ensure directory exists
    model = load_latest_model('bidirectional_lstm')
    input_data = torch.load("data/raw/latest_data.pt")
    scaled = scale_input(input_data)
    predictions = model(scaled)
    unscaled = unscale_predictions(predictions)
    torch.save(unscaled, "data/processed/predictions.pt")


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "fetch":
        run_fetch()
    elif sys.argv[1] == "predict":
        run_predict()