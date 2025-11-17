"""Feature engineering for ML models."""

import pandas as pd
import numpy as np
from typing import List, Optional


def bin_age(age: pd.Series) -> pd.Series:
    """
    Bin age into categories.
    
    Args:
        age: Series of ages (numeric or string)
        
    Returns:
        Series of age group labels
    """
    # Convert to numeric, handling string ages
    age_numeric = pd.to_numeric(age, errors='coerce')
    
    def _bin_single(age_val):
        if pd.isna(age_val):
            return "Unknown"
        
        age_val = float(age_val)
        
        if age_val < 18:
            return "<18"
        elif age_val < 45:
            return "18-44"
        elif age_val < 65:
            return "45-64"
        elif age_val < 75:
            return "65-74"
        else:
            return "75+"
    
    return age_numeric.apply(_bin_single)


def extract_year(date_series: pd.Series) -> pd.Series:
    """
    Extract year from date series.
    
    Args:
        date_series: Series of dates (string or datetime)
        
    Returns:
        Series of years (int)
    """
    dates = pd.to_datetime(date_series, errors='coerce')
    years = dates.dt.year
    return years


def create_polypharmacy_features(
    drug_df: pd.DataFrame,
    caseid_col: str = 'caseid'
) -> pd.DataFrame:
    """
    Create polypharmacy features from drug dataframe.
    
    Args:
        drug_df: Drug dataframe with caseid and drug info
        caseid_col: Column name for case ID
        
    Returns:
        DataFrame with polypharmacy features per case
    """
    # Count total drugs per case
    drug_counts = drug_df.groupby(caseid_col).size().reset_index(name='n_drugs')
    
    # Count concomitant drugs (role = 'C')
    role_col = 'role_cod' if 'role_cod' in drug_df.columns else 'role'
    if role_col in drug_df.columns:
        concomitant = drug_df[drug_df[role_col] == 'C']
    else:
        concomitant = pd.DataFrame()
    if len(concomitant) > 0:
        concomitant_counts = concomitant.groupby(caseid_col).size().reset_index(name='n_concomitant_drugs')
    else:
        concomitant_counts = pd.DataFrame({caseid_col: [], 'n_concomitant_drugs': []})
    
    # Check for specific drug classes in concomitant
    # This is a simplified version - you'd expand this based on your needs
    cardio_keywords = ['LISINOPRIL', 'LOSARTAN', 'METOPROLOL', 'ATENOLOL', 'AMLODIPINE']
    insulin_keywords = ['INSULIN', 'LANTUS', 'NOVOLOG']
    
    def _has_keyword(drugs, keywords):
        drugs_str = ' '.join(str(d).upper() for d in drugs if pd.notna(d))
        return any(kw in drugs_str for kw in keywords)
    
    # Get drugname column (may be named differently)
    drugname_col = 'drugname' if 'drugname' in drug_df.columns else 'prod_ai' if 'prod_ai' in drug_df.columns else None
    if drugname_col:
        case_drugs = drug_df.groupby(caseid_col)[drugname_col].apply(list).reset_index()
        case_drugs.columns = [caseid_col, 'drugname']
    else:
        # Fallback: create empty list
        case_drugs = drug_df.groupby(caseid_col).size().reset_index()
        case_drugs['drugname'] = case_drugs.apply(lambda x: [], axis=1)
    
    case_drugs['has_cardio_comedication'] = case_drugs['drugname'].apply(
        lambda x: _has_keyword(x, cardio_keywords)
    )
    case_drugs['has_insulin'] = case_drugs['drugname'].apply(
        lambda x: _has_keyword(x, insulin_keywords)
    )
    
    # Merge all features
    features = drug_counts.merge(
        concomitant_counts,
        on=caseid_col,
        how='left'
    ).merge(
        case_drugs[['caseid', 'has_cardio_comedication', 'has_insulin']],
        on=caseid_col,
        how='left'
    )
    
    # Fill missing values
    features['n_concomitant_drugs'] = features['n_concomitant_drugs'].fillna(0)
    features['has_cardio_comedication'] = features['has_cardio_comedication'].fillna(False)
    features['has_insulin'] = features['has_insulin'].fillna(False)
    
    return features


def create_ml_features(
    cases_df: pd.DataFrame,
    drug_df: pd.DataFrame,
    reac_df: pd.DataFrame,
    ae_categories: List[str]
) -> pd.DataFrame:
    """
    Create feature matrix for ML models.
    
    Creates one row per case-drug combination with:
    - Demographic features (age_group, sex)
    - Drug features (drug_class)
    - Polypharmacy features (n_concomitant_drugs, etc.)
    - Temporal features (year)
    - Target labels (binary flags for each AE category)
    
    Args:
        cases_df: Cases dataframe (from DEMO, deduplicated)
        drug_df: Drug dataframe (filtered to target drugs)
        reac_df: Reactions dataframe (with ae_category mapped)
        ae_categories: List of AE categories to use as targets
        
    Returns:
        DataFrame with features and labels
    """
    # Start with cases
    features = cases_df[['caseid']].copy()
    
    # Add demographics
    if 'age' in cases_df.columns:
        features['age_group'] = bin_age(cases_df['age'])
        features['age_raw'] = pd.to_numeric(cases_df['age'], errors='coerce')
    else:
        features['age_group'] = 'Unknown'
        features['age_raw'] = np.nan
    
    if 'sex' in cases_df.columns:
        features['sex'] = cases_df['sex'].fillna('Unknown')
    else:
        features['sex'] = 'Unknown'
    
    # Add temporal features
    date_col = 'fda_dt' if 'fda_dt' in cases_df.columns else 'event_dt'
    if date_col in cases_df.columns:
        features['report_year'] = extract_year(cases_df[date_col])
    else:
        features['report_year'] = np.nan
    
    # Add drug information (one row per case-drug)
    # Filter to suspect drugs only
    role_col = 'role_cod' if 'role_cod' in drug_df.columns else 'role'
    if role_col in drug_df.columns:
        suspect_drugs = drug_df[drug_df[role_col].isin(['PS', 'SS'])].copy()
    else:
        # If no role column, use all drugs
        suspect_drugs = drug_df.copy()
    
    # Select available columns for merge
    merge_cols = ['caseid']
    if 'drug_class' in suspect_drugs.columns:
        merge_cols.append('drug_class')
    if 'normalized_name' in suspect_drugs.columns:
        merge_cols.append('normalized_name')
    
    # Merge with features
    case_drugs = suspect_drugs[merge_cols].merge(
        features,
        on='caseid',
        how='inner'
    )
    
    # Add drug_class if missing (set to 'unknown')
    if 'drug_class' not in case_drugs.columns:
        case_drugs['drug_class'] = 'unknown'
    
    # Add polypharmacy features
    polypharm = create_polypharmacy_features(drug_df)
    case_drugs = case_drugs.merge(
        polypharm,
        on='caseid',
        how='left'
    )
    
    # Fill missing polypharmacy
    case_drugs['n_drugs'] = case_drugs['n_drugs'].fillna(1)  # At least the suspect drug
    case_drugs['n_concomitant_drugs'] = case_drugs['n_concomitant_drugs'].fillna(0)
    case_drugs['has_cardio_comedication'] = case_drugs['has_cardio_comedication'].fillna(False)
    case_drugs['has_insulin'] = case_drugs['has_insulin'].fillna(False)
    
    # Create target labels (binary flags for each AE category)
    # Get reactions per case
    case_reactions = reac_df.groupby('caseid')['ae_category'].apply(set).reset_index()
    case_reactions.columns = ['caseid', 'ae_categories']
    
    # Merge with case_drugs
    case_drugs = case_drugs.merge(
        case_reactions,
        on='caseid',
        how='left'
    )
    
    # Create binary flags
    for category in ae_categories:
        case_drugs[category] = case_drugs['ae_categories'].apply(
            lambda cats: category in cats if isinstance(cats, set) else False
        ).astype(int)
    
    # Drop intermediate columns
    case_drugs = case_drugs.drop(columns=['ae_categories'], errors='ignore')
    
    return case_drugs

