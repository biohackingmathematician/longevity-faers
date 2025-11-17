"""Load and combine FAERS tables."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict
import yaml


def load_faers_table(
    file_path: Path,
    delimiter: str = '$',
    encoding: str = 'latin-1',
    low_memory: bool = False
) -> pd.DataFrame:
    """
    Load a single FAERS table file.
    
    Args:
        file_path: Path to table file
        delimiter: Field delimiter (usually '$' or '|')
        encoding: File encoding
        low_memory: Whether to use low memory mode
        
    Returns:
        DataFrame with loaded data
    """
    try:
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            low_memory=low_memory,
            dtype=str  # Read all as strings initially to avoid type issues
        )
        return df
    except Exception as e:
        # Try pipe delimiter if $ fails
        if delimiter == '$':
            try:
                df = pd.read_csv(
                    file_path,
                    delimiter='|',
                    encoding=encoding,
                    low_memory=low_memory,
                    dtype=str
                )
                return df
            except:
                pass
        raise e


def load_quarter_tables(
    quarter: str,
    data_dir: Path,
    tables: List[str] = ['DEMO', 'DRUG', 'REAC']
) -> Dict[str, pd.DataFrame]:
    """
    Load all tables for a single quarter.
    
    Args:
        quarter: Quarter identifier (e.g., '2019Q1')
        data_dir: Base directory with unpacked FAERS data
        tables: List of table names to load
        
    Returns:
        Dictionary mapping table names to DataFrames
    """
    quarter_dir = data_dir / quarter.lower()
    
    if not quarter_dir.exists():
        raise FileNotFoundError(f"Quarter directory not found: {quarter_dir}")
    
    loaded_tables = {}
    
    for table in tables:
        # Try different filename patterns
        patterns = [
            f"{table.lower()}_{quarter.lower()}.txt",
            f"{table}_{quarter}.txt",
            f"{table.lower()}.txt",
            f"{table}.txt"
        ]
        
        file_path = None
        for pattern in patterns:
            candidate = quarter_dir / pattern
            if candidate.exists():
                file_path = candidate
                break
        
        if file_path is None:
            # List available files for debugging
            available = list(quarter_dir.glob("*.txt"))
            print(f"Warning: {table} not found for {quarter}. Available: {available[:5]}")
            continue
        
        try:
            df = load_faers_table(file_path)
            loaded_tables[table] = df
            print(f"Loaded {table} for {quarter}: {len(df)} rows")
        except Exception as e:
            print(f"Error loading {table} for {quarter}: {e}")
            continue
    
    return loaded_tables


def standardize_column_names(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """
    Standardize column names across different FAERS file versions.
    
    Args:
        df: DataFrame to standardize
        table_name: Name of table (DEMO, DRUG, REAC, etc.)
        
    Returns:
        DataFrame with standardized column names
    """
    df = df.copy()
    
    # Standardize caseid/primaryid
    if 'primaryid' in df.columns and 'caseid' not in df.columns:
        df = df.rename(columns={'primaryid': 'caseid'})
    elif 'isr' in df.columns and 'caseid' not in df.columns:
        df = df.rename(columns={'isr': 'caseid'})
    
    # Standardize date columns
    if 'init_fda_dt' in df.columns and 'fda_dt' not in df.columns:
        df = df.rename(columns={'init_fda_dt': 'fda_dt'})
    
    # Standardize drug columns
    if 'drugname' not in df.columns:
        for alt in ['drug', 'medicinalproduct']:
            if alt in df.columns:
                df = df.rename(columns={alt: 'drugname'})
                break
    
    if 'prod_ai' not in df.columns:
        for alt in ['prodai', 'active_substance_name']:
            if alt in df.columns:
                df = df.rename(columns={alt: 'prod_ai'})
                break
    
    # Standardize reaction columns
    if 'pt' not in df.columns:
        for alt in ['pt', 'reaction_pt', 'meddra_pt']:
            if alt in df.columns:
                df = df.rename(columns={alt: 'pt'})
                break
    
    return df


def combine_quarters(
    quarters: List[str],
    data_dir: Path,
    tables: List[str] = ['DEMO', 'DRUG', 'REAC'],
    standardize: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Load and combine tables across multiple quarters.
    
    Args:
        quarters: List of quarter identifiers
        data_dir: Base directory with unpacked FAERS data
        tables: List of table names to load
        standardize: Whether to standardize column names
        
    Returns:
        Dictionary mapping table names to combined DataFrames
    """
    combined = {table: [] for table in tables}
    
    for quarter in quarters:
        quarter_tables = load_quarter_tables(quarter, data_dir, tables)
        
        for table, df in quarter_tables.items():
            if standardize:
                df = standardize_column_names(df, table)
            
            # Add quarter identifier
            df['quarter'] = quarter
            
            combined[table].append(df)
    
    # Concatenate all quarters
    result = {}
    for table in tables:
        if combined[table]:
            result[table] = pd.concat(combined[table], ignore_index=True)
            print(f"Combined {table}: {len(result[table])} total rows")
        else:
            print(f"Warning: No data loaded for {table}")
            result[table] = pd.DataFrame()
    
    return result

