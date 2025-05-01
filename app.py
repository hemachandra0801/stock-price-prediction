import torch
from pathlib import Path
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()
import subprocess
from pathlib import Path

def run_dvc_repro():
    """Execute dvc repro command in the project root"""
    project_root = Path("/home/hiran/Desktop/mlops/project/stock-price-prediction")
    try:
        result = subprocess.run(
            ["dvc", "repro"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        print("DVC repro completed successfully")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("DVC repro failed:")
        print(e.stderr)
        return False


async def get_stock_id(symbol):
    """Fetch stock_id for a given stock symbol"""
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        query = """
        SELECT stock_id 
        FROM stocks 
        WHERE symbol = $1
        LIMIT 1
        """
        result = await conn.fetchval(query, symbol)
        return result
    finally:
        await conn.close()

async def main(stock_symbol):
    file_path = Path("/home/hiran/Desktop/mlops/project/stock-price-prediction/data/processed/predictions.pt")
    
    
    # Get stock ID
    stock_id = await get_stock_id(stock_symbol)
    print(f"{stock_symbol}: {stock_id}")
    
    if stock_id is None:
        print(f"Stock symbol {stock_symbol} not found in database")
        return
    
    # Load predictions
    try:
        # Allow full object loading (safe only if you trust the file)
        data = torch.load(file_path, weights_only=False)
        prediction = data[0, stock_id, 0, :]
        # Print prediction data for this stock (first time step)
        print("Prediction data (first time step):")
        print(data[0, stock_id, 0, :])  # [batch, stock, time_step, features]
        return {
                "symbol": stock_symbol,
                "open": float(prediction[0]),
                "high": float(prediction[1]),
                "low": float(prediction[2]),
                "close": float(prediction[3])
        }
    except FileNotFoundError:
        print(f"Predictions file not found at {file_path}")
    except Exception as e:
        print(f"Error loading predictions: {str(e)}")

if __name__ == "__main__":
    # Run DVC pipeline
    success = run_dvc_repro()
    if success:
        print("Proceeding with predictions...")
        # Your prediction code here
    else:
        print("Failed to run DVC pipeline")
    print(asyncio.run(main(stock_symbol = 'AMZN')))