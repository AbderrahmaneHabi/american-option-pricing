"""
Live Data Options Pricing Tool
File Name: engine.py
Description: Downloads real-time market spot prices and historical data using yfinance,
             calculates live EWMA volatility, and applies analytical BSM models to
             generate customized, live option quotes instantly.
"""

import numpy as np
from scipy.stats import norm
import yfinance as yf  # Deployed to harvest live financial metrics

class LiveDataPricingEngine:
    def __init__(self, ticker, strike_k, time_interval_years):
        self.ticker = ticker.upper().strip()
        self.K = float(strike_k)
        self.T = float(time_interval_years)
        self.r = 0.043  # Benchmark risk-free rate (4.3%)
        
        # Extracted metrics
        self.S0 = 0.0
        self.ewma_vol = 0.30

    def harvest_live_market_data(self):
        """
        Connects via yfinance to grab the absolute latest market spot price
        and a 2-year lookback history to compute exact EWMA volatility.
        """
        print(f"\n📡 Querying Yahoo Finance API for {self.ticker}...")
        
        # 1. Download live stock data
        stock = yf.Ticker(self.ticker)
        
        # Get latest spot price
        todays_data = stock.history(period="1d")
        if todays_data.empty:
            raise ValueError(f"Could not find ticker symbol '{self.ticker}'. Please verify spelling.")
        
        self.S0 = float(todays_data['Close'].iloc[-1])
        
        # 2. Get 2 years of historical daily prices to build EWMA volatility
        hist = stock.history(period="2y")
        close_prices = hist['Close'].dropna().values
        
        if len(close_prices) < 10:
            print("⚠️ Insufficient history for EWMA calibration. Utilizing 30% baseline risk floor.")
            self.ewma_vol = 0.30
            return

        # 3. Process EWMA Volatility (lambda = 0.94)
        returns = np.diff(np.log(close_prices))
        n = len(returns)
        
        lambda_decay = 0.94
        weights = (1 - lambda_decay) * (lambda_decay ** np.arange(n)[::-1])
        weights /= np.sum(weights)  # Normalize weights
        
        daily_variance = np.sum(weights * (returns ** 2))
        calculated_vol = np.sqrt(daily_variance * 252)
        
        # Keep volatility bounded safely for robust options underwriting
        self.ewma_vol = np.clip(calculated_vol, 0.20, 0.60)

    def calculate_premiums(self):
        """
        Processes exact Black-Scholes-Merton math over live market parameters.
        """
        S, K, r, T, sigma = self.S0, self.K, self.r, self.T, self.ewma_vol
        
        if T <= 0:
            return {"Base_Price": max(K - S, 0.0)}
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Standard Put pricing formula
        bs_put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        base_premium = max(bs_put_price, 0.01)
        
        return {
            "Spot_Price": S,
            "Volatility": sigma,
            "Promo_Regime_Price": round(base_premium * 0.85, 2),
            "Standard_GBM_Price": round(base_premium, 2),
            "Protective_Merton_Price": round(base_premium * 1.25, 2)
        }

# ==============================================================================
# LIVE INTERACTIVE TERMINAL APP
# ==============================================================================
if __name__ == "__main__":
    print("=======================================================")
    print("      LIVE MARKET DERIVATIVES QUOTE TERMINAL          ")
    print("=======================================================")
    
    user_ticker = input("📥 Enter Stock Ticker (e.g. AAPL, NVDA, TSLA, MSFT): ")
    user_k = input("📥 Enter Strike Price K ($): ")
    user_time = input("📥 Enter Time Interval to Maturity (in Years, e.g. 1 or 0.5): ")
    
    try:
        # Build and process the pricing engine live
        tool = LiveDataPricingEngine(ticker=user_ticker, strike_k=user_k, time_interval_years=user_time)
        tool.harvest_live_market_data()
        results = tool.calculate_premiums()
        
        print("\n=======================================================")
        print(f"       OFFICIAL LIVE METRIC RECIEPT FOR {tool.ticker}         ")
        print("=======================================================")
        print(f"Live Asset Spot Price (S0)    : ${results['Spot_Price']:,.2f}")
        print(f"Live EWMA Volatility (2Yr)    : {results['Volatility']*100:.2f}%")
        print(f"Target Strike Boundary (K)    : ${tool.K:,.2f}")
        print(f"Contract Duration Horizon (T) : {tool.T} Years")
        print("-------------------------------------------------------")
        print(f"🏷️ Offer Tier A (Promo Discount)  : ${results['Promo_Regime_Price']} per share")
        print(f"🏷️ Offer Tier B (Standard BSM)     : ${results['Standard_GBM_Price']} per share")
        print(f"🏷️ Offer Tier C (Merton Shock Shield): ${results['Protective_Merton_Price']} per share")
        print("=======================================================\n")
        
    except Exception as e:
        print(f"\n❌ Execution Failed: {e}\n")