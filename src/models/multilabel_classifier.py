"""Multi-label classification models for AE prediction."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    classification_report,
    hamming_loss
)
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
import warnings
warnings.filterwarnings('ignore')


def prepare_features(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_cols: List[str],
    categorical_cols: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Prepare features and targets for ML models.
    
    Args:
        df: Input dataframe
        feature_cols: List of feature column names
        target_cols: List of target column names (AE categories)
        categorical_cols: List of categorical columns to one-hot encode
        
    Returns:
        Tuple of (X, y, feature_info)
    """
    if categorical_cols is None:
        categorical_cols = ['age_group', 'sex', 'drug_class']
    
    # Select features
    X = df[feature_cols].copy()
    y = df[target_cols].copy()
    
    # One-hot encode categorical variables
    encoders = {}
    for col in categorical_cols:
        if col in X.columns:
            # One-hot encode
            dummies = pd.get_dummies(X[col], prefix=col, drop_first=False)
            X = pd.concat([X, dummies], axis=1)
            X = X.drop(columns=[col])
            encoders[col] = 'onehot'
    
    # Handle missing values
    X = X.fillna(X.median(numeric_only=True))
    
    # Store feature names
    feature_names = X.columns.tolist()
    
    return X, y, {'feature_names': feature_names, 'encoders': encoders}


def train_baseline_models(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    models: Optional[Dict] = None
) -> Dict:
    """
    Train baseline multi-label classification models.
    
    Args:
        X_train: Training features
        y_train: Training targets (multi-label)
        models: Optional dict of model configs to override defaults
        
    Returns:
        Dictionary of fitted models
    """
    if models is None:
        models = {}
    
    fitted_models = {}
    
    # Logistic Regression
    if 'logistic' not in models or models['logistic']:
        lr = LogisticRegression(
            max_iter=1000,
            C=1.0,
            random_state=42,
            n_jobs=-1
        )
        lr_multi = MultiOutputClassifier(lr)
        lr_multi.fit(X_train, y_train)
        fitted_models['logistic'] = lr_multi
    
    # XGBoost (if available)
    if XGBOOST_AVAILABLE and ('xgboost' not in models or models['xgboost']):
        xgb = XGBClassifier(
            max_depth=6,
            learning_rate=0.1,
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
        xgb_multi = MultiOutputClassifier(xgb)
        xgb_multi.fit(X_train, y_train)
        fitted_models['xgboost'] = xgb_multi
    
    return fitted_models


def evaluate_models(
    models: Dict,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Evaluate multi-label classification models.
    
    Args:
        models: Dictionary of fitted models
        X_test: Test features
        y_test: Test targets
        threshold: Probability threshold for binary predictions
        
    Returns:
        DataFrame with evaluation metrics
    """
    results = []
    
    for model_name, model in models.items():
        # Predict probabilities
        y_pred_proba = model.predict_proba(X_test)
        
        # Convert to binary predictions
        # MultiOutputClassifier returns list of arrays, one per class
        if isinstance(y_pred_proba, list):
            y_pred = np.array([
                (proba[:, 1] >= threshold).astype(int)
                for proba in y_pred_proba
            ]).T
            y_pred_proba_array = np.array([proba[:, 1] for proba in y_pred_proba]).T
        else:
            y_pred = (y_pred_proba >= threshold).astype(int)
            y_pred_proba_array = y_pred_proba
        
        # Per-category metrics
        n_categories = y_test.shape[1]
        category_aucs = []
        category_aps = []
        category_f1s = []
        
        for i, col in enumerate(y_test.columns):
            if y_test[col].sum() > 0:  # At least one positive
                try:
                    auc = roc_auc_score(y_test[col], y_pred_proba_array[:, i])
                    ap = average_precision_score(y_test[col], y_pred_proba_array[:, i])
                    f1 = f1_score(y_test[col], y_pred[:, i])
                    
                    category_aucs.append(auc)
                    category_aps.append(ap)
                    category_f1s.append(f1)
                except:
                    pass
        
        # Aggregate metrics
        macro_auc = np.mean(category_aucs) if category_aucs else np.nan
        micro_auc = roc_auc_score(
            y_test.values.ravel(),
            y_pred_proba_array.ravel()
        ) if len(y_test.values.ravel()) > 0 else np.nan
        
        macro_ap = np.mean(category_aps) if category_aps else np.nan
        hamming = hamming_loss(y_test.values, y_pred)
        
        results.append({
            'model': model_name,
            'macro_auc': macro_auc,
            'micro_auc': micro_auc,
            'macro_ap': macro_ap,
            'hamming_loss': hamming,
            'n_categories': n_categories,
            'n_evaluated': len(category_aucs)
        })
    
    return pd.DataFrame(results)


def get_feature_importance(
    model,
    feature_names: List[str],
    target_names: List[str]
) -> pd.DataFrame:
    """
    Extract feature importance from trained model.
    
    Args:
        model: Fitted model (LogisticRegression or XGBoost)
        feature_names: List of feature names
        target_names: List of target names
        
    Returns:
        DataFrame with feature importance per target
    """
    importances = []
    
    if hasattr(model, 'estimators_'):
        # MultiOutputClassifier
        for i, estimator in enumerate(model.estimators_):
            target = target_names[i]
            
            if hasattr(estimator, 'coef_'):
                # Logistic Regression
                coef = estimator.coef_[0]
                for j, feat in enumerate(feature_names):
                    importances.append({
                        'target': target,
                        'feature': feat,
                        'importance': abs(coef[j]),
                        'coefficient': coef[j]
                    })
            
            elif hasattr(estimator, 'feature_importances_'):
                # XGBoost
                feat_imp = estimator.feature_importances_
                for j, feat in enumerate(feature_names):
                    importances.append({
                        'target': target,
                        'feature': feat,
                        'importance': feat_imp[j],
                        'coefficient': np.nan
                    })
    
    return pd.DataFrame(importances)

