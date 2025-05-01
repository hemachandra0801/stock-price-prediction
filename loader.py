import os
import asyncio
import asyncpg
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, Subset
from sklearn.preprocessing import MinMaxScaler
import joblib
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class StockDataset(Dataset):
    def __init__(self, sequence_length=30, scalers_dir="scalers"):
        self.seq_len = sequence_length
        self.scalers_dir = scalers_dir
        self.scalers = {}
        self.data = self._load_from_db_sync()
        self._prepare_data()
        
    def _load_from_db_sync(self):
        return asyncio.get_event_loop().run_until_complete(self._load_from_db_async())

    async def _load_from_db_async(self):
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            query = """
            WITH stock_order AS (
                SELECT stock_id FROM stocks ORDER BY stock_id LIMIT 50
            )
            SELECT 
                h.date,
                s.stock_id,
                h.open,
                h.high,
                h.low,
                h.close
            FROM stock_historical_data h
            JOIN stocks s ON h.stock_id = s.stock_id
            JOIN stock_order so ON s.stock_id = so.stock_id
            ORDER BY h.date, s.stock_id
            """
            
            records = await conn.fetch(query)
            
            # Create DataFrame and pivot
            df = pd.DataFrame(records, columns=['date', 'stock_id', 'open', 'high', 'low', 'close'])
            df = df.pivot(index='date', columns='stock_id', values=['open', 'high', 'low', 'close'])
            df.columns = [f"{col[1]}_{col[0]}" for col in df.columns]
            
            return df.sort_index()
        finally:
            await conn.close()

    def _prepare_data(self):
        n_features = 4  # open, high, low, close
        n_stocks = len(self.data.columns) // n_features
        data_values = self.data.values
        
        self.scaled_data = np.zeros((len(self.data), n_stocks, n_features))
        
        # Create and save scalers
        for i in range(n_stocks):
            stock_data = data_values[:, i*n_features:(i+1)*n_features]
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
    dataset = StockDataset(sequence_length)
    
    # Sequential split
    indices = torch.arange(len(dataset))
    split_idx = int(len(indices) * split_ratio)
    
    train_dataset = Subset(dataset, indices[:split_idx])
    val_dataset = Subset(dataset, indices[split_idx:])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader

if __name__ == "__main__":
    train_loader, val_loader = get_dataloaders()
    
    # Print info
    print(f"Training batches: {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    
    # Example batch
    x, y = next(iter(train_loader))
    print(f"Batch shape - x: {x.shape}, y: {y.shape}")