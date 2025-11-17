"""
Multi-Label Machine Learning Analysis Script

Trains and evaluates multi-label classification models to predict adverse event
categories from patient demographics, drug class, and polypharmacy features.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.models.multilabel_classifier import (
    prepare_features,
    train_baseline_models,
    evaluate_models,
    get_feature_importance
)
from src.viz.roc_curves import plot_roc_curves, plot_feature_importance, plot_metrics_comparison

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)

logger.info("="*60)
logger.info("Multi-Label AE Prediction Model")
logger.info("="*60)

# Load config
config_path = Path(__file__).parent / 'config' / 'data_config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Load ML dataset
data_path = Path(__file__).parent / config['data_paths']['processed'] / 'cases_ml.csv'
logger.info(f"Loading ML dataset from {data_path}")
df = pd.read_csv(data_path)

logger.info(f"Dataset shape: {df.shape[0]:,} samples, {df.shape[1]} features")

# Define features and targets
ae_categories = ['cardiovascular', 'metabolic', 'musculoskeletal', 'gastrointestinal', 'renal']
# Filter to available categories
ae_categories = [cat for cat in ae_categories if cat in df.columns]

feature_cols = ['age_group', 'sex', 'drug_class', 'report_year', 
                'n_concomitant_drugs', 'has_cardio_comedication', 'has_insulin']
# Filter to available columns
feature_cols = [col for col in feature_cols if col in df.columns]

logger.info(f"Features: {len(feature_cols)}")
logger.info(f"Target categories: {len(ae_categories)}")

# Prepare features
logger.info("Preparing feature matrix...")
X, y, feature_info = prepare_features(
    df,
    feature_cols=feature_cols,
    target_cols=ae_categories,
    categorical_cols=['age_group', 'sex', 'drug_class']
)

logger.info(f"Feature matrix: {X.shape[0]:,} samples × {X.shape[1]} features")
logger.info(f"Target matrix: {y.shape[0]:,} samples × {y.shape[1]} categories")

# Time-based split
logger.info("Splitting data (time-based)...")
ml_split = config['ml_split']

if 'report_year' in df.columns:
    X['year'] = df['report_year'].values
    
    train_mask = (X['year'] >= int(ml_split['train_start'])) & (X['year'] <= int(ml_split['train_end']))
    val_mask = (X['year'] >= int(ml_split['val_start'])) & (X['year'] <= int(ml_split['val_end']))
    test_mask = (X['year'] >= int(ml_split['test_start'])) & (X['year'] <= int(ml_split['test_end']))
    
    X_train = X[train_mask].drop(columns=['year'])
    X_val = X[val_mask].drop(columns=['year'])
    X_test = X[test_mask].drop(columns=['year'])
    
    y_train = y[train_mask]
    y_val = y[val_mask]
    y_test = y[test_mask]
else:
    # Random split if no year
    from sklearn.model_selection import train_test_split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

logger.info(f"Train: {len(X_train):,}, Validation: {len(X_val):,}, Test: {len(X_test):,}")

# Train models
logger.info("Training models...")
models = train_baseline_models(X_train, y_train)

logger.info(f"Trained {len(models)} model(s): {', '.join(models.keys())}")

# Evaluate models
logger.info("Evaluating models on test set...")
metrics_df = evaluate_models(models, X_test, y_test)
logger.info(f"\nModel Performance:\n{metrics_df.to_string()}")

# Save metrics
metrics_path = Path(__file__).parent / 'results' / 'tables' / 'ml_metrics.csv'
metrics_path.parent.mkdir(parents=True, exist_ok=True)
metrics_df.to_csv(metrics_path, index=False)
logger.info(f"Metrics saved to {metrics_path}")

# Visualizations
logger.info("Generating visualizations...")
figures_dir = Path(__file__).parent / 'results' / 'figures'
figures_dir.mkdir(parents=True, exist_ok=True)

# ROC curves for best model
best_model_name = metrics_df.loc[metrics_df['macro_auc'].idxmax(), 'model']
best_model = models[best_model_name]

logger.info(f"Best performing model: {best_model_name}")

y_pred_proba = best_model.predict_proba(X_test)
if isinstance(y_pred_proba, list):
    y_pred_proba_array = np.array([proba[:, 1] for proba in y_pred_proba]).T
else:
    y_pred_proba_array = y_pred_proba

try:
    fig, axes = plot_roc_curves(
        y_test,
        y_pred_proba_array,
        ae_categories,
        model_name=best_model_name
    )
    save_path = figures_dir / 'roc_curves_ml.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved ROC curves: {save_path.name}")
except Exception as e:
    logger.error(f"Error creating ROC curves: {e}")

# Feature importance
try:
    importance_df = get_feature_importance(
        best_model,
        feature_info['feature_names'],
        ae_categories
    )
    
    # Save feature importance
    importance_path = Path(__file__).parent / 'results' / 'tables' / 'feature_importance.csv'
    importance_df.to_csv(importance_path, index=False)
    logger.info(f"Saved feature importance: {importance_path.name}")
    
    # Plot for top categories
    for category in ae_categories[:3]:
        try:
            fig, ax = plot_feature_importance(
                importance_df,
                target_category=category,
                top_n=15
            )
            save_path = figures_dir / f'feature_importance_{category}.png'
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Saved feature importance plot: {save_path.name}")
        except Exception as e:
            logger.error(f"Error creating feature importance plot for {category}: {e}")
except Exception as e:
    logger.error(f"Error getting feature importance: {e}")

# Metrics comparison
try:
    fig, axes = plot_metrics_comparison(metrics_df)
    save_path = figures_dir / 'metrics_comparison.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved metrics comparison: {save_path.name}")
except Exception as e:
    logger.error(f"Error creating metrics comparison: {e}")

logger.info("="*60)
logger.info("ML analysis complete")
logger.info("="*60)

