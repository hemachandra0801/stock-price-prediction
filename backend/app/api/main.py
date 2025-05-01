# main.py
from fastapi import FastAPI, Depends, Form, HTTPException, logger, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, List
import asyncpg
import os
from dotenv import load_dotenv
from fastapi import Request
import httpx

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = os.getenv("DATABASE_URL")

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# FastAPI setup
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
async def options_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return JSONResponse(
            content={"message": "OK"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-CSRF-Token",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.options("/auth/{path:path}")
async def options_handler():
    return JSONResponse(status_code=200)

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection pool
pool = None

async def get_db():
    global pool
    if not pool:
        pool = await asyncpg.create_pool(
            DATABASE_URL, 
            min_size=1,
            max_size=10,
            command_timeout=60
        )
    return pool

# Models
class UserCreate(BaseModel):
    email: str
    password: str

class UserInDB(BaseModel):
    user_id: int
    email: str
    hashed_password: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PortfolioItem(BaseModel):
    symbol: str
    name: str
    quantity: int
    avg_price: float
    current_price: float
    value: float
    profit: float
    profit_percent: float

class TransactionCreate(BaseModel):
    symbol: str
    action: str  # 'buy' or 'sell'
    quantity: int
    price: float

class PredictionResult(BaseModel):
    date: str
    predicted_close: float

class StockHolding(BaseModel):
    symbol: str
    name: str
    quantity: int
    avg_price: float
    current_price: float
    value: float
    profit_percent: float

    class Config:
        from_attributes = True

class PredictionResponse(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float


# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from jose.exceptions import JWTError

def verify_csrf_token(token: str, request: Request) -> bool:
    try:
        logger.debug(f"Verifying CSRF token: {token}")
        logger.debug(f"Cookies: {request.cookies}")

        # Verify the token matches the cookie
        cookie_token = request.cookies.get("csrf_token")
        if not cookie_token:
            logger.error("CSRF cookie missing")
            return False
        
        if token != cookie_token:
            logger.error(f"Token mismatch\nHeader: {token}\nCookie: {cookie_token}")
            return False
            
        decoded_cookie = jwt.decode(cookie_token, SECRET_KEY, algorithms=[ALGORITHM])
        decoded_header = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        return decoded_cookie["csrf"] == decoded_header["csrf"]
    except JWTError as e:
        logger.error(f"CSRF validation failed: {str(e)}")
        return False
    
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

async def get_user(email: str):
    db = await get_db()
    user = await db.fetchrow(
        "SELECT user_id, email, hashed_password, created_at, last_login, is_active FROM users WHERE email = $1",
        email
    )
    if user:
        return UserInDB(
            user_id=user['user_id'],
            email=user['email'],
            hashed_password=user['hashed_password'],
            created_at=user['created_at'],
            last_login=user['last_login'],
            is_active=user['is_active']
        )
    return None

async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Routes
@app.get("/")
async def root():
    return {
        "message": "Stock Prediction API", 
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "login": "/auth/login",
            "register": "/auth/register"
        }
    }

@app.get("/health")
async def health_check(db=Depends(get_db)):
    try:
        await db.execute("SELECT 1")
        return {"database": "connected"}
    except Exception as e:
        return {"database": "disconnected", "error": str(e)}

@app.post("/auth/register")
async def register(email: str = Form(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"),
    password: str = Form(..., min_length=8),
    db: asyncpg.Pool = Depends(get_db)):
    try:
        db = await get_db()
        
        # Check if user exists
        existing_user = await db.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            email
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(password)
        new_user = await db.fetchrow(
            """INSERT INTO users (email, hashed_password) 
            VALUES ($1, $2) RETURNING *""",
            email, hashed_password
        )
        
        return {"message": "User created successfully", "user_id": new_user["user_id"], "email": new_user["email"]}
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.post("/auth/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.debug(f"Login attempt for: {form_data.username}")
        
        # Verify CSRF token first
        csrf_token = request.headers.get("X-CSRF-Token")
        logger.debug(f"CSRF Header: {csrf_token}")
        if not csrf_token or not verify_csrf_token(csrf_token, request):
            logger.error("CSRF validation failed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )

        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.error(f"Invalid credentials for: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user.email,
            "user_id": user.user_id
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/logout")
async def logout():
    # In a real implementation, you would add the token to a blacklist
    return {"message": "Successfully logged out"}

@app.get("/auth/csrf-token")
async def get_csrf_token(request: Request, response: Response):
    csrf_token = jwt.encode({"csrf": "secure_token"}, SECRET_KEY, algorithm=ALGORITHM)
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=True, samesite="lax", secure=False, max_age=1800)
    return {"csrf_token": csrf_token}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user(email)
    if user is None:
        raise credentials_exception
    return user

@app.get("/portfolio", response_model=List[PortfolioItem])
async def get_portfolio(current_user: UserInDB = Depends(get_current_user)):
    try:
        db = await get_db()

        # holdings = await db.fetch('''
        #     SELECT 
        #         s.symbol,
        #         s.company_name AS name,
        #         COALESCE(p.quantity, 0) AS quantity,
        #         COALESCE(p.avg_purchase_price, 0) AS avg_price,
        #         h.close AS current_price,
        #         COALESCE(p.quantity, 0) * h.close AS value,
        #         COALESCE(p.quantity, 0) * h.close - COALESCE(p.quantity, 0) * COALESCE(p.avg_purchase_price, 0) AS profit,
        #         CASE 
        #             WHEN COALESCE(p.avg_purchase_price, 0) = 0 THEN 0
        #             ELSE ((h.close - p.avg_purchase_price) / p.avg_purchase_price * 100)
        #         END AS profit_percent
        #     FROM stocks s
        #     LEFT JOIN portfolios p ON p.stock_id = s.stock_id AND p.user_id = $1
        #     LEFT JOIN (
        #         SELECT DISTINCT ON (stock_id) stock_id, close
        #         FROM stock_historical_data
        #         ORDER BY stock_id, date DESC
        #     ) h ON s.stock_id = h.stock_id
        #     WHERE s.is_active = TRUE
        # ''', current_user.user_id)

        holdings = await db.fetch('''
            SELECT 
                s.symbol,
                s.company_name AS name,
                p.quantity AS quantity,
                p.avg_purchase_price AS avg_price,
                h.close AS current_price,
                ROUND(p.quantity * h.close, 2) AS value,
                ROUND((h.close - p.avg_purchase_price) * p.quantity, 2) AS profit,
                CASE 
                    WHEN p.avg_purchase_price = 0 THEN 0
                    ELSE ROUND(((h.close - p.avg_purchase_price) / p.avg_purchase_price * 100), 2)
                END AS profit_percent
            FROM portfolios p
            INNER JOIN stocks s ON p.stock_id = s.stock_id
            LEFT JOIN LATERAL (
                SELECT close
                FROM stock_historical_data
                WHERE stock_id = s.stock_id
                ORDER BY date DESC
                LIMIT 1
            ) h ON true
            WHERE 
                p.user_id = $1
                AND s.is_active = TRUE
                AND p.quantity > 0
        ''', current_user.user_id)
        
        result = [PortfolioItem(**dict(record)) for record in holdings]
        return result
        
    except Exception as e:
        logger.error(f"Portfolio error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching portfolio")

@app.post("/portfolio/transactions", response_model=StockHolding)
async def add_transaction(
    transaction: TransactionCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        db = await get_db()
        
        async with db.transaction():
            # Get stock ID
            stock = await db.fetchrow(
                "SELECT stock_id FROM stocks WHERE symbol = $1",
                transaction.symbol
            )
            if not stock:
                raise HTTPException(status_code=404, detail="Stock not found")
            
            # Update portfolio
            if transaction.action == 'buy':
                await db.execute('''
                    INSERT INTO portfolios (user_id, stock_id, quantity, avg_purchase_price)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, stock_id) DO UPDATE SET
                        quantity = portfolios.quantity + $3,
                        avg_purchase_price = (portfolios.avg_purchase_price * portfolios.quantity + $4 * $3) / 
                                            (portfolios.quantity + $3)
                ''', current_user.user_id, stock['stock_id'], transaction.quantity, transaction.price)
            elif transaction.action == 'sell':
                # Check existing holdings
                holding = await db.fetchrow(
                    "SELECT quantity FROM portfolios WHERE user_id = $1 AND stock_id = $2",
                    current_user.user_id, stock['stock_id']
                )
                if not holding or holding['quantity'] < transaction.quantity:
                    raise HTTPException(status_code=400, detail="Insufficient shares")
                
                await db.execute('''
                    UPDATE portfolios
                    SET quantity = quantity - $1
                    WHERE user_id = $2 AND stock_id = $3
                ''', transaction.quantity, current_user.user_id, stock['stock_id'])
            else:
                raise HTTPException(status_code=400, detail="Invalid action")
            
            # Get updated holding with current price
            updated_holding = await db.fetchrow('''
                SELECT 
                    s.symbol,
                    s.company_name as name,
                    p.quantity,
                    p.avg_purchase_price as avg_price,
                    h.close as current_price,
                    (p.quantity * h.close) as value,
                    ((h.close - p.avg_purchase_price) / p.avg_purchase_price * 100) as profit_percent
                FROM portfolios p
                JOIN stocks s ON p.stock_id = s.stock_id
                JOIN (
                    SELECT DISTINCT ON (stock_id) *
                    FROM stock_historical_data
                    ORDER BY stock_id, date DESC
                ) h ON s.stock_id = h.stock_id
                WHERE p.user_id = $1 AND s.stock_id = $2
            ''', current_user.user_id, stock['stock_id'])
            
            # Record transaction
            await db.execute('''
                INSERT INTO transactions 
                (user_id, stock_id, type, quantity, price)
                VALUES ($1, $2, $3, $4, $5)
            ''', current_user.user_id, stock['stock_id'], transaction.action, 
                            transaction.quantity, transaction.price)
            
            if not updated_holding:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated holding")

            return StockHolding(**updated_holding)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Transaction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Transaction failed")

@app.get("/portfolio/predictions/{symbol}", response_model=PredictionResponse)
async def get_predictions(
    symbol: str,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        # Replace with actual prediction logic
        prediction = None
        # return {
        #     "symbol": symbol,    
        #     "open": prediction.open,
        #     "high": prediction.high,
        #     "low": prediction.low,
        #     "close": prediction.close
        # }
        try:
            external_url = f"http://10.22.14.38:8000/predict/{symbol}"
            async with httpx.AsyncClient() as client:
                response = await client.get(external_url)

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch prediction")

            data = response.json()
            return {
                "symbol": data["symbol"],
                "open": data["open"],
                "high": data["high"],
                "low": data["low"],
                "close": data["close"]
            }
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise HTTPException(status_code=500, detail="Prediction failed")
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Prediction failed")

@app.get("/auth/status")
async def auth_status(current_user: UserInDB = Depends(get_current_user)):
    return {
        "authenticated": True,
        "email": current_user.email,
        "user_id": current_user.user_id,
        "is_active": current_user.is_active
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)