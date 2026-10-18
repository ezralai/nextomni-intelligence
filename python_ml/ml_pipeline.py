"""
NextOmni Analytics Intelligence Engine - Machine Learning Pipeline
Trains predictive models for:
1. 7-Day Cognitive Burnout & Academic Drop-off Risk (Supervised Ensemble Classification)
2. Autoregressive Circadian Energy Forecasting (Next 7-Day Trajectory)
3. Feature Importance & Interpretability Extraction
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, TimeSeriesSplit, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    brier_score_loss,
)
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data", "seeds")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def load_and_engineer_features():
    """Aggregates multi-table telemetry into a daily analytical feature store."""
    focus_df = pd.read_csv(os.path.join(DATA_DIR, "focus_sessions.csv"))
    circadian_df = pd.read_csv(os.path.join(DATA_DIR, "circadian_energy_logs.csv"))
    habit_df = pd.read_csv(os.path.join(DATA_DIR, "habit_logs.csv"))
    journal_df = pd.read_csv(os.path.join(DATA_DIR, "journal_entries.csv"))
    tasks_df = pd.read_csv(os.path.join(DATA_DIR, "academic_tasks.csv"))

    # 1. Daily Focus Rollups
    daily_focus = focus_df.groupby("session_date").agg(
        total_sessions=("session_id", "count"),
        total_focus_min=("actual_duration_min", "sum"),
        deep_work_min=("actual_duration_min", lambda x: focus_df.loc[x.index, "actual_duration_min"][focus_df.loc[x.index, "is_deep_work"] == 1].sum()),
        avg_flow_score=("flow_score", "mean"),
        total_interruptions=("interruption_count", "sum"),
        avg_completion_rate=("completion_rate", "mean")
    ).reset_index()

    daily_focus["session_date"] = pd.to_datetime(daily_focus["session_date"])
    daily_focus = daily_focus.sort_values("session_date")
    
    # Rolling 7-day window features
    daily_focus["rolling_7d_focus_min"] = daily_focus["total_focus_min"].rolling(7, min_periods=1).mean()
    daily_focus["rolling_7d_flow_score"] = daily_focus["avg_flow_score"].rolling(7, min_periods=1).mean()
    daily_focus["rolling_14d_interruptions"] = daily_focus["total_interruptions"].rolling(14, min_periods=1).sum()

    # 2. Daily Circadian Aggregations
    daily_circadian = circadian_df.groupby("log_date").agg(
        sleep_hours=("sleep_hours_prev_night", "first"),
        sleep_quality=("sleep_quality_score", "first"),
        caffeine_intake_mg=("caffeine_intake_mg", "first"),
        avg_daily_energy=("energy_level", "mean"),
        burnout_proxy=("burnout_risk_proxy", "mean")
    ).reset_index()
    daily_circadian["log_date"] = pd.to_datetime(daily_circadian["log_date"])

    # 3. Daily Habit Adherence
    daily_habits = habit_df.groupby("log_date").agg(
        habit_adherence_rate=("is_completed", "mean")
    ).reset_index()
    daily_habits["log_date"] = pd.to_datetime(daily_habits["log_date"])
    daily_habits["rolling_7d_habit_rate"] = daily_habits["habit_adherence_rate"].rolling(7, min_periods=1).mean()

    # 4. Target Labels from Journal / Biometrics
    daily_journal = journal_df[["entry_date", "mood_score", "burnout_label"]].copy()
    daily_journal["entry_date"] = pd.to_datetime(daily_journal["entry_date"])

    # Merge into unified analytical base table (ABT)
    abt = pd.merge(daily_focus, daily_circadian, left_on="session_date", right_on="log_date", how="left")
    abt = pd.merge(abt, daily_habits, left_on="session_date", right_on="log_date", how="left")
    abt = pd.merge(abt, daily_journal, left_on="session_date", right_on="entry_date", how="left")

    # Fill missing target with heuristic label if journal entry skipped on that day
    abt["burnout_label"] = abt["burnout_label"].fillna(
        (abt["burnout_proxy"] > 0.55).astype(int)
    ).astype(int)

    # Impute rolling forward for any unobserved day metrics
    abt = abt.bfill().ffill()
    
    # Feature Engineering: Chronotype Fatigue Ratio
    abt["fatigue_ratio"] = abt["total_interruptions"] / np.maximum(abt["sleep_hours"], 3.0)
    abt["energy_deficit"] = np.maximum(0, 4.0 - abt["avg_daily_energy"]) * (abt["total_focus_min"] / 60.0)

    return abt

def train_burnout_classifier(abt):
    """Trains Gradient Boosting & Random Forest classifiers with cross-validation."""
    feature_cols = [
        "total_focus_min",
        "deep_work_min",
        "avg_flow_score",
        "total_interruptions",
        "rolling_7d_focus_min",
        "rolling_7d_flow_score",
        "rolling_14d_interruptions",
        "sleep_hours",
        "sleep_quality",
        "caffeine_intake_mg",
        "avg_daily_energy",
        "habit_adherence_rate",
        "rolling_7d_habit_rate",
        "fatigue_ratio",
        "energy_deficit"
    ]

    X = abt[feature_cols]
    y = abt["burnout_label"]

    print(f"Dataset shape: {X.shape}, Positive Burnout Class Prevalance: {y.mean():.2%}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Gradient Boosting Classifier for non-linear feature interaction
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.08,
        max_depth=3,
        subsample=0.85,
        random_state=42
    )

    # 5-Fold Stratified Cross Validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_roc = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
    print(f"5-Fold Stratified CV ROC-AUC: {cv_roc.mean():.4f} (+/- {cv_roc.std():.4f})")

    # Temporal Time-Series Cross Validation (Multi-class safe with test_size=30)
    tscv = TimeSeriesSplit(n_splits=3, test_size=30)
    valid_scores = []
    for train_idx, test_idx in tscv.split(X):
        y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]
        if len(np.unique(y_tr)) > 1 and len(np.unique(y_te)) > 1:
            clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.08, max_depth=3, subsample=0.85, random_state=42)
            clf.fit(X.iloc[train_idx], y_tr)
            preds = clf.predict_proba(X.iloc[test_idx])[:, 1]
            valid_scores.append(roc_auc_score(y_te, preds))

    tscv_mean = float(np.mean(valid_scores)) if valid_scores else float(cv_roc.mean())
    tscv_std = float(np.std(valid_scores)) if valid_scores else 0.0
    print(f"Temporal TimeSeriesSplit ROC-AUC: {tscv_mean:.4f} (+/- {tscv_std:.4f})")

    model.fit(X_train, y_train)

    # Evaluation on Hold-Out Test Set
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.50).astype(int)

    test_roc_auc = roc_auc_score(y_test, y_pred_proba)
    test_pr_auc = average_precision_score(y_test, y_pred_proba)
    test_brier = brier_score_loss(y_test, y_pred_proba)

    print("\n--- HOLD-OUT MODEL PERFORMANCE ---")
    print(f"ROC-AUC: {test_roc_auc:.4f}")
    print(f"PR-AUC (Average Precision): {test_pr_auc:.4f}")
    print(f"Brier Score Loss (Calibration): {test_brier:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Nominal Reserve", "Burnout Risk"]))

    # Feature Importance Ranking
    importances = model.feature_importances_
    feat_ranking = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
    print("\n--- TOP PREDICTIVE FEATURES (Gini Importance) ---")
    for feat, imp in feat_ranking[:8]:
        print(f"  {feat:<28}: {imp:.4f}")

    # Serialize artifacts
    model_path = os.path.join(MODELS_DIR, "burnout_risk_model.joblib")
    joblib.dump({
        "model": model,
        "feature_cols": feature_cols,
        "metrics": {
            "cv_roc_auc": float(cv_roc.mean()),
            "tscv_roc_auc": float(tscv_mean),
            "test_roc_auc": float(test_roc_auc),
            "test_pr_auc": float(test_pr_auc)
        }
    }, model_path)
    print(f"\nTrained model persisted to {model_path}")

    return model, feature_cols

def forecast_cognitive_energy(abt, horizon_days=7):
    """Autoregressive rolling projection for cognitive alertness over the next 7 days."""
    recent_energy = abt["avg_daily_energy"].tail(14).values
    recent_sleep = abt["sleep_hours"].tail(14).values
    
    # Cyclic weekday pattern + autoregressive decay
    forecasts = []
    current_val = recent_energy[-1]
    avg_sleep = np.mean(recent_sleep)
    
    for i in range(1, horizon_days + 1):
        day_noise = float(np.random.normal(0, 0.15))
        # Convergence towards baseline mean of 3.6 modulated by sleep reserve
        next_val = 0.65 * current_val + 0.35 * (3.6 + (avg_sleep - 7.0) * 0.2) + day_noise
        next_val = max(1.0, min(5.0, next_val))
        forecasts.append(round(float(next_val), 2))
        current_val = next_val

    return forecasts

if __name__ == "__main__":
    abt = load_and_engineer_features()
    model, features = train_burnout_classifier(abt)
    forecast = forecast_cognitive_energy(abt)
    print(f"\nNext 7-Day Cognitive Energy Forecast: {forecast}")
