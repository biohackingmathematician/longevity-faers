"""Build analysis-ready datasets from FAERS data."""

import pandas as pd
import yaml
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_ingest.load_faers import combine_quarters, standardize_column_names
from src.data_ingest.dedupe_cases import dedupe_cases, get_latest_caseids
from src.data_ingest.drug_normalizer import DrugNormalizer
from src.features.ae_category_mapper import AECategoryMapper
from src.features.feature_engineering import create_ml_features


def build_disproportionality_dataset(
    demo_df: pd.DataFrame,
    drug_df: pd.DataFrame,
    reac_df: pd.DataFrame,
    drug_normalizer: DrugNormalizer,
    ae_mapper: AECategoryMapper,
    config: dict
) -> pd.DataFrame:
    """
    Build dataset for disproportionality analysis.
    
    Creates drug-event pairs with counts for contingency tables.
    
    Args:
        demo_df: Demographics dataframe (deduplicated)
        drug_df: Drug dataframe
        reac_df: Reactions dataframe
        drug_normalizer: Drug normalizer instance
        ae_mapper: AE category mapper instance
        config: Configuration dictionary
        
    Returns:
        DataFrame with drug-AE category pairs and counts
    """
    # Filter to target drugs
    suspect_roles = config.get('suspect_roles', ['PS', 'SS'])
    role_col = 'role_cod' if 'role_cod' in drug_df.columns else 'role'
    if role_col in drug_df.columns:
        drug_df_filtered = drug_df[drug_df[role_col].isin(suspect_roles)].copy()
    else:
        # If no role column, assume all are suspect
        drug_df_filtered = drug_df.copy()
    
    # Normalize drug names
    drugname_col = 'drugname' if 'drugname' in drug_df_filtered.columns else 'drug'
    prod_ai_col = 'prod_ai' if 'prod_ai' in drug_df_filtered.columns else None
    
    drug_info = drug_df_filtered.apply(
        lambda row: drug_normalizer.normalize_and_classify(
            row.get(drugname_col, '') if drugname_col in row.index else '',
            row.get(prod_ai_col, '') if prod_ai_col and prod_ai_col in row.index else None
        ),
        axis=1
    )
    drug_df_filtered['normalized_name'] = drug_info.apply(lambda x: x['normalized_name'])
    drug_df_filtered['drug_class'] = drug_info.apply(lambda x: x['drug_class'])
    
    # Filter to only target drugs
    drug_df_filtered = drug_df_filtered[drug_df_filtered['normalized_name'].notna()].copy()
    
    # Map reactions to categories
    reac_df_mapped = ae_mapper.map_case_reactions(reac_df)
    
    # Merge: cases -> drugs -> reactions
    # First, get cases with target drugs
    case_drugs = drug_df_filtered[['caseid', 'normalized_name', 'drug_class']].drop_duplicates()
    
    # Merge with reactions
    case_drug_reac = case_drugs.merge(
        reac_df_mapped[['caseid', 'ae_category']].dropna(),
        on='caseid',
        how='inner'
    )
    
    # Add demographics for stratification
    case_drug_reac = case_drug_reac.merge(
        demo_df[['caseid', 'age', 'sex']],
        on='caseid',
        how='left'
    )
    
    return case_drug_reac


def build_ml_dataset(
    demo_df: pd.DataFrame,
    drug_df: pd.DataFrame,
    reac_df: pd.DataFrame,
    drug_normalizer: DrugNormalizer,
    ae_mapper: AECategoryMapper,
    config: dict
) -> pd.DataFrame:
    """
    Build dataset for ML models.
    
    Creates case-level features with multi-label targets.
    
    Args:
        demo_df: Demographics dataframe (deduplicated)
        drug_df: Drug dataframe
        reac_df: Reactions dataframe
        drug_normalizer: Drug normalizer instance
        ae_mapper: AE category mapper instance
        config: Configuration dictionary
        
    Returns:
        DataFrame with features and labels
    """
    # Normalize all drugs (not just suspects, for polypharmacy features)
    drugname_col = 'drugname' if 'drugname' in drug_df.columns else 'drug'
    prod_ai_col = 'prod_ai' if 'prod_ai' in drug_df.columns else None
    
    drug_info = drug_df.apply(
        lambda row: drug_normalizer.normalize_and_classify(
            row.get(drugname_col, '') if drugname_col in row.index else '',
            row.get(prod_ai_col, '') if prod_ai_col and prod_ai_col in row.index else None
        ),
        axis=1
    )
    drug_df['normalized_name'] = drug_info.apply(lambda x: x['normalized_name'])
    drug_df['drug_class'] = drug_info.apply(lambda x: x['drug_class'])
    
    # Filter to target drugs for suspect roles
    suspect_roles = config.get('suspect_roles', ['PS', 'SS'])
    role_col = 'role_cod' if 'role_cod' in drug_df.columns else 'role'
    if role_col in drug_df.columns:
        target_drugs = drug_df[
            (drug_df[role_col].isin(suspect_roles)) &
            (drug_df['normalized_name'].notna())
        ].copy()
    else:
        # If no role column, filter only by normalized_name
        target_drugs = drug_df[drug_df['normalized_name'].notna()].copy()
    
    # Map reactions
    reac_df_mapped = ae_mapper.map_case_reactions(reac_df)
    
    # Get analysis categories
    ae_categories = ae_mapper.get_analysis_categories()
    
    # Create ML features
    ml_df = create_ml_features(
        demo_df,
        drug_df,  # Use full drug_df for polypharmacy
        reac_df_mapped,
        ae_categories
    )
    
    # Filter to only cases with target drugs
    target_caseids = target_drugs['caseid'].unique()
    ml_df = ml_df[ml_df['caseid'].isin(target_caseids)].copy()
    
    return ml_df


def main():
    """Main function to build datasets."""
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "data_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Paths
    data_dir = Path(config['data_paths']['raw_unpacked'])
    interim_dir = Path(config['data_paths']['interim'])
    processed_dir = Path(config['data_paths']['processed'])
    
    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    quarters = config['quarters']
    
    print("="*60)
    print("Building FAERS Analysis Datasets")
    print("="*60)
    
    # Step 1: Load and combine all quarters
    print("\nStep 1: Loading FAERS tables...")
    tables = combine_quarters(quarters, data_dir, tables=['DEMO', 'DRUG', 'REAC'])
    
    demo_all = tables['DEMO']
    drug_all = tables['DRUG']
    reac_all = tables['REAC']
    
    # Save interim files
    print("\nSaving interim files...")
    try:
        demo_all.to_parquet(interim_dir / "demo_all.parquet")
        drug_all.to_parquet(interim_dir / "drug_all.parquet")
        reac_all.to_parquet(interim_dir / "reac_all.parquet")
        print("Saved interim files as parquet")
    except ImportError:
        # Fallback to CSV if parquet not available
        print("Parquet not available, saving as CSV...")
        demo_all.to_csv(interim_dir / "demo_all.csv", index=False)
        drug_all.to_csv(interim_dir / "drug_all.csv", index=False)
        reac_all.to_csv(interim_dir / "reac_all.csv", index=False)
        print("Saved interim files as CSV")
    
    # Step 2: Deduplicate cases
    print("\nStep 2: Deduplicating cases...")
    demo_deduped = dedupe_cases(demo_all)
    latest_caseids = get_latest_caseids(demo_all)
    
    # Filter other tables to latest cases
    drug_all = drug_all[drug_all['caseid'].isin(latest_caseids)].copy()
    reac_all = reac_all[reac_all['caseid'].isin(latest_caseids)].copy()
    
    print(f"After deduplication: {len(demo_deduped)} cases")
    
    # Step 3: Initialize normalizers
    print("\nStep 3: Initializing drug normalizer and AE mapper...")
    drug_normalizer = DrugNormalizer()
    ae_mapper = AECategoryMapper()
    
    # Step 4: Build disproportionality dataset
    print("\nStep 4: Building disproportionality dataset...")
    dispro_df = build_disproportionality_dataset(
        demo_deduped,
        drug_all,
        reac_all,
        drug_normalizer,
        ae_mapper,
        config
    )
    
    # Aggregate to drug-AE category counts
    dispro_agg = dispro_df.groupby([
        'normalized_name', 'drug_class', 'ae_category'
    ]).size().reset_index(name='count')
    
    try:
        dispro_agg.to_parquet(processed_dir / "drug_ae_counts.parquet")
        print(f"Saved: {processed_dir / 'drug_ae_counts.parquet'}")
    except ImportError:
        dispro_agg.to_csv(processed_dir / "drug_ae_counts.csv", index=False)
        print(f"Saved: {processed_dir / 'drug_ae_counts.csv'}")
    print(f"  Shape: {dispro_agg.shape}")
    
    # Step 5: Build ML dataset
    print("\nStep 5: Building ML dataset...")
    ml_df = build_ml_dataset(
        demo_deduped,
        drug_all,
        reac_all,
        drug_normalizer,
        ae_mapper,
        config
    )
    
    try:
        ml_df.to_parquet(processed_dir / "cases_ml.parquet")
        print(f"Saved: {processed_dir / 'cases_ml.parquet'}")
    except ImportError:
        ml_df.to_csv(processed_dir / "cases_ml.csv", index=False)
        print(f"Saved: {processed_dir / 'cases_ml.csv'}")
    print(f"  Shape: {ml_df.shape}")
    
    print("\n" + "="*60)
    print("Dataset building complete!")
    print("="*60)


if __name__ == "__main__":
    main()

