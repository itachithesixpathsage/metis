"""
Unit tests for stochastic simulation models.
"""

import numpy as np
import pytest
from scipy.stats import norm


class TestGBM:
    """Test Geometric Brownian Motion simulation."""

    def test_gbm_formula(self):
        """Test GBM discrete formula: S(t+dt) = S(t) * exp((mu - sigma^2/2)*dt + sigma*sqrt(dt)*Z)"""
        # Parameters
        S0 = 100.0
        mu = 0.05
        sigma = 0.20
        dt = 1/252
        T = 1.0
        steps = int(T / dt)
        num_paths = 10000
        seed = 42

        np.random.seed(seed)
        Z = np.random.normal(0, 1, (num_paths, steps))

        # Vectorized GBM
        drift_term = (mu - 0.5 * sigma**2) * dt
        diffusion_term = sigma * np.sqrt(dt)
        log_returns = drift_term + diffusion_term * Z
        price_paths = S0 * np.exp(np.cumsum(log_returns, axis=1))

        # Check terminal distribution
        terminal_prices = price_paths[:, -1]
        log_terminal = np.log(terminal_prices / S0)

        # Expected mean and variance of log returns
        expected_mean = (mu - 0.5 * sigma**2) * T
        expected_var = sigma**2 * T

        np.testing.assert_allclose(np.mean(log_terminal), expected_mean, rtol=0.05)
        np.testing.assert_allclose(np.var(log_terminal), expected_var, rtol=0.05)

    def test_gbm_reproducibility(self):
        """Test that same seed produces same results."""
        params = {
            "S0": 100.0, "mu": 0.0, "sigma": 0.15, "dt": 1/96, "steps": 16, "num_paths": 1000, "seed": 123
        }

        def run_gbm(seed):
            np.random.seed(seed)
            Z = np.random.normal(0, 1, (params["num_paths"], params["steps"]))
            drift = (params["mu"] - 0.5 * params["sigma"]**2) * params["dt"]
            diff = params["sigma"] * np.sqrt(params["dt"])
            paths = params["S0"] * np.exp(np.cumsum(drift + diff * Z, axis=1))
            return paths

        paths1 = run_gbm(params["seed"])
        paths2 = run_gbm(params["seed"])
        np.testing.assert_array_equal(paths1, paths2)

    def test_gbm_zero_drift(self):
        """Test GBM with zero drift (martingale)."""
        np.random.seed(42)
        S0 = 1.0850
        mu = 0.0
        sigma = 0.10
        dt = 1/96
        steps = 16
        num_paths = 50000

        Z = np.random.normal(0, 1, (num_paths, steps))
        drift = (mu - 0.5 * sigma**2) * dt
        diff = sigma * np.sqrt(dt)
        paths = S0 * np.exp(np.cumsum(drift + diff * Z, axis=1))

        terminal = paths[:, -1]
        # For zero drift, E[S_T] = S_0 * exp(-0.5*sigma^2*T) < S_0
        expected_mean = S0 * np.exp(-0.5 * sigma**2 * steps * dt)
        np.testing.assert_allclose(np.mean(terminal), expected_mean, rtol=0.02)

    def test_gbm_vectorization(self):
        """Test vectorized implementation produces correct shapes."""
        num_paths = 1000
        steps = 16

        np.random.seed(42)
        Z = np.random.normal(0, 1, (num_paths, steps))
        assert Z.shape == (num_paths, steps)

        drift = 0.0
        diff = 0.1 * np.sqrt(1/96)
        log_returns = drift + diff * Z
        assert log_returns.shape == (num_paths, steps)

        paths = np.exp(np.cumsum(log_returns, axis=1))
        assert paths.shape == (num_paths, steps)


class TestHistoricalBootstrap:
    """Test historical bootstrap simulation."""

    def test_independent_bootstrap(self):
        """Test independent bootstrap resampling."""
        np.random.seed(42)
        historical_returns = np.random.normal(0.0001, 0.01, 1000)
        num_paths = 1000
        horizon = 16

        # Resample with replacement
        bootstrap_samples = np.random.choice(
            historical_returns, size=(num_paths, horizon), replace=True
        )

        assert bootstrap_samples.shape == (num_paths, horizon)
        # Check that samples come from original data
        unique_sampled = np.unique(bootstrap_samples)
        unique_original = np.unique(historical_returns)
        assert len(unique_sampled) <= len(unique_original)

    def test_bootstrap_price_reconstruction(self):
        """Test price path reconstruction from bootstrapped returns."""
        np.random.seed(42)
        S0 = 1.0850
        historical_returns = np.random.normal(0.0001, 0.01, 1000)
        num_paths = 1000
        horizon = 16

        bootstrap_returns = np.random.choice(
            historical_returns, size=(num_paths, horizon), replace=True
        )

        # Reconstruct prices: S_t = S_0 * exp(cumsum(log_returns))
        log_returns = np.log1p(bootstrap_returns)  # log(1+r) ≈ r for small r
        price_paths = S0 * np.exp(np.cumsum(log_returns, axis=1))

        assert price_paths.shape == (num_paths, horizon)
        assert np.all(price_paths > 0)

    def test_bootstrap_reproducibility(self):
        """Test bootstrap reproducibility with seed."""
        historical_returns = np.arange(100.0)
        num_paths = 100
        horizon = 10

        np.random.seed(42)
        sample1 = np.random.choice(historical_returns, size=(num_paths, horizon), replace=True)

        np.random.seed(42)
        sample2 = np.random.choice(historical_returns, size=(num_paths, horizon), replace=True)

        np.testing.assert_array_equal(sample1, sample2)


class TestGARCH:
    """Test GARCH(1,1) model."""

    def test_garch_variance_recursion(self):
        """Test GARCH(1,1) variance recursion: sigma^2_t = omega + alpha*eps^2_{t-1} + beta*sigma^2_{t-1}"""
        # Parameters
        omega = 0.000001
        alpha = 0.1
        beta = 0.85
        eps = np.array([0.01, -0.02, 0.015, -0.01, 0.005])  # Shocks
        sigma2_0 = 0.0001  # Initial variance

        sigma2 = np.zeros(len(eps) + 1)
        sigma2[0] = sigma2_0

        for t in range(1, len(sigma2)):
            sigma2[t] = omega + alpha * eps[t-1]**2 + beta * sigma2[t-1]

        # Verify recursion
        expected = np.array([
            0.0001,
            omega + alpha * 0.01**2 + beta * 0.0001,
            omega + alpha * (-0.02)**2 + beta * sigma2[1],
            omega + alpha * 0.015**2 + beta * sigma2[2],
            omega + alpha * (-0.01)**2 + beta * sigma2[3],
            omega + alpha * 0.005**2 + beta * sigma2[4],
        ])
        np.testing.assert_allclose(sigma2, expected, rtol=1e-10)

    def test_garch_stationarity_condition(self):
        """Test GARCH stationarity condition: alpha + beta < 1"""
        # Stationary
        assert 0.1 + 0.85 < 1
        assert 0.05 + 0.90 < 1
        assert 0.2 + 0.7 < 1

        # Non-stationary (integrated GARCH)
        assert 0.1 + 0.9 == 1.0

        # Explosive
        assert 0.2 + 0.9 > 1

    def test_garch_unconditional_variance(self):
        """Test unconditional variance: sigma^2 = omega / (1 - alpha - beta)"""
        omega = 0.000001
        alpha = 0.1
        beta = 0.85

        unconditional_var = omega / (1 - alpha - beta)
        expected = 0.000001 / 0.05  # = 0.00002
        np.testing.assert_allclose(unconditional_var, expected, rtol=1e-10)

    def test_garch_forecast(self):
        """Test GARCH variance forecasting."""
        omega = 0.000001
        alpha = 0.1
        beta = 0.85
        sigma2_last = 0.0002
        eps_last = 0.015

        # 1-step ahead forecast
        forecast_1 = omega + alpha * eps_last**2 + beta * sigma2_last

        # Multi-step ahead (converges to unconditional)
        forecasts = []
        sigma2_t = sigma2_last
        eps_t = eps_last
        for h in range(1, 40):
            sigma2_t = omega + alpha * eps_t**2 + beta * sigma2_t
            forecasts.append(sigma2_t)
            eps_t = 0  # Expected future shocks are zero

        # Should converge to unconditional variance
        unconditional = omega / (1 - alpha - beta)
        np.testing.assert_allclose(forecasts[-1], unconditional, rtol=0.1)


class TestSimulationComparison:
    """Test comparison between simulation models."""

    def test_gbm_vs_bootstrap_terminal_moments(self):
        """Compare terminal distribution moments between GBM and bootstrap."""
        np.random.seed(42)

        # Historical data
        hist_returns = np.random.normal(0.0001, 0.01, 1000)
        hist_vol = np.std(hist_returns)
        S0 = 1.0850
        horizon = 16
        num_paths = 10000

        # GBM with historical volatility
        Z = np.random.normal(0, 1, (num_paths, horizon))
        dt = 1.0
        gbm_returns = (0 - 0.5 * hist_vol**2) * dt + hist_vol * np.sqrt(dt) * Z
        gbm_terminal = S0 * np.exp(np.sum(gbm_returns, axis=1))
        gbm_log_returns = np.log(gbm_terminal / S0)

        # Bootstrap
        boot_returns = np.random.choice(hist_returns, size=(num_paths, horizon), replace=True)
        boot_log_returns = np.sum(np.log1p(boot_returns), axis=1)
        boot_terminal = S0 * np.exp(boot_log_returns)

        # Both should have similar mean (approximately)
        # Bootstrap preserves historical distribution, GBM assumes normal
        assert abs(np.mean(gbm_log_returns) - np.mean(boot_log_returns)) < 0.01


class TestMultivariateSimulation:
    """Test multivariate simulation with correlation."""

    def test_cholesky_correlation(self):
        """Test generating correlated random variables via Cholesky."""
        np.random.seed(42)

        # Correlation matrix
        corr = np.array([
            [1.0, 0.5, -0.3],
            [0.5, 1.0, 0.2],
            [-0.3, 0.2, 1.0]
        ])

        # Cholesky decomposition
        L = np.linalg.cholesky(corr)
        assert L.shape == (3, 3)

        # Generate independent standard normals
        Z_indep = np.random.normal(0, 1, (10000, 3))

        # Apply correlation
        # Finite-sample variation can exceed 0.02 for the original 10k sample;
        # retain the seed and increase the sample for a stable tolerance check.
        Z_indep = np.random.normal(0, 1, (100_000, 3))
        Z_corr = Z_indep @ L.T

        # Check resulting correlation
        emp_corr = np.corrcoef(Z_corr.T)
        np.testing.assert_allclose(emp_corr, corr, atol=0.02)

    def test_near_psd_correction(self):
        """Test correction for near-positive-semidefinite matrices."""
        # Matrix with small negative eigenvalue
        corr = np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
        eigenvals = np.linalg.eigvalsh(corr)
        # Should be positive semi-definite
        assert np.all(eigenvals >= -1e-10)

        # Slightly perturbed
        corr_perturbed = corr + np.eye(3) * 1e-10
        eigenvals = np.linalg.eigvalsh(corr_perturbed)
        assert np.all(eigenvals > 0)


class TestConfidenceIntervals:
    """Test confidence interval calculations."""

    def test_var_percentile(self):
        """Test VaR as percentile of loss distribution."""
        np.random.seed(42)
        losses = np.random.normal(0, 1000, 100000)

        var_95 = np.percentile(losses, 5)  # 5th percentile for 95% VaR
        var_99 = np.percentile(losses, 1)  # 1st percentile for 99% VaR

        # For normal(0, 1000), 95% VaR ≈ -1.645 * 1000 = -1645
        # 99% VaR ≈ -2.326 * 1000 = -2326
        assert abs(var_95 - (-1645)) < 50
        assert abs(var_99 - (-2326)) < 50

    def test_expected_shortfall(self):
        """Test Expected Shortfall (Conditional VaR)."""
        np.random.seed(42)
        losses = np.random.normal(0, 1000, 100000)

        var_95 = np.percentile(losses, 5)
        es_95 = np.mean(losses[losses <= var_95])

        # For normal, ES_95 = -phi(-1.645)/0.05 * sigma
        # phi(-1.645) ≈ 0.103, so ES ≈ -2.06 * 1000 = -2060
        assert abs(es_95 - (-2060)) < 50
