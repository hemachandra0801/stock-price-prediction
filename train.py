import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset, DataLoader

# 1. Data Preparation
class StockDataset(Dataset):
    def __init__(self, data, sequence_length=30):
        self.data = data
        self.seq_len = sequence_length
        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        self.prepare_data()
        
        # Print dataset summary
        print("\nDataset Shapes:")
        print(f"Original DataFrame: {data.shape}")  # (n_days, n_stocks*4)
        print(f"3D Reshaped Data: {self.scaled_data.shape}")  # (n_days, n_stocks, 4)
        print(f"Total Samples (Sequences): {len(self)}")  # n_days - sequence_length
        
        # Print example input/target shapes
        sample_x, sample_y = self[0]
        print(f"\nSample Input Shape: {sample_x.shape}")  # (50, 30, 4)
        print(f"Sample Target Shape: {sample_y.shape}")    # (50, 4)
        
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

# 2. LSTM Model
class MultiStockLSTM(nn.Module):
    def __init__(self, input_size=4, hidden_size=32, num_stocks=50):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_size, input_size)
        self.num_stocks = num_stocks
        
    def forward(self, x):
        # x shape: [batch, 50, 30, 4]
            
        # Process each stock independently
        outputs = []
        for i in range(self.num_stocks):
            stock_data = x[:, :, i, :]
            lstm_out, _ = self.lstm(stock_data)  # [batch, 30, 32]
            last_out = lstm_out[:, -1]  # [batch, 32]
            pred = self.fc(last_out)  # [batch, 4]
            outputs.append(pred)
            
        # Stack predictions: [batch, 50, 4] -> [batch, 50, 1, 4]
        return torch.stack(outputs, dim=1).unsqueeze(2)

# 3. Training Setup
def train_model(data_path, epochs=100, batch_size=32):
    # Load and prepare data
    df = pd.read_csv(data_path, index_col='Date', parse_dates=True)
    dataset = StockDataset(df)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize model
    model = MultiStockLSTM()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    for epoch in range(epochs):
        total_loss = 0
        for x, y in dataloader:
            optimizer.zero_grad()
            outputs = model(x)
            loss = criterion(outputs, y.unsqueeze(2))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        print(f'Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.6f}')
    
    return model

# 4. Main Execution
if __name__ == "__main__":
    # Train the model
    model = train_model("combined_stocks_wide.csv", epochs=5)
    
    # Save the model
    torch.save(model.state_dict(), "models/basic_lstm_1y.pth")
    print("Model saved to multi_stock_lstm.pth")