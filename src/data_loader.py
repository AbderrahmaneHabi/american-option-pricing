import yfinance as yf
import pandas as pd
import numpy as np

def fetch_data(ticker, start_date, end_date="2024-12-31"):
    """Downloads historical data and aggressively sanitizes yfinance MultiIndex/NaN issues."""
    
    # 1. Download data
    df = yf.download(ticker, start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError(f"No data retrieved for ticker {ticker}. Verify network or symbol.")
        
    # 2. Flatten yfinance MultiIndex headers (The root cause of column mapping failures)
    if isinstance(df.columns, pd.MultiIndex):
        # Extracts just the first level (e.g., 'Close' instead of ('Close', 'AAPL'))
        df.columns = [col[0] for col in df.columns]
        
    # Ensure Date is accessible
    if 'Date' not in df.columns:
        df.reset_index(inplace=True)
        
    # 3. Isolate the target price safely
    if 'Adj Close' in df.columns:
        df['Target_Price'] = pd.to_numeric(df['Adj Close'], errors='coerce')
    elif 'Close' in df.columns:
        df['Target_Price'] = pd.to_numeric(df['Close'], errors='coerce')
    else:
        raise KeyError(f"Could not find 'Close' column. Available columns: {list(df.columns)}")
        
    # 4. AGGRESSIVE SANITIZATION (Fixes the "Infinity/SVD" Regression Crash)
    # Drop any row where the price is missing, 0, or infinite
    df = df.dropna(subset=['Target_Price']).copy()
    df = df[df['Target_Price'] > 0] 
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['Target_Price'])
    
    if df.empty:
        raise ValueError("Dataframe became empty after dropping NaNs. Check dates or ticker.")

    # 5. Lock index for time-series operations
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    return df