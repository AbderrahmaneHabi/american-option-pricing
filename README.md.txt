# American Option Pricing via Least-Squares Monte Carlo (LSM)

> **Advanced Derivative Valuation, Multi-Regime Volatility Calibration, and Stochastic Behavioral Risk Ledger Platform.**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Framework Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

This project delivers an end-to-end, institutional-grade quantitative framework for pricing, backtesting, and underwriting **American-style financial derivatives**. Moving beyond static analytical approximations, this platform implements a fully vectorized **Longstaff-Schwartz Least Squares Monte Carlo (LSM)** simulation engine. It integrates advanced continuous-time stochastic processes, dynamic volatility regimes, behavioral finance models, and a production-ready interactive dashboard to transform academic stochastic calculus into a commercial-grade risk management platform.

---

> 📄 **Quick Navigation Documentation:**
> * Want a high-level overview? Read our 3-page [Executive Summary](docs/executive_summary.pdf).
> * Ready for the full mathematical proofs? Dive into the [Full Project Report](docs/report.pdf).

---

## 🛠️ Core Quantitative Features

* **Longstaff-Schwartz (LSM) Backward Induction Engine:** Implements cross-sectional polynomial regressions over optimal temporal nodes to accurately separate the conditional continuation value ($\hat{C}_t$) from immediate intrinsic value ($H_t$) for In-The-Money (ITM) paths.
* **Multi-Model Stochastic Path Projection:**
  * **Standard Geometric Brownian Motion (GBM):** Discretized analytical integration via Itô's Lemma under the risk-neutral measure.
  * **Merton Jump-Diffusion:** Integrates a Poisson process ($\lambda = 1.5$) with asymmetric, negatively skewed downside shock severity ($\mu_J = -0.15, \sigma_J = 0.10$) to insulate capital blocks from systemic crash anomalies.
  * **Markov Regime-Switching:** Eliminates flat historical volatility distortion by alternating dynamically between an *Expansionary State* ($\sigma_{low}$) and a *Turbulent State* ($\sigma_{high}$) via a calibrated transition probability matrix.
* **Applied Behavioral Attrition Engines:** Models counterparty risk out-of-sample by implementing rolling stochastic human behavioral triggers (e.g., non-rational "greed thresholds" and "panic stop-loss liquidation curves") rather than assuming strictly rational mathematical actors.
* **Multi-Asset Portfolio Book Management:** Aggregates risk configurations across non-correlated asset profiles (**AAPL**, **NVDA**, **GLD**, and **SPY**) to stress-test Modern Portfolio Theory (MPT) under synchronized systemic market shocks.
* **Live Calibration & FinTech UI:** Real-time data pipeline powered by the `yfinance` API featuring an **Exponentially Weighted Moving Average (EWMA)** volatility module (252-day decay span) and an interactive **Streamlit** trade execution ledger.

---

## 📐 Key Mathematical Foundations

### 1. Risk-Neutral Asset Propagation (GBM)
The continuous temporal expansion of the underlying spot index is governed by the Stochastic Differential Equation (SDE):

$$dS_t = rS_t dt + \sigma S_t dW_t$$

Vectorized paths are generated step-wise across a space-time grid via the discrete-time mapping:

$$S_{i,j} = S_{i,j-1} \exp\left( \left(r - \frac{1}{2}\sigma^2\right)\Delta t + \sigma \sqrt{\Delta t} Z_{i,j} \right)$$

### 2. Live Volatility Architecture (EWMA)
To avoid overpricing or underpricing derivatives based on stale historical windows, the backend calibrates realized asset behavior using an Exponentially Weighted Moving Average:

$$\sigma_{ewma} = \sqrt{\text{EWMA}(R_t^2, \text{span}=252) \times 252}$$

### 3. Optimal Stopping Regression Rule
At each chronological slice $t_{M-1}$ moving backward from maturity, the engine isolates paths where $S_t < K$ and performs an ordinary least squares (OLS) regression using a polynomial basis function to predict continuation values:

$$\min_{\beta} \sum_{i \in \text{ITM}} \left( Y_i - \sum_{k=0}^{P} \beta_k X_i^k \right)^2$$

Where $X_i = S_{i, t_{M-1}}$ and $Y_i = V_{i, t_M} \times \gamma$. Early exercise is executed if and only if immediate payout exceeds prediction ($H_i > \hat{C}_i$).

---

## 📁 Repository Directory Layout

```text
american-option-pricing/
├── data/
│   └── AAPL_2020_2024.csv          # 5-year macro-regime historical baseline
├── docs/
│   ├── executive_summary.pdf       # 3-page concise executive brief
│   ├── report.pdf                  # Complete deep-dive quantitative thesis
│   └── latex_pics/                 # Static graphical assets & model diagrams
├── notebooks/
│   └── exploration.ipynb           # Model development, matrix testing & validation
├── src/
│   ├── app.py                      # Main production Streamlit dashboard application
│   ├── engine.py                   # Live pricing API, EWMA, and pricing tiers
│   ├── gbm.py                      # Geometric Brownian Motion matrix array generator
│   ├── lsm.py                      # Longstaff-Schwartz backward induction logic
│   ├── estimators.py               # Parameter derivation & statistical filters
│   ├── backtest.py                 # Out-of-sample corporate underwriting simulations
│   ├── portfolio.py                # Cross-asset portfolio matrix aggregation
│   └── plots.py                    # Analytical data visualization pipeline
├── .gitignore                      # Prevents local __pycache__/ & checkpoints leak
├── requirements.txt                # Production environment dependencies
└── README.md                       # Repository command center