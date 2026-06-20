import numpy as np

def price_american_put(S_paths, K, r, T, M):
    """Longstaff-Schwartz Least Squares Monte Carlo Backward Induction."""
    N = S_paths.shape[0]
    dt = T / M
    discount_factor_step = np.exp(-r * dt)
    
    H = np.maximum(K - S_paths, 0.0)
    V = np.zeros_like(H)
    V[:, M] = H[:, M]
    
    saved_betas = {}
    total_early_exercises = 0
    
    # Backward sweep: Step M-1 down to 1
    for t_idx in range(M - 1, 0, -1):
        itm_mask = H[:, t_idx] > 0
        
        if np.sum(itm_mask) < 3:
            V[:, t_idx] = V[:, t_idx + 1] * discount_factor_step
            continue
            
        X_step = S_paths[itm_mask, t_idx]
        Y_step = V[itm_mask, t_idx + 1] * discount_factor_step
        
        # OLS Polynomial Regression
        beta = np.polyfit(X_step, Y_step, deg=2)
        saved_betas[t_idx] = beta
        
        C_fitted = np.polyval(beta, X_step)
        payoffs_step = H[itm_mask, t_idx]
        
        # Behavioral Trigger: If intrinsic value > continuation value
        exercise_mask = payoffs_step > C_fitted
        total_early_exercises += np.sum(exercise_mask)
        
        V[:, t_idx] = V[:, t_idx + 1] * discount_factor_step
        
        global_itm_indices = np.where(itm_mask)[0]
        global_exercise_indices = global_itm_indices[exercise_mask]
        
        # Override with immediate payoff and kill future cash flows
        V[global_exercise_indices, t_idx] = H[global_exercise_indices, t_idx]
        V[global_exercise_indices, t_idx + 1:] = 0.0

    american_put_price = np.mean(V[:, 1] * discount_factor_step)
    european_put_price = np.mean(H[:, M]) * np.exp(-r * T)
    
    diagnostics = {
        "early_exercises": total_early_exercises,
        "european_price": european_put_price,
        "early_exercise_premium": american_put_price - european_put_price
    }
    
    return american_put_price, saved_betas, diagnostics, H