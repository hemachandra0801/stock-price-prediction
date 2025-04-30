# Simplified version using root-level imports
from fetchdata import fetch
from model import load_latest_model
import torch
from dataeng import scale_input, unscale_predictions

def run_fetch():
    data = fetch()
    torch.save(data, "data/raw/latest_data.pt")

def run_predict():
    model = load_latest_model()
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