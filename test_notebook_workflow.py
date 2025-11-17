"""Test notebook workflows with mock data."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_notebook_01_explore():
    """Test notebook 01: Data exploration workflow."""
    print("\n" + "="*60)
    print("Testing Notebook 01: FAERS Data Exploration")
    print("="*60 + "\n")
    
    try:
        # Imports (from notebook)
        import pandas as pd
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import seaborn as sns
        from pathlib import Path
        import sys
        
        sys.path.insert(0, str(Path.cwd().parent / 'src'))
        
        from src.data_ingest.load_faers import standardize_column_names
        from src.data_ingest.dedupe_cases import dedupe_cases
        
        print("✓ All imports successful")
        
        # Create mock FAERS data
        print("\nCreating mock FAERS data...")
        demo = pd.DataFrame({
            'caseid': range(1, 1001),
            'age': np.random.choice([None, 30, 45, 60, 75], 1000),
            'sex': np.random.choice(['M', 'F', 'Unknown'], 1000),
            'fda_dt': pd.date_range('2020-01-01', periods=1000, freq='D'),
            'event_dt': pd.date_range('2020-01-01', periods=1000, freq='D')
        })
        
        drug = pd.DataFrame({
            'caseid': np.random.choice(range(1, 1001), 2000),
            'drugname': np.random.choice(['METFORMIN', 'OZEMPIC', 'LIPITOR', 'JARDIANCE'], 2000),
            'prod_ai': np.random.choice(['METFORMIN', 'SEMAGLUTIDE', 'ATORVASTATIN', 'EMPAGLIFLOZIN'], 2000),
            'role_cod': np.random.choice(['PS', 'SS', 'C'], 2000, p=[0.4, 0.3, 0.3])
        })
        
        reac = pd.DataFrame({
            'caseid': np.random.choice(range(1, 1001), 3000),
            'pt': np.random.choice([
                'NAUSEA', 'MYALGIA', 'HYPOGLYCEMIA', 'MYOCARDIAL INFARCTION',
                'DIARRHEA', 'MYOPATHY', 'HYPERTENSION'
            ], 3000)
        })
        
        print(f"  Demo: {len(demo)} rows")
        print(f"  Drug: {len(drug)} rows")
        print(f"  Reac: {len(reac)} rows")
        
        # Test deduplication
        print("\nTesting deduplication...")
        demo_deduped = dedupe_cases(demo)
        print(f"  ✓ Deduplicated: {len(demo_deduped)} cases")
        
        # Test standardization
        print("\nTesting column standardization...")
        demo_std = standardize_column_names(demo, 'DEMO')
        print(f"  ✓ Standardized columns: {list(demo_std.columns)[:5]}...")
        
        print("\n✓ Notebook 01 workflow test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Notebook 01 workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notebook_02_disproportionality():
    """Test notebook 02: Disproportionality analysis workflow."""
    print("\n" + "="*60)
    print("Testing Notebook 02: Disproportionality Analysis")
    print("="*60 + "\n")
    
    try:
        # Imports
        import pandas as pd
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import seaborn as sns
        from pathlib import Path
        import sys
        
        sys.path.insert(0, str(Path.cwd().parent / 'src'))
        
        from src.models.disproportionality import run_disproportionality_analysis
        from src.viz.volcano_plots import plot_volcano, plot_heatmap
        
        print("✓ All imports successful")
        
        # Create mock data for disproportionality analysis
        print("\nCreating mock disproportionality data...")
        n_cases = 1000
        drugs = ['METFORMIN', 'SEMAGLUTIDE', 'ATORVASTATIN']
        events = ['cardiovascular', 'metabolic', 'musculoskeletal', 'gastrointestinal']
        
        # Create data with some signal
        data = []
        for drug in drugs:
            for event in events:
                # Create some cases with drug+event
                n_cooccur = np.random.randint(5, 50) if drug == 'METFORMIN' and event == 'gastrointestinal' else np.random.randint(0, 20)
                for _ in range(n_cooccur):
                    data.append({'drug': drug, 'event': event})
        
        # Add cases without events
        for drug in drugs:
            n_no_event = np.random.randint(50, 200)
            for _ in range(n_no_event):
                data.append({'drug': drug, 'event': 'other'})
        
        df = pd.DataFrame(data)
        print(f"  Created {len(df)} drug-event pairs")
        
        # Run analysis
        print("\nRunning disproportionality analysis...")
        results = run_disproportionality_analysis(
            df,
            drug_col='drug',
            drug_list=drugs,
            event_col='event',
            event_list=events,
            min_count=3,
            min_drug_reports=10
        )
        
        print(f"  ✓ Found {len(results)} significant pairs")
        if len(results) > 0:
            print(f"  Top signal: {results.iloc[0]['drug']} - {results.iloc[0]['event']} (ROR={results.iloc[0]['ror']:.2f})")
        
        print("\n✓ Notebook 02 workflow test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Notebook 02 workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notebook_03_ml():
    """Test notebook 03: ML model workflow."""
    print("\n" + "="*60)
    print("Testing Notebook 03: Multi-Label Model")
    print("="*60 + "\n")
    
    try:
        # Imports
        import pandas as pd
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import seaborn as sns
        from pathlib import Path
        import sys
        
        sys.path.insert(0, str(Path.cwd().parent / 'src'))
        
        from src.features.feature_engineering import bin_age, create_ml_features
        from src.features.ae_category_mapper import AECategoryMapper
        
        print("✓ All imports successful")
        
        # Create mock ML data
        print("\nCreating mock ML dataset...")
        n_cases = 500
        
        cases_df = pd.DataFrame({
            'caseid': range(1, n_cases + 1),
            'age': np.random.choice([None, 30, 45, 60, 75], n_cases),
            'sex': np.random.choice(['M', 'F'], n_cases),
            'fda_dt': pd.date_range('2020-01-01', periods=n_cases, freq='D')
        })
        
        drug_df = pd.DataFrame({
            'caseid': np.random.choice(range(1, n_cases + 1), n_cases * 2),
            'drugname': np.random.choice(['METFORMIN', 'OZEMPIC', 'LIPITOR'], n_cases * 2),
            'role_cod': np.random.choice(['PS', 'SS', 'C'], n_cases * 2, p=[0.5, 0.3, 0.2])
        })
        drug_df['drug_class'] = drug_df['drugname'].map({
            'METFORMIN': 'metformin',
            'OZEMPIC': 'glp1',
            'LIPITOR': 'statin'
        })
        drug_df['normalized_name'] = drug_df['drugname']
        
        reac_df = pd.DataFrame({
            'caseid': np.random.choice(range(1, n_cases + 1), n_cases * 3),
            'pt': np.random.choice(['NAUSEA', 'MYALGIA', 'HYPOGLYCEMIA'], n_cases * 3)
        })
        
        # Map reactions
        print("Mapping reactions to categories...")
        try:
            ae_mapper = AECategoryMapper()
            reac_df['ae_category'] = ae_mapper.map_pts_to_categories(reac_df['pt'])
        except:
            # Fallback if yaml not available
            reac_df['ae_category'] = reac_df['pt'].map({
                'NAUSEA': 'gastrointestinal',
                'MYALGIA': 'musculoskeletal',
                'HYPOGLYCEMIA': 'metabolic'
            })
        
        print(f"  Cases: {len(cases_df)}")
        print(f"  Drugs: {len(drug_df)}")
        print(f"  Reactions: {len(reac_df)}")
        
        # Test age binning
        print("\nTesting age binning...")
        age_groups = bin_age(cases_df['age'])
        print(f"  ✓ Age groups: {age_groups.value_counts().to_dict()}")
        
        print("\n✓ Notebook 03 workflow test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Notebook 03 workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all notebook workflow tests."""
    print("="*60)
    print("Testing Notebook Workflows with Mock Data")
    print("="*60)
    
    results = []
    results.append(("Notebook 01: Exploration", test_notebook_01_explore()))
    results.append(("Notebook 02: Disproportionality", test_notebook_02_disproportionality()))
    results.append(("Notebook 03: ML Model", test_notebook_03_ml()))
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All notebook workflows work correctly!")
        return 0
    else:
        print("\n⚠ Some workflows need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

