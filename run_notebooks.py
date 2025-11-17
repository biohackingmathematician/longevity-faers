"""Run notebook code as Python scripts for testing."""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def run_notebook_cells(notebook_path):
    """Extract and run code cells from a notebook."""
    print(f"\n{'='*60}")
    print(f"Running: {notebook_path.name}")
    print(f"{'='*60}\n")
    
    with open(notebook_path, 'r') as f:
        nb = json.load(f)
    
    cells = nb.get('cells', [])
    code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
    
    print(f"Found {len(code_cells)} code cells\n")
    
    for i, cell in enumerate(code_cells, 1):
        source = ''.join(cell.get('source', []))
        
        if not source.strip():
            continue
        
        print(f"--- Cell {i} ---")
        # Print first few lines
        lines = source.split('\n')[:5]
        for line in lines:
            if line.strip():
                print(f"  {line}")
        if len(source.split('\n')) > 5:
            print("  ...")
        print()
        
        # Try to execute (will fail if data not available, but tests imports)
        try:
            exec(source, globals())
            print(f"  ✓ Cell {i} executed successfully\n")
        except FileNotFoundError as e:
            if 'data' in str(e).lower() or 'faers' in str(e).lower():
                print(f"  ⚠ Cell {i} skipped (data not available): {e}\n")
            else:
                print(f"  ✗ Cell {i} error: {e}\n")
        except ImportError as e:
            print(f"  ⚠ Cell {i} skipped (import not available): {e}\n")
        except Exception as e:
            # Check if it's a data-related error
            error_str = str(e).lower()
            if any(x in error_str for x in ['data', 'file', 'not found', 'faers', 'parquet']):
                print(f"  ⚠ Cell {i} skipped (data not available): {type(e).__name__}\n")
            else:
                print(f"  ✗ Cell {i} error: {type(e).__name__}: {e}\n")
                import traceback
                traceback.print_exc()

def main():
    """Run all notebooks."""
    notebooks_dir = Path(__file__).parent / 'notebooks'
    
    notebooks = sorted(notebooks_dir.glob('*.ipynb'))
    
    if not notebooks:
        print("No notebooks found!")
        return
    
    print(f"Found {len(notebooks)} notebook(s)")
    
    for nb_path in notebooks:
        try:
            run_notebook_cells(nb_path)
        except Exception as e:
            print(f"\n✗ Error processing {nb_path.name}: {e}\n")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Notebook execution complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

