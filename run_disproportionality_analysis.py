"""
Disproportionality Analysis Script

Executes disproportionality analysis (ROR/PRR) for longevity-relevant drugs
using FAERS data. Generates volcano plots, heatmaps, and results tables.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import yaml
import logging

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.models.disproportionality import run_disproportionality_analysis
from src.viz.volcano_plots import plot_volcano, plot_heatmap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)

logger.info("="*60)
logger.info("Disproportionality Analysis")
logger.info("="*60)

# Load config
config_path = Path(__file__).parent / 'config' / 'data_config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Load processed data
data_path = Path(__file__).parent / config['data_paths']['processed'] / 'drug_ae_counts.csv'
logger.info(f"Loading data from {data_path}")
df = pd.read_csv(data_path)

logger.info(f"Data shape: {df.shape}")
logger.info(f"Drugs analyzed: {len(df['normalized_name'].unique())}")
logger.info(f"AE categories: {len(df['ae_category'].unique())}")

# Prepare data for disproportionality analysis
# Expand counts into individual records for contingency table construction
logger.info("Expanding drug-AE counts into individual records...")
expanded_data = []
for _, row in df.iterrows():
    for _ in range(row['count']):
        expanded_data.append({
            'normalized_name': row['normalized_name'],
            'ae_category': row['ae_category']
        })

df_expanded = pd.DataFrame(expanded_data)
logger.info(f"Expanded to {len(df_expanded):,} records")

# Get unique drugs and categories
drug_list = df['normalized_name'].unique().tolist()
ae_list = df['ae_category'].unique().tolist()

logger.info(f"Analyzing {len(drug_list)} drugs × {len(ae_list)} AE categories")

# Run analysis
logger.info("Computing disproportionality metrics...")
results = run_disproportionality_analysis(
    df_expanded,
    drug_col='normalized_name',
    drug_list=drug_list,
    event_col='ae_category',
    event_list=ae_list,
    min_count=5,
    min_drug_reports=10
)

logger.info(f"Found {len(results)} significant drug-event pairs")
logger.info(f"Signals detected: {results['is_signal'].sum()}")

# Save results
results_path = Path(__file__).parent / 'results' / 'tables' / 'disproportionality_results.csv'
results_path.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(results_path, index=False)
logger.info(f"Results saved to {results_path}")

# Create visualizations
logger.info("Generating visualizations...")
figures_dir = Path(__file__).parent / 'results' / 'figures'
figures_dir.mkdir(parents=True, exist_ok=True)

# Volcano plots for top drugs
top_drugs = df['normalized_name'].value_counts().head(6).index.tolist()
for drug in top_drugs:
    try:
        fig, ax = plot_volcano(
            results,
            drug_name=drug,
            top_n=10
        )
        save_path = figures_dir / f'volcano_{drug.lower().replace(" ", "_")}.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved volcano plot: {save_path.name}")
    except Exception as e:
        logger.error(f"Error creating volcano plot for {drug}: {e}")

# Heatmap
try:
    fig, ax = plot_heatmap(
        results,
        drug_col='drug',
        event_col='event',
        value_col='ror'
    )
    save_path = figures_dir / 'heatmap_all_drugs.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved heatmap: {save_path.name}")
except Exception as e:
    logger.error(f"Error creating heatmap: {e}")

# Save top 50 signals per drug
tables_dir = Path(__file__).parent / 'results' / 'tables'
tables_dir.mkdir(parents=True, exist_ok=True)

for drug in drug_list:
    drug_results = results[results['drug'] == drug].nlargest(50, 'ror')
    if len(drug_results) > 0:
        save_path = tables_dir / f'{drug.lower().replace(" ", "_")}_top50_signals.csv'
        drug_results.to_csv(save_path, index=False)
        logger.info(f"Saved top signals for {drug}: {len(drug_results)} pairs")

logger.info("="*60)
logger.info("Disproportionality analysis complete")
logger.info("="*60)

