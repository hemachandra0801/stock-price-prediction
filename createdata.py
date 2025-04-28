import yfinance as yf
import pandas as pd
import os

import json


def combine_stock_data(input_folder='stock_data', output_file='combined_stocks_wide.csv'):
    """
    Combine individual stock CSV files into one wide-format CSV.
    
    Args:
        input_folder: Folder containing individual stock CSV files (format: TICKER.csv)
        output_file: Name of the output combined CSV file
    """
    # Get list of all stock files
    stock_files = [f for f in os.listdir(input_folder) if f.endswith('.csv') and not f.startswith('combined')]
    
    if not stock_files:
        print(f"No stock files found in {input_folder}")
        return
    
    combined_df = pd.DataFrame()
    
    for file in stock_files:
        try:
            ticker = file.split('.')[0]  # Extract ticker from filename
            filepath = os.path.join(input_folder, file)
            
            # Read individual stock file
            df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
            
            # Rename columns with ticker prefix
            df = df[['Open', 'High', 'Low', 'Close']].rename(columns={
                'Open': f'{ticker}_open',
                'High': f'{ticker}_high',
                'Low': f'{ticker}_low',
                'Close': f'{ticker}_close'
            })
            
            # Combine with main dataframe
            if combined_df.empty:
                combined_df = df
            else:
                combined_df = combined_df.join(df, how='outer')
            
            print(f"Processed {ticker}")
            
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
    
    # Sort by date and save
    combined_df.sort_index(inplace=True)
    combined_df.to_csv(output_file)
    print(f"\nSuccessfully created combined file: {output_file}")
    print(f"Shape: {combined_df.shape}")
    return combined_df


    
def download_stock_data(tickers, period="1y"):
    """Download historical stock data for given tickers"""
    data = {}
    for ticker in tickers:
        try:
            print(f"Downloading data for {ticker}...")
            stock = yf.Ticker(ticker)
            # Get historical market data
            hist = stock.history(period=period)
            if not hist.empty:
                hist['Ticker'] = ticker  # Add ticker column
                data[ticker] = hist
            else:
                print(f"No data for {ticker}")
        except Exception as e:
            print(f"Error downloading {ticker}: {e}")
    return data

def save_to_csv(data, output_folder='stock_data'):
    """Save stock data to CSV files"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    all_data = []
    
    for ticker, df in data.items():
        filename = f"{output_folder}/{ticker}.csv"
        df.to_csv(filename)
        print(f"Saved {filename}")
        all_data.append(df)
    

        



# Get top 50 tickers
with open('config.json') as f:
    data = json.load(f)

stock_list = data['Stocks']
tickers = stock_list
print(f"Top 50 tickers: {tickers}")

# # Download data (default 1 year history)
# stock_data = download_stock_data(tickers)

# # Save to CSV
# save_to_csv(stock_data)
combined_data = combine_stock_data(
        input_folder='stock_data',
        output_file='combined_stocks_wide.csv'
    )
print("Process completed!")