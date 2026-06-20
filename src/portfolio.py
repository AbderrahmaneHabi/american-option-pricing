import pandas as pd

class Portfolio:
    """Manages multi-asset global positions and corporate/buyer profit & loss."""
    def __init__(self):
        self.positions = []
        
    def add_position(self, ticker, maturity, strike, quantity, premium, payoff=None):
        self.positions.append({
            "Ticker": ticker,
            "Maturity (Y)": maturity,
            "Strike ($)": strike,
            "Qty": quantity,
            "Total Premium Paid": premium * quantity,
            "Total Payoff Realized": (payoff * quantity) if payoff else 0.0
        })
        
    def get_summary(self):
        df = pd.DataFrame(self.positions)
        if df.empty:
            return df, 0.0, 0.0
        
        tot_prem = df["Total Premium Paid"].sum()
        tot_pay = df["Total Payoff Realized"].sum()
        df["Net PnL (Buyer)"] = df["Total Payoff Realized"] - df["Total Premium Paid"]
        
        return df, tot_prem, tot_pay