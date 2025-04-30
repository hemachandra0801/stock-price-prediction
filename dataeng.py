import torch 
import numpy as np
import joblib


def scale_input(input_data, scalers_dir="./scalers"):
    """
    Scale input data using pre-fitted stock scalers
    
    Args:
        input_data: Tensor of shape [batch_size, seq_len, num_stocks, num_features]
                   (typically [1, 30, 50, 4] for prediction)
        scalers_dir: Path to directory containing saved scalers
    
    Returns:
        scaled_input: Tensor in same shape as input
    """
    # Convert to numpy if it's a tensor
    if isinstance(input_data, torch.Tensor):
        input_data = input_data.numpy()
    
    batch_size, seq_len, num_stocks, num_features = input_data.shape
    scaled_data = np.zeros_like(input_data)
    
    for stock_idx in range(num_stocks):
        # Load the scaler for this stock
        scaler = joblib.load(f"{scalers_dir}/scaler_{stock_idx}.pkl")
        
        # Reshape to [batch*seq_len, features] for scaling
        stock_data = input_data[:, :, stock_idx, :].reshape(-1, num_features)
        scaled_stock_data = scaler.transform(stock_data)
        
        # Reshape back to original structure
        scaled_data[:, :, stock_idx, :] = scaled_stock_data.reshape(batch_size, seq_len, num_features)
    
    return torch.FloatTensor(scaled_data)

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
