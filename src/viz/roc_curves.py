"""ROC curves and ML evaluation visualizations."""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from sklearn.metrics import roc_curve, auc, precision_recall_curve


def plot_roc_curves(
    y_true: pd.DataFrame,
    y_pred_proba: np.ndarray,
    category_names: List[str],
    model_name: str = 'Model',
    save_path: Optional[str] = None
):
    """
    Plot ROC curves for each AE category.
    
    Args:
        y_true: True binary labels (n_samples, n_categories)
        y_pred_proba: Predicted probabilities (n_samples, n_categories)
        category_names: List of category names
        model_name: Name of model for title
        save_path: Path to save figure
    """
    n_categories = len(category_names)
    n_cols = 3
    n_rows = (n_categories + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
    axes = axes.flatten() if n_categories > 1 else [axes]
    
    for i, category in enumerate(category_names):
        ax = axes[i]
        
        # Get true and predicted for this category
        y_true_cat = y_true.iloc[:, i].values if isinstance(y_true, pd.DataFrame) else y_true[:, i]
        y_pred_cat = y_pred_proba[:, i] if y_pred_proba.ndim > 1 else y_pred_proba
        
        # Compute ROC curve
        fpr, tpr, _ = roc_curve(y_true_cat, y_pred_cat)
        roc_auc = auc(fpr, tpr)
        
        # Plot
        ax.plot(fpr, tpr, linewidth=2, label=f'AUC = {roc_auc:.3f}')
        ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5, label='Random')
        
        ax.set_xlabel('False Positive Rate', fontsize=10)
        ax.set_ylabel('True Positive Rate', fontsize=10)
        ax.set_title(f'{category}', fontsize=12, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3)
    
    # Hide unused subplots
    for i in range(n_categories, len(axes)):
        axes[i].axis('off')
    
    fig.suptitle(f'ROC Curves: {model_name}', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved ROC curves to {save_path}")
    
    return fig, axes


def plot_feature_importance(
    importance_df: pd.DataFrame,
    target_category: Optional[str] = None,
    top_n: int = 15,
    save_path: Optional[str] = None
):
    """
    Plot feature importance from trained model.
    
    Args:
        importance_df: DataFrame with feature importance (from get_feature_importance)
        target_category: Specific category to plot (None = aggregate)
        top_n: Number of top features to show
        save_path: Path to save figure
    """
    if target_category:
        plot_df = importance_df[importance_df['target'] == target_category].copy()
        title_suffix = f': {target_category}'
    else:
        # Aggregate across all targets
        plot_df = importance_df.groupby('feature')['importance'].mean().reset_index()
        plot_df = plot_df.sort_values('importance', ascending=False)
        title_suffix = ' (Aggregated)'
    
    # Get top N
    plot_df = plot_df.nlargest(top_n, 'importance')
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, max(6, len(plot_df) * 0.4)))
    
    # Horizontal bar plot
    y_pos = np.arange(len(plot_df))
    ax.barh(y_pos, plot_df['importance'], alpha=0.7)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_df['feature'])
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Top {top_n} Feature Importance{title_suffix}', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved feature importance to {save_path}")
    
    return fig, ax


def plot_metrics_comparison(
    metrics_df: pd.DataFrame,
    save_path: Optional[str] = None
):
    """
    Plot comparison of metrics across models.
    
    Args:
        metrics_df: DataFrame with evaluation metrics (from evaluate_models)
        save_path: Path to save figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    metrics_to_plot = ['macro_auc', 'micro_auc', 'macro_ap', 'hamming_loss']
    titles = ['Macro-Averaged AUC', 'Micro-Averaged AUC', 'Macro-Averaged AP', 'Hamming Loss']
    
    for i, (metric, title) in enumerate(zip(metrics_to_plot, titles)):
        ax = axes[i // 2, i % 2]
        
        bars = ax.bar(metrics_df['model'], metrics_df[metric], alpha=0.7)
        ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=10)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{height:.3f}',
                ha='center',
                va='bottom',
                fontsize=9
            )
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved metrics comparison to {save_path}")
    
    return fig, axes

