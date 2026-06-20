import sys
import os

# This line forces Python to look inside your src folder no matter where you run it from
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import fetch_data
from estimators import estimate_parameters
from gbm import simulate_gbm
from lsm import price_american_put
import numpy as np

def price_option(ticker: str, maturity_years: float, strike: float | None = None, valuation_end: str = "2024-12-31"):
    """Master wrapper fulfilling the specific requirement outlined in the prompt."""
    
    # 1. Fetch and clean data
    df = fetch_data(ticker, "2020-01-01", valuation_end)
    
    # 2. Estimate moments
    params = estimate_parameters(df)
    S0 = params["S0"]
    sigma_hat = params["sigma_hat"]
    r = 0.05
    
    # Mathematical failsafe
    if sigma_hat <= 0 or sigma_hat != sigma_hat: 
        sigma_hat = 0.20
        
    K = strike if strike is not None else S0
    
    # 3. Define Time Steps (M)
    M = max(10, int(50 * maturity_years)) 
    N = 10000
    
    # 4. Simulate Paths and Price
    S_paths = simulate_gbm(S0, r, sigma_hat, maturity_years, M, N)
    premium, saved_betas, diagnostics, H_matrix = price_american_put(S_paths, K, r, maturity_years, M)
    
    return {
        "premium": premium,
        "S0": S0,
        "sigma_hat": sigma_hat,
        "K": K,
        "T": maturity_years,
        "saved_betas": saved_betas,
        "diagnostics": diagnostics,
        "log_returns": params["log_returns"],
        "S_paths": S_paths,
        "H_matrix": H_matrix,
        "historical_df": df
    }

def generate_offers(ticker, maturity_years, valuation_end="2024-12-31"):
    """Automates structured tier creation."""
    base_res = price_option(ticker, maturity_years, strike=None, valuation_end=valuation_end)
    S0 = base_res["S0"]
    
    offers = []
    configs = [
        ("Basic Protection", 0.90, "90%"),
        ("Standard Protection", 1.00, "100%"),
        ("Premium Protection", 1.10, "110%")
    ]
    
    for label, multiplier, pct in configs:
        k = S0 * multiplier
        res = price_option(ticker, maturity_years, strike=k, valuation_end=valuation_end)
        offers.append({
            "Tier": label,
            "Strike": k,
            "Premium": res["premium"],
            "Protection %": pct,
            "Details": res
        })
        
    return offers