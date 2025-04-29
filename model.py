import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset, DataLoader, random_split

class StockDataset(Dataset):
    def __init__(self, data, sequence_length=30):
        """
        Args:
            data: Path to CSV or DataFrame
            sequence_length: Length of input sequences
        """
           
        self.seq_len = sequence_length
        self.scalers = {}  # Store scalers per stock
        self.prepare_data()
        
    def prepare_data(self):
        # Get number of stocks (4 features per stock)
        n_features = 4
        n_stocks = self.data.shape[1] // n_features
        
        # Reshape and scale
        data_values = self.data.values
        self.scaled_data = np.zeros((len(self.data), n_stocks, n_features))
        
        for i in range(n_stocks):
            stock_data = data_values[:, i*n_features:(i+1)*n_features]
            self.scalers[i] = MinMaxScaler(feature_range=(-1, 1))
            self.scaled_data[:, i, :] = self.scalers[i].fit_transform(stock_data)
            
    def __len__(self):
        return len(self.data) - self.seq_len
        
    def __getitem__(self, idx):
        x = self.scaled_data[idx:idx+self.seq_len]  # [seq_len, n_stocks, 4]
        y = self.scaled_data[idx+self.seq_len]      # [n_stocks, 4]
        return torch.FloatTensor(x), torch.FloatTensor(y)

def get_dataloaders(data_path, sequence_length=30, batch_size=32, split_ratio=0.8):
    df = pd.read_csv(data_path, index_col='Date', parse_dates=True)
    dataset = StockDataset(df, sequence_length)
    
    # Split dataset
    train_size = int(len(dataset) * split_ratio)
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    return train_loader, val_loader





# 1. Data Preparation
class StockDataset(Dataset):
    def __init__(self, data, sequence_length=30):
        self.data = data
        self.seq_len = sequence_length
        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        self.prepare_data()
        
        
    def prepare_data(self):
        # Reshape data: [n_days, n_stocks*4] -> [n_stocks, n_days, 4]
        n_stocks = 50
        n_features = 4
        data_3d = self.data.values.reshape(-1, n_stocks, n_features)
        
        # Scale each stock's features independently
        self.scaled_data = np.zeros_like(data_3d)
        for i in range(n_stocks):
            self.scaled_data[:, i, :] = self.scaler.fit_transform(data_3d[:, i, :])
        
    def __len__(self):
        return len(self.data) - self.seq_len
        
    def __getitem__(self, idx):
        # Input: [50 stocks, 30 days, 4 features]
        x = self.scaled_data[idx:idx+self.seq_len]
        # Output: [50 stocks, 1 day, 4 features]
        y = self.scaled_data[idx+self.seq_len]
        
        return torch.FloatTensor(x), torch.FloatTensor(y)


class MultiStockLSTM(nn.Module):
    def __init__(self, input_size=4, hidden_size=32, num_stocks=50, 
                 num_layers=1, dropout=0.0, bidirectional=False):
        super().__init__()
        self.num_stocks = num_stocks
        self.hidden_size = hidden_size
        
        # LSTM layer with configurable dropout
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,  # Dropout only between layers
            bidirectional=bidirectional
        )
        
        # Final prediction layer
        self.fc = nn.Linear(hidden_size * (2 if bidirectional else 1), input_size)
        
        # Additional regularization
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        """Input shape: [batch_size, num_stocks, seq_len, num_features]"""
        batch_size, num_stocks, seq_len, num_features = x.shape
        
        outputs = []
        for i in range(self.num_stocks):
            stock_data = x[:, :, i, :]
            lstm_out, _ = self.lstm(stock_data)  # [batch, 30, 32]
            last_out = lstm_out[:, -1]  # [batch, 32]
            pred = self.fc(last_out)  # [batch, 4]
            outputs.append(pred)
            
        # Stack predictions: [batch, 50, 4] -> [batch, 50, 1, 4]
        return torch.stack(outputs, dim=1).unsqueeze(2)

def train_model(model, train_loader, val_loader, config):
    """
    Enhanced training function with validation and early stopping
    
    Args:
        model: Initialized model
        train_loader: Training DataLoader
        val_loader: Validation DataLoader
        config: Dictionary containing training configuration
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=config.get('lr', 0.001),
        weight_decay=config.get('weight_decay', 0)
    )
    
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        patience=config.get('lr_patience', 5),
        factor=config.get('lr_factor', 0.1)
    )
    
    best_val_loss = float('inf')
    early_stop_counter = 0
    early_stop_patience = config.get('early_stop_patience', 10)
    
    history = {
        'train_loss': [],
        'val_loss': []
    }
    
    for epoch in range(config.get('epochs', 100)):
        # Training phase
        model.train()
        train_loss = 0.0
        
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            
            optimizer.zero_grad()
            outputs = model(x)
            loss = criterion(outputs, y.unsqueeze(2))
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * x.size(0)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                outputs = model(x)
                print(outputs.shape)
                loss = criterion(outputs, y.unsqueeze(2))
                val_loss += loss.item() * x.size(0)
        
        # Calculate epoch metrics
        train_loss = train_loss / len(train_loader.dataset)
        val_loss = val_loss / len(val_loader.dataset)
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        
        # Update learning rate
        scheduler.step(val_loss)
        
        # Print progress
        print(f'Epoch {epoch+1}/{config["epochs"]}')
        print(f'Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}')
        print(f'LR: {optimizer.param_groups[0]["lr"]:.6f}')
        print('-' * 50)
        
        # Early stopping and model checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), config['model_path'])
            early_stop_counter = 0
            print(f'Validation loss improved. Model saved to {config["model_path"]}')
        else:
            early_stop_counter += 1
            if early_stop_counter >= early_stop_patience:
                print(f'Early stopping after {early_stop_patience} epochs without improvement')
                break
    
    # Load best model weights
    model.load_state_dict(torch.load(config['model_path']))
    
    return model, history

# if __name__ == "__main__":
#     # Configurations
#     model_config = {
#         'input_size': 4,
#         'hidden_size': 64,
#         'num_layers': 2,
#         'dropout': 0.3,
#         'bidirectional': True,
#         'num_stocks': 50  # Should match your data
#     }
    
#     training_config = {
#         'sequence_length': 30,
#         'batch_size': 64,
#         'epochs': 50,
#         'lr': 0.001,
#         'weight_decay': 1e-4,
#         'model_path': 'models/best_lstm.pth'
#     }
    
#     # Get data loaders
#     train_loader, val_loader = get_dataloaders(
#         "combined_stocks_wide.csv",
#         sequence_length=training_config['sequence_length'],
#         batch_size=training_config['batch_size']
#     )
    
#     # Initialize and train model
#     model = MultiStockLSTM(**model_config)
#     model, history = train_model(model, train_loader, val_loader, training_config)