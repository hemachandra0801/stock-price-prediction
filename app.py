import torch
from pathlib import Path

file_path = Path("/home/hiran/Desktop/mlops/project/stock-price-prediction/data/processed/predictions.pt")

# Allow full object loading (safe only if you trust the file)
data = torch.load(file_path, weights_only=False)

print(data)
