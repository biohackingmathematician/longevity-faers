"""Volcano plots for disproportionality analysis."""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Optional, List
from pathlib import Path


def plot_volcano(
    results_df: pd.DataFrame,
    drug_name: str,
    x_col: str = 'a',
    y_col: str = 'ror',
    color_col: str = 'event',
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    top_n: int = 10,
    ror_threshold: float = 2.0
):
    """
    Create volcano plot for disproportionality analysis.
    
    Args:
        results_df: DataFrame with disproportionality results
        drug_name: Name of drug to plot
        x_col: Column for x-axis (typically count 'a')
        y_col: Column for y-axis (typically 'ror')
        color_col: Column to color by (typically 'event' or 'ae_category')
        title: Plot title (auto-generated if None)
        save_path: Path to save figure
        top_n: Number of top signals to annotate
        ror_threshold: ROR threshold line to draw
    """
    # Filter to drug
    drug_df = results_df[results_df['drug'] == drug_name].copy()
    
    if len(drug_df) == 0:
        print(f"No data found for {drug_name}")
        return
    
    # Prepare data
    drug_df['log10_count'] = np.log10(drug_df[x_col] + 1)
    drug_df['log2_ror'] = np.log2(drug_df[y_col] + 1e-6)  # Add small value to avoid log(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    scatter = ax.scatter(
        drug_df['log10_count'],
        drug_df['log2_ror'],
        c=drug_df[color_col].astype('category').cat.codes,
        cmap='tab10',
        alpha=0.6,
        s=50,
        edgecolors='black',
        linewidth=0.5
    )
    
    # Add threshold line
    ax.axhline(y=np.log2(ror_threshold), color='red', linestyle='--', linewidth=2, label=f'ROR = {ror_threshold}')
    
    # Annotate top signals
    top_signals = drug_df.nlargest(top_n, y_col)
    for idx, row in top_signals.iterrows():
        ax.annotate(
            row[color_col],
            (row['log10_count'], row['log2_ror']),
            fontsize=8,
            alpha=0.8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5)
        )
    
    # Labels and title
    ax.set_xlabel(f'Log10(Count) [{x_col}]', fontsize=12)
    ax.set_ylabel(f'Log2(ROR)', fontsize=12)
    if title is None:
        title = f'Volcano Plot: {drug_name}'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved volcano plot to {save_path}")
    
    return fig, ax


def plot_heatmap(
    results_df: pd.DataFrame,
    drug_col: str = 'drug',
    event_col: str = 'event',
    value_col: str = 'ror',
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    cmap: str = 'RdYlBu_r'
):
    """
    Create heatmap of drugs × AE categories with ROR values.
    
    Args:
        results_df: DataFrame with disproportionality results
        drug_col: Column name for drugs
        event_col: Column name for events/categories
        value_col: Column name for values to plot (typically 'ror')
        title: Plot title
        save_path: Path to save figure
        vmin: Minimum value for color scale
        vmax: Maximum value for color scale
        cmap: Colormap name
    """
    # Pivot to create matrix
    pivot_df = results_df.pivot_table(
        index=drug_col,
        columns=event_col,
        values=value_col,
        aggfunc='mean'
    )
    
    # Clamp values for visualization
    if vmin is None:
        vmin = -2
    if vmax is None:
        vmax = 4
    
    # Apply log2 transform and clamp
    pivot_df_log = np.log2(pivot_df + 1e-6)
    pivot_df_log = pivot_df_log.clip(vmin, vmax)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Heatmap
    sns.heatmap(
        pivot_df_log,
        annot=True,
        fmt='.2f',
        cmap=cmap,
        center=0,
        vmin=vmin,
        vmax=vmax,
        cbar_kws={'label': 'Log2(ROR)'},
        ax=ax
    )
    
    ax.set_title(title or 'Drug × AE Category Heatmap (Log2 ROR)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Adverse Event Category', fontsize=12)
    ax.set_ylabel('Drug', fontsize=12)
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved heatmap to {save_path}")
    
    return fig, ax


def plot_forest_plot(
    results_df: pd.DataFrame,
    event_name: str,
    drug_col: str = 'drug',
    ror_col: str = 'ror',
    ci_low_col: str = 'ror_ci_low',
    ci_high_col: str = 'ror_ci_high',
    title: Optional[str] = None,
    save_path: Optional[str] = None
):
    """
    Create forest plot showing ROR and 95% CI for one event across all drugs.
    
    Args:
        results_df: DataFrame with disproportionality results
        event_name: Name of event to plot
        drug_col: Column name for drugs
        ror_col: Column name for ROR values
        ci_low_col: Column name for lower CI
        ci_high_col: Column name for upper CI
        title: Plot title
        save_path: Path to save figure
    """
    # Filter to event
    event_df = results_df[results_df['event'] == event_name].copy()
    
    if len(event_df) == 0:
        print(f"No data found for {event_name}")
        return
    
    # Sort by ROR
    event_df = event_df.sort_values(ror_col, ascending=True)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, max(6, len(event_df) * 0.5)))
    
    y_pos = np.arange(len(event_df))
    
    # Plot CI bars
    for i, (idx, row) in enumerate(event_df.iterrows()):
        ax.plot(
            [row[ci_low_col], row[ci_high_col]],
            [i, i],
            'k-',
            linewidth=2,
            alpha=0.7
        )
    
    # Plot ROR points
    ax.scatter(
        event_df[ror_col],
        y_pos,
        s=100,
        color='red',
        zorder=3,
        edgecolors='black',
        linewidth=1
    )
    
    # Add reference line at ROR = 1
    ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, label='ROR = 1 (no association)')
    
    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(event_df[drug_col])
    ax.set_xlabel('Reporting Odds Ratio (ROR) with 95% CI', fontsize=12)
    ax.set_title(title or f'Forest Plot: {event_name}', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved forest plot to {save_path}")
    
    return fig, ax

