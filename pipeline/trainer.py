import json
import os
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_val_score,
)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from config import (
    LABEL_MAP,
    LABEL_NAMES,
    XGBOOST_PARAMS,
    MODEL_PATH,
    STRUCTURED_FEATURES,
)
from feature_extractor import extract_features


def load_dataset(path: str) -> Tuple[np.ndarray, np.ndarray, List[dict]]:
    """
    Load candidates JSON file and extract features + labels.

    Args:
        path: path to JSON file containing list of candidate objects

    Returns:
        X: feature matrix (n_candidates, n_features)
        y: label vector (n_candidates,)
        raw: list of raw candidate dicts (for fairness audit later)
    """
    with open(path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    X_list = []
    y_list = []
    valid_candidates = []

    for c in candidates:
        label = c.get("label")
        if label not in LABEL_MAP:
            print(f"  [SKIP] Candidate {c.get('id', '?')}: unknown label '{label}'")
            continue

        features = extract_features(c)
        X_list.append(features)
        y_list.append(LABEL_MAP[label])
        valid_candidates.append(c)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)

    print(f"Loaded {len(y)} candidates ({len(candidates) - len(y)} skipped)")
    print(f"  Label distribution: {dict(zip(LABEL_NAMES, np.bincount(y, minlength=3)))}")
    print(f"  Feature dimensions: {X.shape}")

    return X, y, valid_candidates


def train_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> Any:
    """
    Train gradient boosting classifier.
    Uses XGBoost if available, falls back to sklearn GradientBoosting.
    """
    model = XGBClassifier(**XGBOOST_PARAMS)
    model.fit(X_train, y_train, verbose=False)
    return model


def train_baseline_gpa(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Baseline 1: rank by GPA only.
    Returns predicted labels based on GPA thresholds.
    """
    gpa_idx = STRUCTURED_FEATURES.index("f_gpa")
    gpa = X[:, gpa_idx]

    # Simple thresholds: top 30% = shortlist, middle 40% = maybe, bottom 30% = reject
    sorted_gpa = np.sort(gpa)
    low_thresh = np.percentile(sorted_gpa, 30)
    high_thresh = np.percentile(sorted_gpa, 70)

    preds = np.zeros(len(gpa), dtype=np.int32)
    preds[gpa < low_thresh] = 0   # reject
    preds[(gpa >= low_thresh) & (gpa < high_thresh)] = 1  # maybe
    preds[gpa >= high_thresh] = 2  # shortlist

    return preds


def train_baseline_rules(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Baseline 2: rule-based scoring.
    Hand-crafted formula simulating what a human committee might do.
    """
    gpa_idx = STRUCTURED_FEATURES.index("f_gpa")
    olymp_idx = STRUCTURED_FEATURES.index("f_olympiad_count")
    proj_idx = STRUCTURED_FEATURES.index("f_project_count")
    founder_idx = STRUCTURED_FEATURES.index("f_founder_ratio")
    diversity_idx = STRUCTURED_FEATURES.index("f_project_diversity")

    score = (
        X[:, gpa_idx] * 20          # GPA weight
        + X[:, olymp_idx] * 10       # Olympiad count
        + X[:, proj_idx] * 8         # Project count
        + X[:, founder_idx] * 15     # Initiative
        + X[:, diversity_idx] * 5    # Diversity
    )

    low_thresh = np.percentile(score, 30)
    high_thresh = np.percentile(score, 70)

    preds = np.ones(len(score), dtype=np.int32)  # default maybe
    preds[score < low_thresh] = 0
    preds[score >= high_thresh] = 2

    return preds


def train_baseline_logreg(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
) -> np.ndarray:
    """
    Baseline 3: Logistic Regression on same features.
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)
    return model.predict(X_test_scaled)


def cross_validate(X: np.ndarray, y: np.ndarray, n_folds: int = 5) -> dict:
    model = XGBClassifier(**XGBOOST_PARAMS)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    scores_acc = cross_val_score(model, X, y, cv=skf, scoring="accuracy")
    scores_f1 = cross_val_score(model, X, y, cv=skf, scoring="f1_macro")

    results = {
        "n_folds": n_folds,
        "accuracy_mean": float(np.mean(scores_acc)),
        "accuracy_std": float(np.std(scores_acc)),
        "f1_macro_mean": float(np.mean(scores_f1)),
        "f1_macro_std": float(np.std(scores_f1)),
        "fold_accuracies": scores_acc.tolist(),
        "fold_f1s": scores_f1.tolist(),
    }

    print(f"\n=== {n_folds}-Fold Cross-Validation ===")
    print(f"  Accuracy: {results['accuracy_mean']:.4f} ± {results['accuracy_std']:.4f}")
    print(f"  F1 Macro: {results['f1_macro_mean']:.4f} ± {results['f1_macro_std']:.4f}")

    return results


def save_model(model, path: str = None):
    path = path or MODEL_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved to {path}")


def load_model(path: str = None):
    """Load trained model from disk."""
    path = path or MODEL_PATH
    with open(path, "rb") as f:
        model = pickle.load(f)
    return model



def train(dataset_path: str, test_size: float = 0.2) -> dict:
    """
    Full training pipeline:
    1. Load data
    2. Split train/test
    3. Cross-validate
    4. Train final model
    5. Save model
    6. Return all artifacts for evaluator

    Returns:
        dict with model, splits, cv_results
    """
    print("=" * 60)
    print("InVision U — Model Training")
    print("=" * 60)

    # 1. Load
    X, y, raw_candidates = load_dataset(dataset_path)

    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )
    print(f"\nTrain: {len(y_train)} | Test: {len(y_test)}")

    # 3. Cross-validate
    cv_results = cross_validate(X_train, y_train)

    # 4. Train final model
    print("\nTraining final XGBoost model...")
    model = train_xgboost(X_train, y_train)

    # 5. Save
    save_model(model)

    return {
        "model": model,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "cv_results": cv_results,
        "raw_candidates": raw_candidates,
    }


def train_two_stage(dataset_path: str, test_size: float = 0.2) -> dict:
    """
    Train the ThreeStageScorer (structural + fingerprint + essay).
    Imported here lazily to avoid circular imports.
    """
    from scorer import ThreeStageScorer

    print("=" * 60)
    print("InVision U — Two-Stage Model Training")
    print("=" * 60)

    _, y, raw_candidates = load_dataset(dataset_path)

    indices = np.arange(len(raw_candidates))
    train_idx, test_idx = train_test_split(
        indices, test_size=test_size, stratify=y, random_state=42
    )

    train_candidates = [raw_candidates[i] for i in train_idx]
    test_candidates  = [raw_candidates[i] for i in test_idx]
    y_train = y[train_idx]
    y_test  = y[test_idx]

    print(f"\nTrain: {len(y_train)} | Test: {len(y_test)}")

    scorer = ThreeStageScorer()
    scorer.fit(train_candidates, y_train)
    scorer.save()

    return {
        "scorer":           scorer,
        "train_candidates": train_candidates,
        "test_candidates":  test_candidates,
        "y_train":          y_train,
        "y_test":           y_test,
    }


if __name__ == "__main__":
    import sys

    dataset_path = sys.argv[1] if len(sys.argv) > 1 else "../data/synthetic_dataset.json"

    if "--two-stage" in sys.argv:
        results = train_two_stage(dataset_path)
        print("\n✓ Two-stage training complete.")
    else:
        results = train(dataset_path)
        print("\n✓ Training complete.")
        print(f"  Model: {MODEL_PATH}")
        print(f"  Test set size: {len(results['y_test'])}")
