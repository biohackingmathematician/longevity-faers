"""Deduplicate FAERS cases (handle follow-up reports)."""

import pandas as pd
from typing import Optional


def dedupe_cases(
    demo_df: pd.DataFrame,
    date_col: str = 'fda_dt',
    caseid_col: str = 'caseid'
) -> pd.DataFrame:
    """
    Deduplicate cases by keeping the latest report per caseid.
    
    FAERS may have multiple reports for the same case (follow-ups).
    We keep the one with the latest fda_dt (FDA received date).
    
    Args:
        demo_df: Demographics dataframe
        date_col: Column name for date (fda_dt or event_dt)
        caseid_col: Column name for case ID (caseid or primaryid)
        
    Returns:
        Deduplicated dataframe
    """
    # Normalize column names (handle caseid vs primaryid)
    if caseid_col not in demo_df.columns:
        # Try alternative names
        if 'primaryid' in demo_df.columns:
            caseid_col = 'primaryid'
        elif 'isr' in demo_df.columns:
            caseid_col = 'isr'
        else:
            raise ValueError(f"Case ID column not found. Available: {demo_df.columns.tolist()}")
    
    # Convert date to datetime if not already
    if date_col in demo_df.columns:
        demo_df[date_col] = pd.to_datetime(demo_df[date_col], errors='coerce')
    else:
        # Try alternative date columns
        for alt_col in ['event_dt', 'init_fda_dt', 'foll_seq']:
            if alt_col in demo_df.columns:
                date_col = alt_col
                demo_df[date_col] = pd.to_datetime(demo_df[date_col], errors='coerce')
                break
    
    # Sort by caseid and date (descending)
    demo_df = demo_df.sort_values([caseid_col, date_col], ascending=[True, False])
    
    # Keep first row per caseid (latest date)
    deduped = demo_df.drop_duplicates(subset=[caseid_col], keep='first')
    
    return deduped.reset_index(drop=True)


def get_latest_caseids(
    demo_df: pd.DataFrame,
    date_col: str = 'fda_dt',
    caseid_col: str = 'caseid'
) -> pd.Series:
    """
    Get set of caseids to keep (latest report per case).
    
    Useful for filtering other tables (DRUG, REAC) before joining.
    
    Args:
        demo_df: Demographics dataframe
        date_col: Column name for date
        caseid_col: Column name for case ID
        
    Returns:
        Series of caseids to keep
    """
    deduped = dedupe_cases(demo_df, date_col, caseid_col)
    return deduped[caseid_col].unique()

