import os
import asyncio
import asyncpg
import pandas as pd
import torch
from torch.utils.data import Dataset
import numpy as np
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class StockDataset(Dataset):
    def __init__(self):
        self.data = self._load_from_db_sync()
        
    def _load_from_db_sync(self):
        """Synchronous wrapper around async function"""
        return asyncio.get_event_loop().run_until_complete(self._load_from_db_async())

    async def _load_from_db_async(self):
        """Fetch last 30 days data with proper chronological ordering"""
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            query = """
            WITH date_range AS (
                SELECT DISTINCT date 
                FROM stock_historical_data 
                ORDER BY date DESC 
                LIMIT 30
            ),
            stock_order AS (
                SELECT stock_id FROM stocks ORDER BY stock_id LIMIT 50
            )
            SELECT 
                dr.date,
                s.stock_id,
                h.open,
                h.high,
                h.low,
                h.close
            FROM date_range dr
            JOIN stock_historical_data h ON h.date = dr.date
            JOIN stocks s ON h.stock_id = s.stock_id
            JOIN stock_order so ON s.stock_id = so.stock_id
            ORDER BY dr.date DESC, s.stock_id  -- Newest dates first in query results
            """
            
            records = await conn.fetch(query)
            
            # Get unique dates (newest first) and stock_ids (ascending)
            unique_dates = sorted({r['date'] for r in records}, reverse=True)  # Newest first for printout
            unique_stock_ids = sorted({r['stock_id'] for r in records})
            
            print("Fetched dates (newest to oldest):")
            for i, date in enumerate(unique_dates):
                print(f"{i+1}. {date}")
            
            # Initialize array (we'll fill it in reverse date order)
            arr = np.empty((len(unique_dates), len(unique_stock_ids), 4), dtype='float32')
            
            # Fill array in chronological order (oldest first in tensor)
            date_order = sorted(unique_dates)  # Oldest first for tensor
            for r in records:
                # Reverse the date index for chronological order
                date_idx = len(unique_dates) - 1 - unique_dates.index(r['date'])
                stock_idx = unique_stock_ids.index(r['stock_id'])
                arr[date_idx, stock_idx] = [
                    r['open'],
                    r['high'],
                    r['low'],
                    r['close']
                ]
            
            # Verify data
            if np.isnan(arr).any():
                raise ValueError("Missing data points in the tensor")
            
            return torch.from_numpy(arr).unsqueeze(0)  # [1, 30, 50, 4]
            
        finally:
            await conn.close()
      

    def __len__(self):
        return 1  # Only one sequence

    def __getitem__(self, idx):
        return self.data  # Always return the full tensor


def fetch() :
    dataset = StockDataset()
    return dataset[0]

# Usage example
if __name__ == "__main__":
    dataset = StockDataset()
    stock_id = 0
    print(dataset[0][0, 29, stock_id, :])
    # tensor_data = dataset[0]  # Get the tensor
    # print(f"Data shape: {tensor_data.shape}")
    # print(f"Sample data:\n{tensor_data[0, 0, 0]}")  # First day, first stock