from predict import load_latest_model, predict_with_model

from fetchdata import fetch


import torch
from dataeng import scale_input, unscale_predictions

model = load_latest_model("bidirectional_lstm")

random_input = fetch()

scaled_input = scale_input(random_input)

scaled = predict_with_model(model, scaled_input)

unscaled = unscale_predictions(scaled)

print(unscaled)