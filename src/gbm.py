import numpy as np

def simulate_gbm(S0, r, sigma_hat, T, M, N=10000):
    """Vectorized Geometric Brownian Motion Simulator."""
    dt = T / M
    S_paths = np.zeros((N, M + 1))
    S_paths[:, 0] = S0
    
    np.random.seed(42) # Fixed seed for consistency
    
    for t in range(1, M + 1):
        Z = np.random.standard_normal(N)
        drift = (r - 0.5 * sigma_hat**2) * dt
        diffusion = sigma_hat * np.sqrt(dt) * Z
        S_paths[:, t] = S_paths[:, t - 1] * np.exp(drift + diffusion)
        
    return S_paths