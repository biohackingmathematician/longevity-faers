"""Disproportionality analysis (ROR/PRR) for pharmacovigilance."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List


def compute_ror(
    a: int, b: int, c: int, d: int
) -> Tuple[float, float, float]:
    """
    Compute Reporting Odds Ratio (ROR) with 95% confidence interval.
    
    ROR = (a/b) / (c/d) = (a*d) / (b*c)
    
    Args:
        a: Reports with both drug and event
        b: Reports with drug, without event
        c: Reports with event, without drug
        d: Reports with neither drug nor event
        
    Returns:
        Tuple of (ROR, CI_lower, CI_upper)
    """
    # Avoid division by zero
    if b == 0 or c == 0:
        return (np.nan, np.nan, np.nan)
    
    if a == 0:
        return (0.0, 0.0, 0.0)
    
    # Compute ROR
    ror = (a * d) / (b * c) if (b * c) > 0 else np.nan
    
    # Compute standard error of log(ROR)
    se_log_ror = np.sqrt(1/a + 1/b + 1/c + 1/d)
    
    # 95% CI on log scale
    log_ror = np.log(ror)
    ci_lower = np.exp(log_ror - 1.96 * se_log_ror)
    ci_upper = np.exp(log_ror + 1.96 * se_log_ror)
    
    return (ror, ci_lower, ci_upper)


def compute_prr(
    a: int, b: int, c: int, d: int
) -> Tuple[float, float]:
    """
    Compute Proportional Reporting Ratio (PRR) with chi-square statistic.
    
    PRR = (a / (a+b)) / (c / (c+d))
    
    Args:
        a: Reports with both drug and event
        b: Reports with drug, without event
        c: Reports with event, without drug
        d: Reports with neither drug nor event
        
    Returns:
        Tuple of (PRR, chi2_statistic)
    """
    # Avoid division by zero
    if (a + b) == 0 or (c + d) == 0:
        return (np.nan, np.nan)
    
    if a == 0:
        return (0.0, 0.0)
    
    # Compute PRR
    prr = (a / (a + b)) / (c / (c + d))
    
    # Compute chi-square statistic
    # Expected values for 2x2 table
    n = a + b + c + d
    expected_a = (a + b) * (a + c) / n
    expected_b = (a + b) * (b + d) / n
    expected_c = (c + d) * (a + c) / n
    expected_d = (c + d) * (b + d) / n
    
    # Chi-square (with continuity correction)
    chi2 = (
        ((a - expected_a) ** 2) / expected_a +
        ((b - expected_b) ** 2) / expected_b +
        ((c - expected_c) ** 2) / expected_c +
        ((d - expected_d) ** 2) / expected_d
    )
    
    return (prr, chi2)


def build_contingency_table(
    df: pd.DataFrame,
    drug_col: str,
    drug_value: str,
    event_col: str,
    event_value: str
) -> Tuple[int, int, int, int]:
    """
    Build 2x2 contingency table for a drug-event pair.
    
    Args:
        df: DataFrame with drug and event information
        drug_col: Column name for drug identifier
        drug_value: Value to match for drug
        event_col: Column name for event identifier
        event_value: Value to match for event
        
    Returns:
        Tuple of (a, b, c, d) counts
    """
    # a: drug+ and event+
    a = len(df[(df[drug_col] == drug_value) & (df[event_col] == event_value)])
    
    # b: drug+ and event- (exclude NaN)
    b = len(df[(df[drug_col] == drug_value) & (df[event_col] != event_value) & (df[event_col].notna())])
    
    # c: drug- and event+ (exclude NaN)
    c = len(df[(df[drug_col] != drug_value) & (df[drug_col].notna()) & (df[event_col] == event_value)])
    
    # d: drug- and event- (exclude NaN)
    d = len(df[(df[drug_col] != drug_value) & (df[drug_col].notna()) & (df[event_col] != event_value) & (df[event_col].notna())])
    
    return (a, b, c, d)


def run_disproportionality_analysis(
    df: pd.DataFrame,
    drug_col: str,
    drug_list: List[str],
    event_col: str,
    event_list: List[str],
    min_count: int = 5,
    min_drug_reports: int = 10
) -> pd.DataFrame:
    """
    Run disproportionality analysis for all drug-event pairs.
    
    Args:
        df: DataFrame with drug and event information
        drug_col: Column name for drug identifier
        drug_list: List of drugs to analyze
        event_col: Column name for event identifier
        event_list: List of events to analyze
        min_count: Minimum a value (drug+event co-occurrences)
        min_drug_reports: Minimum total reports with drug (a + b)
        
    Returns:
        DataFrame with ROR, PRR, and statistics for each drug-event pair
    """
    results = []
    
    for drug in drug_list:
        # Filter to cases with this drug
        drug_cases = df[df[drug_col] == drug]
        
        # Check minimum drug reports
        if len(drug_cases) < min_drug_reports:
            continue
        
        for event in event_list:
            # Build contingency table
            a, b, c, d = build_contingency_table(
                df, drug_col, drug, event_col, event
            )
            
            # Apply minimum thresholds
            if a < min_count:
                continue
            
            if (a + b) < min_drug_reports:
                continue
            
            # Compute metrics
            ror, ror_ci_low, ror_ci_high = compute_ror(a, b, c, d)
            prr, chi2 = compute_prr(a, b, c, d)
            
            # Determine if signal
            is_signal_ror = (ror > 2.0) and (ror_ci_low > 1.0)
            is_signal_prr = (prr > 2.0) and (chi2 > 4.0) and (a >= 3)
            is_signal = is_signal_ror or is_signal_prr
            
            results.append({
                'drug': drug,
                'event': event,
                'a': a,
                'b': b,
                'c': c,
                'd': d,
                'ror': ror,
                'ror_ci_low': ror_ci_low,
                'ror_ci_high': ror_ci_high,
                'prr': prr,
                'chi2': chi2,
                'is_signal': is_signal
            })
    
    results_df = pd.DataFrame(results)
    
    # Sort by ROR descending
    if len(results_df) > 0:
        results_df = results_df.sort_values('ror', ascending=False)
    
    return results_df


def run_stratified_analysis(
    df: pd.DataFrame,
    drug_col: str,
    drug_list: List[str],
    event_col: str,
    event_list: List[str],
    stratify_col: str,
    min_count: int = 3,  # Lower threshold for stratified (smaller groups)
    min_drug_reports: int = 5
) -> pd.DataFrame:
    """
    Run disproportionality analysis stratified by a categorical variable.
    
    Args:
        df: DataFrame with drug and event information
        drug_col: Column name for drug identifier
        drug_list: List of drugs to analyze
        event_col: Column name for event identifier
        event_list: List of events to analyze
        stratify_col: Column to stratify by (e.g., 'age_group', 'sex')
        min_count: Minimum a value (lower for stratified)
        min_drug_reports: Minimum total reports with drug
        
    Returns:
        DataFrame with stratified results
    """
    results = []
    
    for stratum in df[stratify_col].dropna().unique():
        stratum_df = df[df[stratify_col] == stratum]
        
        stratum_results = run_disproportionality_analysis(
            stratum_df,
            drug_col,
            drug_list,
            event_col,
            event_list,
            min_count=min_count,
            min_drug_reports=min_drug_reports
        )
        
        if len(stratum_results) > 0:
            stratum_results[stratify_col] = stratum
            results.append(stratum_results)
    
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame()

