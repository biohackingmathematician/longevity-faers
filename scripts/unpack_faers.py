"""Unpack and standardize FAERS zip files."""

import zipfile
import yaml
from pathlib import Path
import shutil
from typing import List
import re


def unpack_quarter(quarter: str, zip_dir: Path, output_dir: Path) -> bool:
    """
    Unpack a single FAERS quarter zip file.
    
    Args:
        quarter: Quarter identifier (e.g., '2019Q1')
        zip_dir: Directory containing zip files
        output_dir: Directory to extract files
        
    Returns:
        True if successful, False otherwise
    """
    zip_path = zip_dir / f"faers_{quarter}.zip"
    
    if not zip_path.exists():
        print(f"Zip file not found: {zip_path}")
        return False
    
    quarter_output = output_dir / quarter.lower()
    quarter_output.mkdir(parents=True, exist_ok=True)
    
    print(f"Unpacking {quarter}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in zip
            file_list = zip_ref.namelist()
            
            # Extract and rename files
            for file_info in zip_ref.infolist():
                filename = file_info.filename
                
                # Skip directories
                if filename.endswith('/'):
                    continue
                
                # Extract file
                extracted_path = zip_ref.extract(filename, quarter_output)
                
                # Standardize filename
                # FAERS files may be named: DEMO19Q1.txt, demo19q1.txt, etc.
                base_name = Path(filename).stem.upper()
                ext = Path(filename).suffix
                
                # Map to standard names
                table_map = {
                    'DEMO': 'demo',
                    'DRUG': 'drug',
                    'REAC': 'reac',
                    'OUTC': 'outc',
                    'THER': 'ther',
                    'RPSR': 'rpsr',
                    'INDI': 'indi'
                }
                
                # Extract table name and quarter from filename
                for old_name, new_name in table_map.items():
                    if old_name in base_name:
                        # Standardize to: demo_2019q1.txt
                        new_filename = f"{new_name}_{quarter.lower()}{ext}"
                        new_path = quarter_output / new_filename
                        
                        # Rename if different
                        if extracted_path != str(new_path):
                            if new_path.exists():
                                new_path.unlink()
                            Path(extracted_path).rename(new_path)
                        
                        break
        
        print(f"Successfully unpacked {quarter}")
        return True
        
    except Exception as e:
        print(f"Error unpacking {quarter}: {e}")
        return False


def unpack_faers_data(config_path: str = None):
    """
    Unpack all FAERS zip files.
    
    Args:
        config_path: Path to data_config.yaml
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "data_config.yaml"
    else:
        config_path = Path(config_path)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    quarters = config['quarters']
    zip_dir = Path(config['data_paths']['raw_zips'])
    output_dir = Path(config['data_paths']['raw_unpacked'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Unpacking FAERS data for {len(quarters)} quarters...")
    print(f"Zip directory: {zip_dir}")
    print(f"Output directory: {output_dir}")
    
    successful = 0
    failed = []
    
    for i, quarter in enumerate(quarters, 1):
        print(f"\n[{i}/{len(quarters)}] Processing {quarter}...")
        
        if unpack_quarter(quarter, zip_dir, output_dir):
            successful += 1
        else:
            failed.append(quarter)
    
    print(f"\n{'='*60}")
    print(f"Unpacking complete: {successful}/{len(quarters)} successful")
    if failed:
        print(f"Failed quarters: {failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    unpack_faers_data()

