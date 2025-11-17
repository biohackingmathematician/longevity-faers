"""Drug name normalization and matching utilities."""

import re
from typing import List, Dict, Set, Optional
import yaml
import pandas as pd
from pathlib import Path
try:
    from difflib import SequenceMatcher
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


class DrugNormalizer:
    """Normalize drug names from FAERS to standardized drug classes."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize drug normalizer with configuration.
        
        Args:
            config_path: Path to drug_list.yaml. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "drug_list.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Build mapping dictionaries
        self._build_mappings()
    
    def _build_mappings(self):
        """Build internal mappings for fast lookup."""
        self.brand_to_generic: Dict[str, str] = {}
        self.generic_to_class: Dict[str, str] = {}
        self.all_drug_names: Set[str] = set()
        self.target_drugs: Set[str] = set()
        
        # Process Tier 1 drugs
        for drug_key, drug_info in self.config['tier1_core'].items():
            drug_class = drug_info['drug_class']
            
            # Map generics
            generics = drug_info.get('generic', [])
            if isinstance(generics, str):
                generics = [generics]
            for generic in generics:
                generic_upper = generic.upper().strip()
                self.generic_to_class[generic_upper] = drug_class
                self.all_drug_names.add(generic_upper)
                self.target_drugs.add(generic_upper)
            
            # Map brands to generics
            for brand in drug_info.get('brands', []):
                brand_upper = brand.upper().strip()
                self.brand_to_generic[brand_upper] = generics[0] if generics else None
                self.all_drug_names.add(brand_upper)
            
            # Map active ingredients
            for ai in drug_info.get('active_ingredients', []):
                ai_upper = ai.upper().strip()
                self.generic_to_class[ai_upper] = drug_class
                self.all_drug_names.add(ai_upper)
                self.target_drugs.add(ai_upper)
        
        # Add target drugs from config
        for drug in self.config.get('target_drugs', []):
            self.target_drugs.add(drug.upper().strip())
    
    def normalize_drug_name(self, drug_name: str) -> Optional[str]:
        """
        Normalize a drug name to its generic form.
        
        Args:
            drug_name: Raw drug name from FAERS
            
        Returns:
            Normalized generic name, or None if not found
        """
        if not drug_name or pd.isna(drug_name):
            return None
        
        drug_upper = str(drug_name).upper().strip()
        
        # Direct match
        if drug_upper in self.generic_to_class:
            return drug_upper
        
        # Brand name match
        if drug_upper in self.brand_to_generic:
            return self.brand_to_generic[drug_upper]
        
        # Fuzzy matching for common misspellings/variations
        # Remove common suffixes/prefixes
        cleaned = re.sub(r'\s+(HCL|HYDROCHLORIDE|CALCIUM|SODIUM|POTASSIUM)$', '', drug_upper)
        if cleaned in self.generic_to_class:
            return cleaned
        
        # Check if contains target drug name
        for target in self.target_drugs:
            if target in drug_upper or drug_upper in target:
                return target
        
        # Fuzzy matching for misspellings (Phase 2 enhancement)
        if FUZZY_AVAILABLE:
            best_match = self._fuzzy_match(drug_upper, threshold=0.85)
            if best_match:
                return best_match
        
        return None
    
    def _fuzzy_match(self, drug_name: str, threshold: float = 0.85) -> Optional[str]:
        """
        Fuzzy match drug name to handle misspellings.
        
        Args:
            drug_name: Drug name to match
            threshold: Similarity threshold (0-1)
            
        Returns:
            Matched drug name or None
        """
        if not FUZZY_AVAILABLE:
            return None
        
        best_match = None
        best_ratio = 0.0
        
        for target in self.target_drugs:
            ratio = SequenceMatcher(None, drug_name, target).ratio()
            if ratio >= threshold and ratio > best_ratio:
                best_ratio = ratio
                best_match = target
        
        return best_match
    
    def get_drug_class(self, drug_name: str) -> Optional[str]:
        """
        Get drug class for a normalized drug name.
        
        Args:
            drug_name: Normalized drug name
            
        Returns:
            Drug class (metformin, glp1, statin, sglt2) or None
        """
        if not drug_name:
            return None
        
        drug_upper = str(drug_name).upper().strip()
        return self.generic_to_class.get(drug_upper)
    
    def is_target_drug(self, drug_name: str, use_fuzzy: bool = True) -> bool:
        """
        Check if a drug name matches any target drug.
        
        Args:
            drug_name: Drug name to check
            use_fuzzy: Whether to use fuzzy matching
            
        Returns:
            True if matches a target drug
        """
        if not drug_name:
            return False
        
        normalized = self.normalize_drug_name(drug_name) if use_fuzzy else None
        
        if normalized:
            return normalized in self.target_drugs
        
        drug_upper = str(drug_name).upper().strip()
        return drug_upper in self.target_drugs
    
    def normalize_and_classify(self, drug_name: str, prod_ai: Optional[str] = None) -> Dict[str, Optional[str]]:
        """
        Normalize drug name and return both normalized name and class.
        
        Args:
            drug_name: Raw drug name
            prod_ai: Active ingredient field (preferred if available)
            
        Returns:
            Dict with 'normalized_name' and 'drug_class'
        """
        # Prefer prod_ai if available (cleaner)
        name_to_check = prod_ai if prod_ai and not pd.isna(prod_ai) else drug_name
        
        normalized = self.normalize_drug_name(name_to_check)
        
        if normalized:
            drug_class = self.get_drug_class(normalized)
            return {
                'normalized_name': normalized,
                'drug_class': drug_class
            }
        
        return {
            'normalized_name': None,
            'drug_class': None
        }

