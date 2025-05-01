import csv
import asyncpg
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def populate_stocks_and_history(csv_path):
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Step 1: Create stock master list
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Read header row
            
            # Extract unique stock symbols (BMY, ABT, CRM, etc.)
            symbols = list({col.split('_')[0] for col in headers if '_open' in col})
            
            # Insert into stocks table
            await conn.execute('''
                INSERT INTO stocks (symbol, company_name)
                SELECT symbol, 'Placeholder Company Name'
                FROM unnest($1::text[]) symbol
                ON CONFLICT (symbol) DO NOTHING
            ''', symbols)
            
            # Get stock_id mapping
            stock_map = {row['symbol']: row['stock_id']
                        for row in await conn.fetch('SELECT stock_id, symbol FROM stocks')}

        # Step 2: Process historical data
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            
            batch = []
            batch_size = 1000  # Adjust based on memory constraints
            
            for row in reader:
                date_str = row['Date'].split(' ')[0]
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                for symbol in symbols:
                    try:
                        stock_id = stock_map[symbol]
                        batch.append((
                            stock_id,
                            date,
                            float(row[f'{symbol}_open']),
                            float(row[f'{symbol}_high']),
                            float(row[f'{symbol}_low']),
                            float(row[f'{symbol}_close'])
                        ))
                        
                        # Insert in batches
                        if len(batch) >= batch_size:
                            await conn.executemany('''
                                INSERT INTO stock_historical_data 
                                (stock_id, date, open, high, low, close)
                                VALUES ($1, $2, $3, $4, $5, $6)
                                ON CONFLICT (stock_id, date) DO NOTHING
                            ''', batch)
                            batch = []
                            
                    except KeyError:
                        print(f"Missing data for {symbol} on {date}")
                        continue
                    except ValueError:
                        print(f"Invalid data format for {symbol} on {date}")
                        continue

            # Insert remaining records
            if batch:
                await conn.executemany('''
                    INSERT INTO stock_historical_data 
                    (stock_id, date, open, high, low, close)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (stock_id, date) DO NOTHING
                ''', batch)

    finally:
        await conn.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(populate_stocks_and_history('combined_stocks_wide.csv'))