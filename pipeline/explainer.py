import os
import json
import numpy as np
from typing import Dict, Any, List
import shap

from config import STRUCTURED_FEATURES, LABEL_NAMES, SHAP_PLOTS_DIR


# Human-readable feature descriptions (Russian)
FEATURE_DESCRIPTIONS = {
    "f_gpa": "Средний балл (GPA)",
    "f_olympiad_count": "Количество олимпиад",
    "f_olympiad_max_level": "Максимальный уровень олимпиады",
    "f_olympiad_has_prize": "Наличие призового места",
    "f_courses_count": "Количество онлайн-курсов",
    "f_courses_completed_ratio": "Доля завершённых курсов",
    "f_project_count": "Количество проектов",
    "f_founder_ratio": "Доля проектов как основатель",
    "f_has_technical_project": "Наличие технического проекта",
    "f_has_social_project": "Наличие социального проекта",
    "f_project_diversity": "Разнообразие типов проектов",
    "f_max_team_size": "Макс. размер команды",
    "f_solo_project_count": "Количество сольных проектов",
    "f_role_progression": "Рост ролей (участник → лидер)",
    "f_scope_progression": "Рост масштаба деятельности",
    "f_skill_diversity_growth": "Рост разнообразия навыков",
    "f_activity_years_span": "Период активности (лет)",
    "f_persistence_signal": "Сигнал упорства (повтор после неудачи)",
    "f_activity_recency": "Давность последней активности",
    "f_session_duration": "Длительность заполнения заявки",
    "f_essay_typing_duration": "Время написания эссе",
    "f_total_pauses": "Количество пауз при заполнении",
}


class CandidateExplainer:
    def __init__(self, model, X_background: np.ndarray = None):
        self.model = model
        self.feature_names = STRUCTURED_FEATURES
        self.X_background = X_background

        if X_background is not None and len(X_background) > 200:
            indices = np.random.RandomState(42).choice(
                len(X_background), 200, replace=False
            )
            X_background = X_background[indices]

        self.explainer = shap.TreeExplainer(model, data=X_background)

    def explain(
        self,
        feature_vector: np.ndarray,
        predicted_class: int = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate explanation for a single candidate.
        Uses SHAP if available, otherwise uses model feature_importances_
        combined with feature values for a simulated explanation.
        """
        X = feature_vector.reshape(1, -1)

        if predicted_class is None:
            predicted_class = int(self.model.predict(X)[0])

        if self.explainer is not None:
            return self._explain_shap(feature_vector, predicted_class, top_k)
        else:
            return self._explain_fallback(feature_vector, predicted_class, top_k)

    def _explain_shap(
        self,
        feature_vector: np.ndarray,
        predicted_class: int,
        top_k: int,
    ) -> Dict[str, Any]:
        """SHAP-based explanation."""
        X = feature_vector.reshape(1, -1)
        shap_values = self.explainer.shap_values(X)

        if isinstance(shap_values, list):
            sv = shap_values[predicted_class][0]
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            sv = shap_values[0, :, predicted_class]
        else:
            sv = shap_values[0]

        return self._format_explanation(sv, feature_vector, predicted_class, top_k)

    def _explain_fallback(
        self,
        feature_vector: np.ndarray,
        predicted_class: int,
        top_k: int,
    ) -> Dict[str, Any]:
        """
        Fallback explanation using feature_importances_ and deviation
        from mean. Approximates SHAP by: importance × (value - mean).
        """
        importances = self._get_feature_importances()

        # Compute mean of each feature from background
        if self.X_background is not None:
            means = self.X_background.mean(axis=0)
        else:
            means = np.zeros(len(feature_vector))

        # Simulate SHAP: importance × normalized deviation
        deviations = feature_vector - means
        stds = self.X_background.std(axis=0) if self.X_background is not None else np.ones(len(feature_vector))
        stds = np.where(stds == 0, 1, stds)
        normalized_dev = deviations / stds

        # Pseudo-SHAP: direction depends on deviation, magnitude on importance
        sv = importances * normalized_dev

        return self._format_explanation(sv, feature_vector, predicted_class, top_k)

    def _get_feature_importances(self) -> np.ndarray:
        """Extract feature importances from model."""
        if hasattr(self.model, "feature_importances_"):
            return self.model.feature_importances_
        else:
            return np.ones(len(self.feature_names)) / len(self.feature_names)

    def _format_explanation(
        self,
        sv: np.ndarray,
        feature_vector: np.ndarray,
        predicted_class: int,
        top_k: int,
    ) -> Dict[str, Any]:
        """Format SHAP/pseudo-SHAP values into explanation dict."""
        feature_impacts = []
        for i, (name, value) in enumerate(zip(self.feature_names, sv)):
            feature_impacts.append({
                "feature": name,
                "description": FEATURE_DESCRIPTIONS.get(name, name),
                "shap_value": float(value),
                "feature_value": float(feature_vector[i]),
                "impact": "positive" if value > 0 else "negative",
            })

        feature_impacts.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        positive = [f for f in feature_impacts if f["shap_value"] > 0][:top_k]
        negative = [f for f in feature_impacts if f["shap_value"] < 0][:top_k]

        explanation = {
            "predicted_class": LABEL_NAMES[predicted_class],
            "top_positive_factors": positive,
            "top_negative_factors": negative,
            "all_shap_values": dict(zip(self.feature_names, sv.tolist())),
            "method": "shap" if self.explainer is not None else "feature_importance_fallback",
        }

        return explanation

    def explain_readable(
        self,
        feature_vector: np.ndarray,
        predicted_class: int = None,
    ) -> str:
        """
        Generate human-readable explanation in Russian.
        """
        exp = self.explain(feature_vector, predicted_class)
        lines = []

        lines.append(f"Рекомендация: {exp['predicted_class'].upper()}")
        lines.append("")

        if exp["top_positive_factors"]:
            lines.append("Сильные стороны:")
            for f in exp["top_positive_factors"]:
                lines.append(
                    f"  ✅ {f['description']} "
                    f"(значение: {f['feature_value']:.2f}, "
                    f"вклад: +{f['shap_value']:.3f})"
                )

        if exp["top_negative_factors"]:
            lines.append("")
            lines.append("Слабые стороны:")
            for f in exp["top_negative_factors"]:
                lines.append(
                    f"  ⚠️  {f['description']} "
                    f"(значение: {f['feature_value']:.2f}, "
                    f"вклад: {f['shap_value']:.3f})"
                )

        return "\n".join(lines)

    def global_importance(self, X: np.ndarray) -> List[Dict[str, Any]]:
        """
        Compute global feature importance.
        Uses SHAP if available, else model.feature_importances_.
        """
        if self.explainer is not None:
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                mean_abs = np.mean(
                    [np.abs(sv).mean(axis=0) for sv in shap_values], axis=0,
                )
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                mean_abs = np.abs(shap_values).mean(axis=(0, 2))
            else:
                mean_abs = np.abs(shap_values).mean(axis=0)
        else:
            mean_abs = self._get_feature_importances()

        importance = []
        for i, name in enumerate(self.feature_names):
            importance.append({
                "feature": name,
                "description": FEATURE_DESCRIPTIONS.get(name, name),
                "mean_abs_shap": float(mean_abs[i]),
            })

        importance.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
        return importance

    def save_explanation(
        self,
        explanation: dict,
        candidate_id: str,
        path: str = None,
    ):
        """Save explanation to JSON file."""
        path = path or os.path.join(SHAP_PLOTS_DIR, f"explanation_{candidate_id}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(explanation, f, indent=2, ensure_ascii=False)


# ============================================================
# Ablation study
# ============================================================

def ablation_study(
    model_class,
    model_params: dict,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Dict[str, float]:
    """
    Remove feature groups one at a time and measure accuracy drop.
    Proves each component of the pipeline is necessary.
    """
    from sklearn.metrics import f1_score as sk_f1_score

    feature_groups = {
        "Education": [0, 1, 2, 3, 4, 5],
        "Experience": [6, 7, 8, 9, 10, 11, 12],
        "Trajectory": [13, 14, 15, 16, 17, 18],
        "Bot Metadata": [19, 20, 21],
    }

    # Full model baseline
    full_model = model_class(**model_params)
    full_model.fit(X_train, y_train)
    full_f1 = sk_f1_score(y_test, full_model.predict(X_test), average="macro")

    results = {"Full model": float(full_f1)}

    print(f"\n=== Ablation Study ===")
    print(f"Full model F1: {full_f1:.4f}\n")

    for group_name, indices in feature_groups.items():
        # Remove this group
        remaining = [i for i in range(X_train.shape[1]) if i not in indices]
        X_train_ablated = X_train[:, remaining]
        X_test_ablated = X_test[:, remaining]

        ablated_model = model_class(**model_params)
        ablated_model.fit(X_train_ablated, y_train)
        ablated_f1 = sk_f1_score(y_test, ablated_model.predict(X_test_ablated), average="macro")

        drop = full_f1 - ablated_f1
        results[f"Without {group_name}"] = float(ablated_f1)

        print(f"  Without {group_name:15s}: F1 = {ablated_f1:.4f}  (drop: {drop:+.4f})")

    return results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    from trainer import train
    from feature_extractor import extract_features

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python explainer.py <dataset.json>              # global importance")
        print("  python explainer.py <dataset.json> <candidate.json>  # single explanation")
        sys.exit(1)

    # Train or load model
    dataset_path = sys.argv[1]
    results = train(dataset_path)

    explainer = CandidateExplainer(results["model"], results["X_train"])

    if len(sys.argv) >= 3:
        # Single candidate explanation
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            candidate = json.load(f)
        vector = extract_features(candidate)
        print("\n" + explainer.explain_readable(vector))
    else:
        # Global importance
        importance = explainer.global_importance(results["X_train"])
        print("\n=== Global Feature Importance ===")
        for i, feat in enumerate(importance):
            bar = "█" * int(feat["mean_abs_shap"] * 50)
            print(f"  {i + 1:2d}. {feat['description']:40s} {bar} ({feat['mean_abs_shap']:.4f})")
