import mlflow
import mlflow.pytorch
from datetime import datetime
from model import MultiStockLSTM, train_model
from loader import get_dataloaders
import pandas as pd
import mlflow
from mlflow.models.signature import infer_signature
import torch

def run_experiment(experiment_name, model_config, training_config):
    # Set up MLflow
    mlflow.set_experiment(experiment_name)
    
    # Determine device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    with mlflow.start_run():
        # Log parameters including device info
        mlflow.log_params({
            **model_config,
            **training_config,
            "device": str(device)
        })
        
        # Get data loaders
        train_loader, val_loader = get_dataloaders()
        
        # Initialize model and move to device
        model = MultiStockLSTM(**model_config).to(device)
        
        # Train model (ensure train_model handles device properly)
        model, history = train_model(model, train_loader, val_loader, training_config)
        
        # Create input example (handle device properly)
        sample_input, _ = next(iter(train_loader))
        input_example = sample_input[:1].to(device)  # Move to model's device
        
        # Infer model signature (move model to CPU for compatibility)
        model.eval()
        with torch.no_grad():
            # Temporarily move to CPU for signature inference
            cpu_model = model.cpu()
            cpu_input = input_example.cpu()
            sample_output = cpu_model(cpu_input)
            
            signature = infer_signature(
                cpu_input.numpy(),
                sample_output.numpy()
            )
            
            # Move model back to original device
            model = cpu_model.to(device)
        
        # Log model (MLflow handles device conversion)
        mlflow.pytorch.log_model(
            pytorch_model=model.cpu(),  # MLflow expects CPU models
            artifact_path="model",
            conda_env=None,
            code_paths=[__file__],
            signature=signature,
            input_example=cpu_input.numpy(),  # Use CPU-converted example
            registered_model_name=f"{experiment_name}_stock_lstm"
        )
        
        # Log metrics
        mlflow.log_metric("best_val_loss", min(history['val_loss']))
        
        # Log training curves
        for epoch, (train_loss, val_loss) in enumerate(zip(history['train_loss'], history['val_loss'])):
            mlflow.log_metrics({
                "train_loss": train_loss,
                "val_loss": val_loss
            }, step=epoch)


# Experiment 1: Baseline LSTM
run_experiment(
    "baseline_lstm",
    model_config={
        'input_size': 4,
        'hidden_size': 32,
        'num_layers': 1,
        'dropout': 0.0,
        'bidirectional': False,
        'num_stocks': 50
    },
    training_config={
        'sequence_length': 30,
        'batch_size': 64,
        'epochs': 5,
        'lr': 0.001,
        'weight_decay': 1e-4,
        'model_path': 'models/baseline_lstm.pth'
    }
)

# Experiment 2: Deeper LSTM with Dropout
run_experiment(
    "deep_lstm",
    model_config={
        'input_size': 4,
        'hidden_size': 64,
        'num_layers': 2,
        'dropout': 0.3,
        'bidirectional': False,
        'num_stocks': 50
    },
    training_config={
        'sequence_length': 30,
        'batch_size': 64,
        'epochs': 5,
        'lr': 0.001,
        'weight_decay': 1e-4,
        'model_path': 'models/deep_lstm.pth'
    }
)

# Experiment 3: Bidirectional LSTM
run_experiment(
    "bidirectional_lstm",
    model_config={
        'input_size': 4,
        'hidden_size': 64,
        'num_layers': 2,
        'dropout': 0.3,
        'bidirectional': True,
        'num_stocks': 50
    },
    training_config={
        'sequence_length': 30,
        'batch_size': 64,
        'epochs': 50,
        'lr': 0.001,
        'weight_decay': 1e-4,
        'model_path': 'models/bidirectional_lstm.pth'
    }
)