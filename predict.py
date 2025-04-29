import mlflow
import torch
import pandas as pd
import numpy as np
import joblib



def load_latest_model(experiment_name):
    """Load the latest model from an experiment"""
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    
    if not experiment:
        raise ValueError(f"Experiment {experiment_name} not found")
    
    # Get best run (sorted by validation loss)
    runs = client.search_runs(
        experiment.experiment_id,
        order_by=["metrics.val_loss ASC"],
        max_results=1
    )
    
    if not runs:
        raise ValueError("No runs found")
    
    return mlflow.pytorch.load_model(f"runs:/{runs[0].info.run_id}/model")

def predict_with_model(model, input_data):
    """
    Load a logged MLflow model and make predictions
    
    Args:
        model: model
        input_data: Input tensor of shape [batch_size, 1, 30, 4] (OHLC for 50 stocks)
    """
    
    # Make prediction
    with torch.no_grad():
        model.eval()
        predictions = model(input_data)
    
    return predictions.numpy()

def unscale_predictions(scaled_predictions, scalers_dir="./scalers"):
    """
    Convert scaled predictions back to original OHLC values
    
    Args:
        scaled_predictions: Tensor of shape [batch_size, num_stocks, 1, 4]
        scalers_dir: Path to directory containing saved scalers
    
    Returns:
        unscaled_predictions: Numpy array in same shape
    """
    # Convert to numpy and remove batch dimension if needed
    if isinstance(scaled_predictions, torch.Tensor):
        scaled_predictions = scaled_predictions.detach().numpy()
    
    batch_size, num_stocks, _, num_features = scaled_predictions.shape
    unscaled = np.zeros_like(scaled_predictions)
    
    for stock_idx in range(num_stocks):
        # Load the scaler for this stock
        scaler = joblib.load(f"{scalers_dir}/scaler_{stock_idx}.pkl")
        
        # Inverse transform each prediction
        for batch_idx in range(batch_size):
            unscaled[batch_idx, stock_idx, 0, :] = scaler.inverse_transform(
                scaled_predictions[batch_idx, stock_idx, 0, :].reshape(1, -1)
            )
    
    return unscaled

# Load model and predict
model = load_latest_model("bidirectional_lstm")

random_input = torch.rand(1, 30, 50, 4)

scaled = predict_with_model(model, random_input)

unscaled = unscale_predictions(scaled)

print(unscaled)