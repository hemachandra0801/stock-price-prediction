import os
import asyncio
import asyncpg
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.preprocessing import MinMaxScaler
import joblib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class StockDataset(Dataset):
    def __init__(self, sequence_length=30, scalers_dir="scalers"):
        """
        Args:
            sequence_length: Length of input sequences
            scalers_dir: Directory to save/load scalers
        """
        self.seq_len = sequence_length
        self.scalers_dir = scalers_dir
        self.scalers = {}
        
        # Load data from database (synchronously)
        self.data = self._load_from_db_sync()
        self._prepare_data()

    def _load_from_db_sync(self):
        """Synchronous wrapper around async function"""
        return asyncio.get_event_loop().run_until_complete(self._load_from_db_async())

    async def _load_from_db_async(self):
        """Actual async database query"""
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            query = """
            SELECT 
                s.symbol,
                h.date,
                h.open,
                h.high,
                h.low,
                h.close
            FROM stock_historical_data h
            JOIN stocks s ON h.stock_id = s.stock_id
            ORDER BY h.date, s.symbol
            """
            
            records = await conn.fetch(query)
            
            # Convert to DataFrame
            df = pd.DataFrame(records, columns=['symbol', 'date', 'open', 'high', 
                                             'low', 'close'])
            
            # Pivot to wide format
            df = df.pivot(index='date', columns='symbol', 
                         values=['open', 'high', 'low', 'close'])
            df.columns = [f"{col[1]}_{col[0]}" for col in df.columns]
            return df.sort_index()
        finally:
            await conn.close()

    def _prepare_data(self):
        """Normalize the data"""
        n_features = 4  # open, high, low, close
        n_stocks = len(self.data.columns) // n_features
        data_values = self.data.values
        
        self.scaled_data = np.zeros((len(self.data), n_stocks, n_features))
        
        # Load or create scalers
        if self.scalers_dir and os.path.exists(self.scalers_dir):
            for i in range(n_stocks):
                scaler_path = os.path.join(self.scalers_dir, f'scaler_{i}.pkl')
                if os.path.exists(scaler_path):
                    self.scalers[i] = joblib.load(scaler_path)
        
        for i in range(n_stocks):
            stock_data = data_values[:, i*n_features:(i+1)*n_features]
            if i not in self.scalers:
                self.scalers[i] = MinMaxScaler(feature_range=(-1, 1))
                self.scalers[i].fit(stock_data)
            self.scaled_data[:, i, :] = self.scalers[i].transform(stock_data)
        
        if self.scalers_dir:
            os.makedirs(self.scalers_dir, exist_ok=True)
            for i, scaler in self.scalers.items():
                joblib.dump(scaler, os.path.join(self.scalers_dir, f'scaler_{i}.pkl'))

    def __len__(self):
        return len(self.data) - self.seq_len
        
    def __getitem__(self, idx):
        x = self.scaled_data[idx:idx+self.seq_len]
        y = self.scaled_data[idx+self.seq_len]
        return torch.FloatTensor(x), torch.FloatTensor(y)

def get_dataloaders(sequence_length=30, batch_size=32, split_ratio=0.8):
    """Synchronous function to get dataloaders"""
    dataset = StockDataset(sequence_length)
    
    # Split dataset
    train_size = int(len(dataset) * split_ratio)
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    return train_loader, val_loader

# Example usage
if __name__ == "__main__":
    # Initialize dataset and get dataloaders
    train_loader, val_loader = get_dataloaders()
    
    # Print dimensions
    print(f"Number of training batches: {len(train_loader)}")
    
    # Get first batch
    first_batch_x, first_batch_y = next(iter(train_loader))
    
    # Print batch dimensions
    print(f"\nTraining batch dimensions:")
    print(f"Input shape (x): {first_batch_x.shape}")  # [batch_size, seq_len, n_stocks, n_features]
    print(f"Target shape (y): {first_batch_y.shape}")  # [batch_size, n_stocks, n_features]
    
    # Print sample data (first sequence of first batch)
    print("\nSample input sequence (first sequence of first batch):")
    print(first_batch_x[0])  # Shape: [seq_len, n_stocks, n_features]
    
    print("\nCorresponding target:")
    print(first_batch_y[0])  # Shape: [n_stocks, n_features]