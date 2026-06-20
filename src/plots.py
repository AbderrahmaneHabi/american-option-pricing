import matplotlib.pyplot as plt
import numpy as np

def plot_historical(df):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df['Target_Price'], color='navy', lw=1.5)
    ax.set_title("Asset Historical Price Trajectory", fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    return fig

def plot_returns(log_returns, r_bar, daily_std):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(log_returns, bins=60, color='crimson', edgecolor='black', alpha=0.6, density=True)
    x_axis = np.linspace(r_bar - 4 * daily_std, r_bar + 4 * daily_std, 300)
    pdf = (1.0 / (daily_std * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((x_axis - r_bar) / daily_std) ** 2)
    ax.plot(x_axis, pdf, color='black', lw=2.0, linestyle='--')
    ax.set_title("Log Returns vs. Perfect Gaussian Overlay", fontweight='bold')
    return fig

def plot_gbm_paths(S_paths, S0, T, num_paths=20):
    fig, ax = plt.subplots(figsize=(10, 4))
    M = S_paths.shape[1] - 1
    time_grid = np.linspace(0, T, M + 1)
    for i in range(num_paths):
        ax.plot(time_grid, S_paths[i, :], lw=1.0, alpha=0.8)
    ax.axhline(S0, color='black', linestyle=':', label=f'Initial S0 (${S0:.2f})')
    ax.set_title("Monte Carlo Asset Projection (Sample Paths)", fontweight='bold')
    ax.legend()
    return fig