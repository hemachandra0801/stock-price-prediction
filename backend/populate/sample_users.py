import asyncpg
import bcrypt
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def create_dummy_data():
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create dummy users
        users = [
            {
                "email": "abcd@gmail.com",
                "password": "password",
                "portfolio": [{"symbol": "MSFT", "quantity": 100},
                    {"symbol": "TSLA", "quantity": 20},
                    {"symbol": "AMZN", "quantity": 15}
                ]
            },
            {
                "email": "user2@test.com",
                "password": "SecurePass456!",
                "portfolio": [
                    {"symbol": "AAPL", "quantity": 50},
                    {"symbol": "GOOGL", "quantity": 10}
                ]
            },
            {
                "email": "trader@test.com", 
                "password": "StockMaster789!",
                "portfolio": [
                    {"symbol": "MSFT", "quantity": 100},
                    {"symbol": "TSLA", "quantity": 20},
                    {"symbol": "AMZN", "quantity": 15}
                ]
            }
        ]

        # Insert users
        for user in users:
            hashed_pw = bcrypt.hashpw(user['password'].encode(), bcrypt.gensalt())
            await conn.execute('''
                INSERT INTO users (email, hashed_password, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (email) DO NOTHING
            ''', user['email'], hashed_pw.decode(), datetime.now())

        stock_records = await conn.fetch("""
                SELECT s.stock_id, s.symbol, h.close 
                FROM stocks s
                JOIN (
                    SELECT stock_id, close,
                    ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY date DESC) AS rn
                    FROM stock_historical_data
                ) h ON s.stock_id = h.stock_id AND h.rn = 1
            """)
        stock_map = {rec['symbol']: (rec['stock_id'], rec['close']) for rec in stock_records}

        # Insert portfolios with realistic prices
        for user in users:
            user_id = await conn.fetchval(
                "SELECT user_id FROM users WHERE email = $1",
                user['email']
            )
            
            portfolio = []
            for item in user['portfolio']:
                stock_data = stock_map.get(item['symbol'])
                if stock_data:
                    stock_id, current_price = stock_data
                    # Generate realistic purchase price (±5% of current price)
                    avg_price = round(float(current_price) * random.uniform(0.95, 1.05), 2)
                    
                    portfolio.append((
                        user_id,
                        stock_id,
                        item['quantity'],
                        avg_price,
                        datetime.now() - timedelta(days=random.randint(1, 365))
                    ))
            
            if portfolio:
                await conn.executemany('''
                    INSERT INTO portfolios 
                    (user_id, stock_id, quantity, avg_purchase_price, last_updated)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id, stock_id) DO UPDATE
                    SET quantity = EXCLUDED.quantity,
                        avg_purchase_price = EXCLUDED.avg_purchase_price
                ''', portfolio)

        print("Successfully populated dummy data!")

    finally:
        await conn.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(create_dummy_data())