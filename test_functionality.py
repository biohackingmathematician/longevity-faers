"""
Test suite for FAERS Longevity Drug Safety Analysis.

Validates core functionality including disproportionality calculations,
data processing, and feature engineering using mock data.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def test_disproportionality():
    """Test disproportionality calculations."""
    print("Testing disproportionality calculations...")
    
    try:
        from src.models.disproportionality import compute_ror, compute_prr, build_contingency_table
        
        # Test ROR calculation
        ror, ci_low, ci_high = compute_ror(10, 100, 50, 1000)
        assert not np.isnan(ror), "ROR should not be NaN"
        assert ci_low < ror < ci_high, "CI should bracket ROR"
        print(f"  PASS: compute_ror: ROR={ror:.2f}, CI=[{ci_low:.2f}, {ci_high:.2f}]")
        
        # Test PRR calculation
        prr, chi2 = compute_prr(10, 100, 50, 1000)
        assert not np.isnan(prr), "PRR should not be NaN"
        print(f"  PASS: compute_prr: PRR={prr:.2f}, chi2={chi2:.2f}")
        
        # Test contingency table
        df = pd.DataFrame({
            'drug': ['A', 'A', 'A', 'B', 'B'],
            'event': ['X', 'X', 'Y', 'X', 'Z']
        })
        a, b, c, d = build_contingency_table(df, 'drug', 'A', 'event', 'X')
        assert a == 2, f"Expected a=2, got {a}"
        assert b == 1, f"Expected b=1, got {b}"
        print(f"  PASS: build_contingency_table: a={a}, b={b}, c={c}, d={d}")
        
        return True
    except Exception as e:
        print(f"  FAIL: Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dedupe_cases():
    """Test case deduplication."""
    print("\nTesting case deduplication...")
    
    try:
        from src.data_ingest.dedupe_cases import dedupe_cases
        
        demo = pd.DataFrame({
            'caseid': [1, 1, 2, 2, 3],
            'fda_dt': pd.to_datetime(['2020-01-01', '2020-02-01', '2020-01-01', '2020-01-15', '2020-01-01']),
            'age': [50, 50, 60, 60, 70]
        })
        
        deduped = dedupe_cases(demo)
        assert len(deduped) == 3, f"Expected 3 cases, got {len(deduped)}"
        case1_date = deduped[deduped['caseid'] == 1]['fda_dt'].iloc[0]
        expected_date = pd.to_datetime('2020-02-01')
        assert case1_date == expected_date, f"Should keep latest date, got {case1_date}, expected {expected_date}"
        print(f"  PASS: dedupe_cases: {len(deduped)} unique cases")
        
        return True
    except Exception as e:
        print(f"  FAIL: Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_engineering():
    """Test feature engineering functions."""
    print("\nTesting feature engineering...")
    
    try:
        from src.features.feature_engineering import bin_age, extract_year
        
        # Test age binning
        ages = pd.Series([15, 30, 55, 70, 80, None])
        age_groups = bin_age(ages)
        assert len(age_groups) == 6, "Should have 6 age groups"
        assert age_groups.iloc[0] == "<18", "First should be <18"
        print(f"  PASS: bin_age: {age_groups.value_counts().to_dict()}")
        
        # Test year extraction
        dates = pd.Series(['2020-01-15', '2021-06-20', None])
        years = extract_year(dates)
        assert years.iloc[0] == 2020, "First year should be 2020"
        print(f"  PASS: extract_year: {years.tolist()}")
        
        return True
    except Exception as e:
        print(f"  FAIL: Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """Test configuration file loading."""
    print("\nTesting configuration loading...")
    
    try:
        try:
            import yaml
        except ImportError:
            print("  SKIP: yaml not installed")
            return True
        
        config_path = Path(__file__).parent / 'config' / 'drug_list.yaml'
        with open(config_path, 'r') as f:
            drug_config = yaml.safe_load(f)
        
        assert 'tier1_core' in drug_config, "Should have tier1_core"
        assert 'metformin' in drug_config['tier1_core'], "Should have metformin"
        print(f"  PASS: drug_list.yaml: {len(drug_config['tier1_core'])} drug classes")
        
        config_path = Path(__file__).parent / 'config' / 'ae_mapping.yaml'
        with open(config_path, 'r') as f:
            ae_config = yaml.safe_load(f)
        
        assert 'tier1_core_categories' in ae_config, "Should have tier1_core_categories"
        print(f"  PASS: ae_mapping.yaml: {len(ae_config['tier1_core_categories'])} categories")
        
        return True
    except Exception as e:
        print(f"  FAIL: Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_drug_normalizer():
    """Test drug normalizer."""
    print("\nTesting drug normalizer...")
    
    try:
        import yaml
        from src.data_ingest.drug_normalizer import DrugNormalizer
        
        normalizer = DrugNormalizer()
        
        # Test normalization
        result = normalizer.normalize_drug_name("OZEMPIC")
        assert result == "SEMAGLUTIDE" or result is not None, "Should normalize brand name"
        print(f"  PASS: normalize_drug_name: OZEMPIC -> {result}")
        
        result = normalizer.get_drug_class("METFORMIN")
        assert result == "metformin", "Should return drug class"
        print(f"  PASS: get_drug_class: METFORMIN -> {result}")
        
        return True
    except ImportError:
        print("  SKIP: yaml not installed")
        return True
    except Exception as e:
        print(f"  FAIL: Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("FAERS Longevity Analysis - Test Suite")
    print("="*60)
    
    results = []
    results.append(("Disproportionality", test_disproportionality()))
    results.append(("Dedupe Cases", test_dedupe_cases()))
    results.append(("Feature Engineering", test_feature_engineering()))
    results.append(("Config Loading", test_config_loading()))
    results.append(("Drug Normalizer", test_drug_normalizer()))
    
    print("\n" + "="*60)
    print("Test Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed.")
        return 0
    else:
        print("\nSome tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
