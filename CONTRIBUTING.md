# Development Setup

## Environment

Requires Python 3.10+

### Option 1: pip

```bash
pip install -r requirements.txt
```

### Option 2: Poetry

```bash
poetry install
poetry shell
```

## Dependencies

- pandas / numpy (data wrangling)
- scikit-learn, xgboost (ML)
- matplotlib, seaborn, plotly (viz)
- pyyaml (config)
- requests (FAERS download)

## Running Tests

```bash
pytest tests/
```

## Code Style

- Black formatter: `black src/`
- Flake8 linter: `flake8 src/`

## Data

FAERS data is NOT included in repo (too large). Run `scripts/download_faers.py` to fetch.

## Workflow

1. Download FAERS data: `python scripts/download_faers.py`
2. Unpack data: `python scripts/unpack_faers.py`
3. Build datasets: `python scripts/build_dataset.py`
4. Run analysis: Use Jupyter notebooks in `notebooks/`

