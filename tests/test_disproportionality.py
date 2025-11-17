"""Unit tests for disproportionality calculations."""

import pytest
import numpy as np
from src.models.disproportionality import compute_ror, compute_prr, build_contingency_table
import pandas as pd


def test_ror_calculation_known_values():
    """Test ROR with manually calculated values."""
    # Example: a=50, b=950, c=100, d=9900
    # ROR = (50*9900) / (950*100) = 5.21
    ror, ci_low, ci_high = compute_ror(50, 950, 100, 9900)
    
    assert np.isclose(ror, 5.21, atol=0.01), f"Expected ROR ~5.21, got {ror}"
    assert ci_low > 1.0, "CI lower bound should be > 1 for significant signal"
    assert ci_high > ror, "CI upper should be > ROR"


def test_ror_handles_zero_cells():
    """ROR should return NaN for zero cells."""
    ror, ci_low, ci_high = compute_ror(0, 100, 50, 1000)
    assert np.isnan(ror), "ROR should be NaN when a=0"
    
    ror, ci_low, ci_high = compute_ror(10, 0, 50, 1000)
    assert np.isnan(ror), "ROR should be NaN when b=0"
    
    ror, ci_low, ci_high = compute_ror(10, 100, 0, 1000)
    assert np.isnan(ror), "ROR should be NaN when c=0"


def test_ror_no_signal():
    """ROR close to 1 should not be significant."""
    ror, ci_low, ci_high = compute_ror(50, 50, 50, 50)
    assert np.isclose(ror, 1.0, atol=0.1), f"Expected ROR ~1.0, got {ror}"
    assert ci_low < 1.0 or ci_high < 1.0, "CI should include 1.0 for no signal"


def test_prr_calculation():
    """Test PRR calculation."""
    prr, chi2 = compute_prr(50, 950, 100, 9900)
    
    # PRR = (50/1000) / (100/10000) = 0.05 / 0.01 = 5.0
    expected_prr = (50 / 1000) / (100 / 10000)
    assert np.isclose(prr, expected_prr, atol=0.1), f"Expected PRR ~{expected_prr}, got {prr}"
    assert chi2 > 0, "Chi-square should be positive"


def test_build_contingency_table():
    """Test contingency table construction."""
    df = pd.DataFrame({
        'drug': ['A', 'A', 'A', 'B', 'B', 'B'],
        'event': ['X', 'X', 'Y', 'X', 'Z', 'Z']
    })
    
    a, b, c, d = build_contingency_table(df, 'drug', 'A', 'event', 'X')
    
    assert a == 2, f"Expected a=2, got {a}"
    assert b == 1, f"Expected b=1, got {b}"
    assert c == 1, f"Expected c=1, got {c}"
    assert d == 2, f"Expected d=2, got {d}"


def test_build_contingency_table_with_nan():
    """Test contingency table handles NaN correctly."""
    df = pd.DataFrame({
        'drug': ['A', 'A', 'A', 'B', np.nan],
        'event': ['X', 'X', np.nan, 'X', 'X']
    })
    
    a, b, c, d = build_contingency_table(df, 'drug', 'A', 'event', 'X')
    
    # Should exclude NaN values
    assert a >= 0, "a should be non-negative"
    assert b >= 0, "b should be non-negative"
    assert c >= 0, "c should be non-negative"
    assert d >= 0, "d should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

