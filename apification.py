import torch
from pathlib import Path
import asyncio
import asyncpg
from dotenv import load_dotenv
import os
from fastapi import FastAPI, HTTPException
import mlflow.pytorch
from pydantic import BaseModel
from typing import Dict, List
import subprocess

app = FastAPI()
load_dotenv()

class PredictionResponse(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float

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

async def get_stock_id(symbol: str) -> int:
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

async def get_predictions(symbol: str):
    """Get predictions for a specific stock symbol"""
    file_path = Path("/home/hiran/Desktop/mlops/project/stock-price-prediction/data/processed/predictions.pt")
    
    stock_id = await get_stock_id(symbol)
    if stock_id is None:
        raise HTTPException(status_code=404, detail=f"Stock symbol {symbol} not found")
    
    try:
        data = torch.load(file_path, map_location=torch.device('cpu'), weights_only=False)
        prediction = data[0, stock_id, 0, :]  # [batch, stock, time_step, features]
        
        return PredictionResponse(
            symbol=symbol,
            open=float(prediction[0]),
            high=float(prediction[1]),
            low=float(prediction[2]),
            close=float(prediction[3])
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Predictions file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/predict/{symbol}", response_model=PredictionResponse)
async def predict(symbol: str):
    """
    Get predictions for a specific stock symbol.
    
    Parameters:
    - symbol: Stock ticker symbol (e.g., AMZN, AAPL)
    
    Returns:
    - OHLC predictions for the next time period
    """
    # Run DVC pipeline to update predictions
    if not run_dvc_repro():
        raise HTTPException(status_code=500, detail="Failed to update predictions")
    
    # Get and return predictions
    return await get_predictions(symbol)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)