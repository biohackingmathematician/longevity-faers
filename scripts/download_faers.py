"""Download FAERS quarterly data files."""

import requests
import yaml
from pathlib import Path
import time
from typing import List
import zipfile
import io


def get_faers_url(quarter: str) -> str:
    """
    Construct FAERS download URL for a quarter.
    
    Note: FAERS URL structure varies. This is a template that may need adjustment.
    Actual URLs can be found at: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
    
    Args:
        quarter: Quarter identifier (e.g., '2019Q1')
        
    Returns:
        URL string
    """
    year = quarter[:4]
    q = quarter[-1].lower()
    
    # FAERS files are typically named like: faers_ascii_2019Q1.zip
    # But the actual URL structure may vary - check the FDA website
    base_url = "https://fis.fda.gov/content/Exports"
    
    # Try common patterns
    patterns = [
        f"{base_url}/faers_ascii_{quarter}.zip",
        f"{base_url}/faers_ascii_{year}q{q}.zip",
        f"{base_url}/faers_json_{quarter}.zip",
    ]
    
    return patterns[0]  # Return first pattern, user may need to adjust


def download_quarter(quarter: str, output_dir: Path, max_retries: int = 3) -> bool:
    """
    Download a single FAERS quarter.
    
    Args:
        quarter: Quarter identifier
        output_dir: Directory to save zip file
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if successful, False otherwise
    """
    url = get_faers_url(quarter)
    output_path = output_dir / f"faers_{quarter}.zip"
    
    # Skip if already exists
    if output_path.exists():
        print(f"Already exists: {output_path}")
        return True
    
    print(f"Downloading {quarter} from {url}...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=300, stream=True)
            response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Successfully downloaded {quarter} ({output_path.stat().st_size / 1e6:.1f} MB)")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {quarter}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                print(f"Failed to download {quarter} after {max_retries} attempts")
                return False
    
    return False


def download_faers_data(config_path: str = None):
    """
    Download FAERS data for all quarters specified in config.
    
    Args:
        config_path: Path to data_config.yaml (default: config/data_config.yaml)
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "data_config.yaml"
    else:
        config_path = Path(config_path)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    quarters = config['quarters']
    output_dir = Path(config['data_paths']['raw_zips'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading FAERS data for {len(quarters)} quarters...")
    print(f"Output directory: {output_dir}")
    
    successful = 0
    failed = []
    
    for i, quarter in enumerate(quarters, 1):
        print(f"\n[{i}/{len(quarters)}] Processing {quarter}...")
        
        if download_quarter(quarter, output_dir):
            successful += 1
        else:
            failed.append(quarter)
        
        # Be nice to the server
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"Download complete: {successful}/{len(quarters)} successful")
    if failed:
        print(f"Failed quarters: {failed}")
        print("\nNote: You may need to manually download these from:")
        print("https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html")
    print(f"{'='*60}")


if __name__ == "__main__":
    download_faers_data()

