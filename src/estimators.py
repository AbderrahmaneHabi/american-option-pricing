import numpy as np

def estimate_parameters(df):
    """
    Computes statistical moments manually using first principles (Bessel's correction).
    Ensures absolute mathematical transparency per notebook requirements.
    """
    raw_prices = df['Target_Price'].values
    S0 = float(raw_prices[-1])
    
    # 1. Manual log returns
    log_returns = []
    for i in range(1, len(raw_prices)):
        r_i = np.log(raw_prices[i] / raw_prices[i-1])
        log_returns.append(r_i)
        
    n = len(log_returns)
    r_bar = sum(log_returns) / n
    
    # 2. Variance using Bessel's Correction (n-1)
    squared_deviations_sum = sum((r_i - r_bar)**2 for r_i in log_returns)
    daily_variance = squared_deviations_sum / (n - 1)
    
    daily_std = np.sqrt(daily_variance)
    sigma_hat = daily_std * np.sqrt(252) # Annualized
    
    return {
        "S0": S0,
        "r_bar": r_bar,
        "daily_variance": daily_variance,
        "daily_std": daily_std,
        "sigma_hat": sigma_hat,
        "n": n,
        "log_returns": log_returns
    }