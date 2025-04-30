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

