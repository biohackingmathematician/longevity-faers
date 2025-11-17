"""Map MedDRA Preferred Terms to adverse event categories."""

import re
from typing import Dict, List, Set, Optional
import yaml
from pathlib import Path
import pandas as pd


class AECategoryMapper:
    """Map MedDRA Preferred Terms to custom AE categories."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize mapper with configuration.
        
        Args:
            config_path: Path to ae_mapping.yaml. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "ae_mapping.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Build mapping structures
        self._build_mappings()
    
    def _build_mappings(self):
        """Build internal mappings for fast lookup."""
        self.exact_matches: Dict[str, str] = {}  # PT -> category
        self.keyword_patterns: Dict[str, List[re.Pattern]] = {}  # category -> patterns
        
        # Process all categories
        all_categories = {}
        all_categories.update(self.config.get('tier1_core_categories', {}))
        all_categories.update(self.config.get('tier2_extended_categories', {}))
        
        for category, rules in all_categories.items():
            # Exact matches
            for pt in rules.get('exact_matches', []):
                self.exact_matches[pt.upper()] = category
            
            # Keyword patterns
            patterns = []
            for keyword in rules.get('keywords', []):
                # Create case-insensitive pattern
                pattern = re.compile(rf'\b{re.escape(keyword.upper())}\b', re.IGNORECASE)
                patterns.append(pattern)
            
            self.keyword_patterns[category] = patterns
    
    def map_pt_to_category(self, pt: str) -> Optional[str]:
        """
        Map a MedDRA Preferred Term to an AE category.
        
        Args:
            pt: MedDRA Preferred Term
            
        Returns:
            AE category name, or None if no match
        """
        if not pt or pd.isna(pt):
            return None
        
        pt_upper = str(pt).upper().strip()
        
        # Check exact matches first (most reliable)
        if pt_upper in self.exact_matches:
            return self.exact_matches[pt_upper]
        
        # Check keyword patterns
        for category, patterns in self.keyword_patterns.items():
            for pattern in patterns:
                if pattern.search(pt_upper):
                    return category
        
        return None
    
    def map_pts_to_categories(self, pts: pd.Series) -> pd.Series:
        """
        Map a series of PTs to categories.
        
        Args:
            pts: Series of MedDRA Preferred Terms
            
        Returns:
            Series of AE categories
        """
        return pts.apply(self.map_pt_to_category)
    
    def get_analysis_categories(self) -> List[str]:
        """Get list of categories to use for analysis."""
        return self.config.get('analysis_categories', [
            'cardiovascular',
            'metabolic',
            'musculoskeletal',
            'gastrointestinal',
            'renal'
        ])
    
    def map_case_reactions(self, reac_df: pd.DataFrame) -> pd.DataFrame:
        """
        Map all reactions in a REAC dataframe to categories.
        
        Args:
            reac_df: REAC dataframe with 'pt' column
            
        Returns:
            DataFrame with added 'ae_category' column
        """
        reac_df = reac_df.copy()
        reac_df['ae_category'] = self.map_pts_to_categories(reac_df['pt'])
        return reac_df

