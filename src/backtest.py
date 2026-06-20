import yfinance as yf
import numpy as np
import pandas as pd
import datetime

def run_backtest(ticker, K, saved_betas, r, T, M):
    """Subject the priced contract to the actual 2025 timeline logic."""
    start_date = "2025-01-01"
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    
    df = yf.download(ticker, start=start_date, end=end_date)
    if df.empty: return None
        
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    real_prices = df['Close'].dropna().values
    if len(real_prices) < 2: return None
        
    # Scale physical dates into M discrete checkpoints 
    indices = np.linspace(0, len(real_prices) - 1, M + 1).astype(int)
    s_real = real_prices[indices]
    
    exercise_step = -1
    final_payoff = 0.0
    
    for t in range(1, M):
        current_price = s_real[t]
        intrinsic_val = max(K - current_price, 0)
        
        # Check human behavioral matrix (if Intrinsic > Estimated Continuation)
        if intrinsic_val > 0 and t in saved_betas:
            C_hat = np.polyval(saved_betas[t], current_price)
            if intrinsic_val > C_hat:
                exercise_step = t
                final_payoff = intrinsic_val
                break
                
    # If the contract survives until maturity
    if exercise_step == -1:
        intrinsic_val = max(K - s_real[-1], 0)
        if intrinsic_val > 0:
            exercise_step = M
            final_payoff = intrinsic_val
            
    return {
        "exercise_step": exercise_step,
        "payoff": final_payoff,
        "s_real_path": s_real
    }