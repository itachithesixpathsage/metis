"""
Unit tests for statistical analysis - returns calculations.
"""

import numpy as np
import pytest


class TestReturnsCalculation:
    """Test returns calculation functions."""

    def test_simple_return(self):
        """Test simple return calculation: R(t) = P(t)/P(t-1) - 1"""
        prices = np.array([100.0, 102.0, 101.0, 103.0])
        returns = prices[1:] / prices[:-1] - 1
        expected = np.array([0.02, -0.00980392, 0.01980198])
        np.testing.assert_allclose(returns, expected, rtol=1e-6)

    def test_log_return(self):
        """Test log return calculation: r(t) = ln(P(t)/P(t-1))"""
        prices = np.array([100.0, 102.0, 101.0, 103.0])
        log_returns = np.log(prices[1:] / prices[:-1])
        expected = np.log(np.array([1.02, 101.0/102.0, 103.0/101.0]))
        np.testing.assert_allclose(log_returns, expected, rtol=1e-10)

    def test_log_return_approximation(self):
        """Test that log return approximates simple return for small changes."""
        prices = np.array([100.0, 100.1, 100.05, 100.15])
        simple = prices[1:] / prices[:-1] - 1
        log_r = np.log(prices[1:] / prices[:-1])
        np.testing.assert_allclose(simple, log_r, rtol=1e-3)

    def test_return_with_zero_price_raises(self):
        """Test that zero prices are handled."""
        prices = np.array([0.0, 100.0, 101.0])
        with pytest.warns(RuntimeWarning):
            returns = prices[1:] / prices[:-1] - 1
        assert np.isinf(returns[0]) or np.isnan(returns[0])


class TestDescriptiveStatistics:
    """Test descriptive statistics functions."""

    def test_mean(self):
        """Test mean calculation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert np.mean(data) == 3.0

    def test_variance(self):
        """Test variance calculation (sample variance)."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        # Sample variance (ddof=1)
        assert np.var(data, ddof=1) == 2.5

    def test_std(self):
        """Test standard deviation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        expected = np.sqrt(2.5)
        np.testing.assert_allclose(np.std(data, ddof=1), expected, rtol=1e-10)

    def test_skewness(self):
        """Test skewness calculation."""
        from scipy.stats import skew
        # Symmetric distribution should have ~0 skewness
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0])
        # This sequence is median-symmetric, but not mean-symmetric, so its
        # third central moment is not zero. Check SciPy's established value.
        np.testing.assert_allclose(skew(data, bias=False), 0.1463545236, rtol=1e-8)

    def test_kurtosis(self):
        """Test excess kurtosis calculation."""
        from scipy.stats import kurtosis
        # Normal distribution has excess kurtosis ~0
        np.random.seed(42)
        data = np.random.normal(0, 1, 10000)
        assert abs(kurtosis(data)) < 0.1

    def test_min_max(self):
        """Test min and max."""
        data = np.array([5.0, 2.0, 8.0, 1.0, 9.0])
        assert np.min(data) == 1.0
        assert np.max(data) == 9.0


class TestRollingVolatility:
    """Test rolling volatility calculations."""

    def test_rolling_std(self):
        """Test rolling standard deviation."""
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 200)
        window = 20
        rolling_vol = np.array([
            np.std(returns[i-window:i], ddof=1)
            for i in range(window, len(returns))
        ])
        assert len(rolling_vol) == len(returns) - window
        # Should be close to true volatility (0.01)
        np.testing.assert_allclose(np.mean(rolling_vol), 0.01, rtol=0.2)

    def test_annualisation_factor(self):
        """Test annualisation factors for different frequencies."""
        # 15-min bars: 96 bars per day, ~252 trading days = 24192 bars/year
        # sqrt(24192) ≈ 155.5
        # But commonly: sqrt(96 * 252) = sqrt(24192) ≈ 155.5
        # For daily: sqrt(252) ≈ 15.87
        daily_factor = np.sqrt(252)
        intraday_15min_factor = np.sqrt(96 * 252)
        intraday_5min_factor = np.sqrt(288 * 252)
        intraday_1h_factor = np.sqrt(24 * 252)

        assert abs(daily_factor - 15.8745) < 0.01
        assert abs(intraday_15min_factor - 155.563) < 0.1
        assert abs(intraday_5min_factor - 269.399) < 0.1
        assert abs(intraday_1h_factor - 77.781) < 0.1


class TestCorrelation:
    """Test correlation calculations."""

    def test_pearson_correlation(self):
        """Test Pearson correlation coefficient."""
        np.random.seed(42)
        x = np.random.normal(0, 1, 1000)
        y = 0.7 * x + np.sqrt(1 - 0.7**2) * np.random.normal(0, 1, 1000)
        corr = np.corrcoef(x, y)[0, 1]
        # Should be close to 0.7
        assert abs(corr - 0.7) < 0.05

    def test_correlation_matrix(self):
        """Test correlation matrix properties."""
        np.random.seed(42)
        n_assets = 4
        n_obs = 1000
        returns = np.random.normal(0, 0.01, (n_obs, n_assets))
        # Add correlation
        returns[:, 1] = 0.5 * returns[:, 0] + 0.5 * np.random.normal(0, 0.01, n_obs)
        returns[:, 2] = -0.3 * returns[:, 0] + 0.7 * np.random.normal(0, 0.01, n_obs)

        corr_matrix = np.corrcoef(returns.T)
        assert corr_matrix.shape == (n_assets, n_assets)
        # Diagonal should be 1
        np.testing.assert_allclose(np.diag(corr_matrix), 1.0, atol=1e-10)
        # Matrix should be symmetric
        np.testing.assert_allclose(corr_matrix, corr_matrix.T, atol=1e-10)
        # Should be positive semi-definite (all eigenvalues >= 0)
        eigenvals = np.linalg.eigvalsh(corr_matrix)
        assert np.all(eigenvals >= -1e-10)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_array(self):
        """Test handling of empty arrays."""
        data = np.array([])
        assert np.isnan(np.mean(data))
        assert np.isnan(np.std(data))

    def test_single_element(self):
        """Test handling of single element."""
        data = np.array([5.0])
        assert np.mean(data) == 5.0
        assert np.isnan(np.std(data, ddof=1))  # Sample std with 1 element is NaN

    def test_constant_array(self):
        """Test handling of constant array."""
        data = np.full(100, 5.0)
        assert np.mean(data) == 5.0
        assert np.std(data) == 0.0
        assert np.all(np.isnan(np.corrcoef(data, data)))

    def test_nan_handling(self):
        """Test NaN handling."""
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        assert np.isnan(np.mean(data))
        assert np.isnan(np.std(data))
        # nanmean should work
        assert np.nanmean(data) == 3.0
