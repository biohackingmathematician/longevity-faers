"""Enhanced demographics cleaning with age unit conversion."""

import pandas as pd
import numpy as np
from typing import Optional


def convert_age_to_years(row: pd.Series) -> float:
    """
    Convert FAERS age field to years.
    
    FAERS age can be in different units:
    - YR: Years (default)
    - DEC: Decades
    - MON: Months
    - DY: Days
    
    Args:
        row: DataFrame row with 'age' and optionally 'age_cod' or 'age_unit'
        
    Returns:
        Age in years, or NaN if invalid/missing
    """
    age = row.get('age')
    age_unit = row.get('age_cod', row.get('age_unit', 'YR')).upper()
    
    if pd.isna(age):
        return np.nan
    
    try:
        age = float(age)
        
        if age_unit == 'YR' or age_unit == '':
            return age
        elif age_unit == 'DEC':
            return age * 10
        elif age_unit == 'MON':
            return age / 12
        elif age_unit == 'DY':
            return age / 365
        else:
            # Unknown unit, assume years
            return age
    except (ValueError, TypeError):
        return np.nan


def clean_demographics(demo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize demographics data.
    
    Handles:
    - Age unit conversion (YR, MON, DEC, DY)
    - Age binning
    - Missing sex values
    - Invalid age values
    
    Args:
        demo_df: Demographics dataframe
        
    Returns:
        Cleaned dataframe with additional columns:
        - age_years: Age converted to years
        - age_group: Binned age categories
    """
    df = demo_df.copy()
    
    # Convert age to years
    if 'age' in df.columns:
        df['age_years'] = df.apply(convert_age_to_years, axis=1)
        
        # Remove invalid ages (negative, >150)
        df.loc[(df['age_years'] < 0) | (df['age_years'] > 150), 'age_years'] = np.nan
        
        # Age binning
        df['age_group'] = pd.cut(
            df['age_years'],
            bins=[0, 18, 45, 65, 75, 200],
            labels=['<18', '18-44', '45-64', '65-74', '75+'],
            include_lowest=True
        )
        df['age_group'] = df['age_group'].cat.add_categories(['Unknown'])
        df.loc[df['age_years'].isna(), 'age_group'] = 'Unknown'
    else:
        df['age_years'] = np.nan
        df['age_group'] = 'Unknown'
    
    # Clean sex field
    if 'sex' in df.columns:
        # Standardize sex values
        df['sex'] = df['sex'].str.upper().str.strip()
        df['sex'] = df['sex'].replace({
            '': 'UNK',
            'NS': 'UNK',
            'N': 'UNK',
            'U': 'UNK',
            None: 'UNK'
        })
        df['sex'] = df['sex'].fillna('UNK')
    else:
        df['sex'] = 'UNK'
    
    return df

