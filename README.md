# FAERS Longevity Drug Safety Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

Computational pharmacovigilance analysis of "longevity-relevant" drugs using FDA Adverse Event Reporting System (FAERS). This project focuses on four drug classes with emerging evidence in healthspan/lifespan extension:

- **Metformin** (glucose regulation, potential anti-aging effects)
- **GLP-1 receptor agonists** (weight management, cardiovascular protection)
- **SGLT2 inhibitors** (cardiorenal benefits)
- **Statins** (lipid management, pleiotropic effects)

**Key Goal:** Characterize safety profiles with rigorous disproportionality analysis and modern ML, emphasizing adverse events relevant to longevity, cardiovascular health, and physical performance.

## Research Questions

1. Which adverse event categories (cardiovascular, metabolic, musculoskeletal, GI, renal) are disproportionately reported for each drug?
2. How do safety profiles differ across these drug classes?
3. Do patient factors (age, sex, polypharmacy) modify adverse event patterns?

## Key Features

- Rigorous disproportionality analysis (ROR/PRR with confidence intervals)
- Multi-label ML models (XGBoost) for AE prediction
- Performance-aware narrative (musculoskeletal, cardiovascular, metabolic AEs)
- Reproducible pipeline with full documentation

## Critical Limitations

⚠️ **FAERS is a spontaneous reporting system:**

- No exposure denominator → cannot calculate incidence rates
- Reporting bias → serious AEs over-represented
- **This is signal detection, NOT causal inference**
- **Not medical advice**

This is an analytical exercise in pharmacovigilance methods, not medical advice.

## Installation

```bash
git clone https://github.com/yourusername/faers-longevity-analysis.git
cd faers-longevity-analysis
pip install -r requirements.txt
```

Or with Poetry:

```bash
poetry install
poetry shell
```

## Usage

```bash
# 1. Download FAERS data (2019-2024)
python scripts/download_faers.py

# 2. Unpack and standardize data
python scripts/unpack_faers.py

# 3. Process and clean data
python scripts/build_dataset.py

# 4. Run analysis (or use notebooks)
jupyter notebook notebooks/02_disproportionality.ipynb
```

## Project Structure

```
faers-longevity-analysis/
├── config/              # Configuration files (drugs, AE mappings, data config)
├── data/                # Data directory (gitignored)
│   ├── raw/            # Raw FAERS downloads
│   ├── interim/        # Intermediate processed data
│   └── processed/      # Final analysis-ready datasets
├── docs/               # Documentation (methods, discussion, notes)
├── notebooks/          # Jupyter notebooks for analysis
├── scripts/            # Data acquisition and processing scripts
├── src/                # Source code modules
│   ├── data_ingest/    # Data loading and cleaning
│   ├── features/       # Feature engineering
│   ├── models/         # Statistical and ML models
│   └── viz/            # Visualization modules
└── results/            # Output tables and figures
```

## Results

- [Methods Documentation](docs/methods.md)
- [Key Findings](docs/discussion.md)
- [FAERS Data Notes](docs/faers_notes.md)
- [Figures](results/figures/)

## Data Sources

- **FAERS Quarterly Data Files**: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- **OpenFDA API**: https://open.fda.gov/apis/drug/event/ (for exploration only)

## Citation

If you use this work:

```
[Your Name]. (2024). FAERS Longevity Drug Safety Analysis. 
GitHub: https://github.com/yourusername/faers-longevity-analysis
```

## License

MIT License - See LICENSE file

## Disclaimer

This project is for educational and research purposes only. It does not constitute medical advice. Consult healthcare professionals for medication decisions.

