"""
InVision U ML Pipeline — Scorer
=================================
Final scoring module. Takes a candidate JSON, runs through the full
pipeline, and returns prediction + explanation ready for the dashboard.

This is the main entry point for the API.
"""

import json
import os
import numpy as np
from typing import Dict, Any

from config import LABEL_NAMES, MODEL_PATH
from feature_extractor import extract_features, extract_features_dict
from trainer import load_model
from explainer import CandidateExplainer, FEATURE_DESCRIPTIONS


class CandidateScorer:
    """
    Scores candidates and generates explanations.
    Loads a trained model once, then can score many candidates.
    """

    def __init__(self, model_path: str = None, X_background: np.ndarray = None):
        """
        Args:
            model_path: path to trained model pickle
            X_background: training data for SHAP background (optional)
        """
        self.model = load_model(model_path or MODEL_PATH)
        self.explainer = CandidateExplainer(self.model, X_background)

    def score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single candidate.

        Args:
            candidate: dict following candidate_schema.json

        Returns:
            {
                "candidate_id": str,
                "prediction": "shortlist" | "maybe" | "reject",
                "confidence": float,
                "probabilities": {"shortlist": float, "maybe": float, "reject": float},
                "explanation": {
                    "top_positive_factors": [...],
                    "top_negative_factors": [...]
                },
                "feature_values": {...},
                "radar": {...},
                "flags": {...}
            }
        """
        candidate_id = candidate.get("id", "unknown")

        # 1. Extract features
        feature_vector = extract_features(candidate)
        feature_dict = extract_features_dict(candidate)

        # 2. Predict
        X = feature_vector.reshape(1, -1)
        probabilities = self.model.predict_proba(X)[0]
        predicted_class = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_class])

        # 3. Explain
        explanation = self.explainer.explain(feature_vector, predicted_class)

        # 4. Build radar chart data
        radar = self._build_radar(feature_dict)

        # 5. Build flags
        flags = self._build_flags(feature_dict)

        # 6. Build trajectory summary
        trajectory = self._build_trajectory(candidate)

        result = {
            "candidate_id": candidate_id,
            "prediction": LABEL_NAMES[predicted_class],
            "confidence": confidence,
            "probabilities": {
                LABEL_NAMES[i]: float(probabilities[i]) for i in range(3)
            },
            "explanation": {
                "top_positive_factors": [
                    {
                        "description": f["description"],
                        "value": f["feature_value"],
                        "impact": round(f["shap_value"], 4),
                    }
                    for f in explanation["top_positive_factors"]
                ],
                "top_negative_factors": [
                    {
                        "description": f["description"],
                        "value": f["feature_value"],
                        "impact": round(f["shap_value"], 4),
                    }
                    for f in explanation["top_negative_factors"]
                ],
            },
            "radar": radar,
            "flags": flags,
            "trajectory": trajectory,
            "feature_values": {
                FEATURE_DESCRIPTIONS.get(k, k): round(v, 4)
                for k, v in feature_dict.items()
            },
        }

        return result

    def score_batch(self, candidates: list) -> list:
        """Score multiple candidates at once."""
        return [self.score(c) for c in candidates]

    def rank(self, candidates: list) -> list:
        """
        Score and rank candidates by shortlist probability.
        Returns sorted list with rank field added.
        """
        scored = self.score_batch(candidates)

        # Sort by shortlist probability descending
        scored.sort(key=lambda x: x["probabilities"]["shortlist"], reverse=True)

        # Add rank
        for i, s in enumerate(scored):
            s["rank"] = i + 1
            s["total_candidates"] = len(scored)

        return scored

    # ============================================================
    # Radar chart builder
    # ============================================================

    def _build_radar(self, features: Dict[str, float]) -> Dict[str, int]:
        """
        Build radar chart data (1-5 scale) for dashboard.
        Maps raw features to intuitive dimensions.
        """
        radar = {}

        # Initiative (1-5): based on founder_ratio and solo projects
        initiative = features["f_founder_ratio"] * 3 + min(features["f_solo_project_count"], 2)
        radar["Инициативность"] = self._to_scale(initiative, 0, 5)

        # Resilience (1-5): persistence + olympiad retries
        resilience = (
            features["f_persistence_signal"] * 3
            + min(features["f_activity_years_span"], 2)
        )
        radar["Устойчивость"] = self._to_scale(resilience, 0, 5)

        # Academic (1-5): GPA + olympiads
        academic = (
            (features["f_gpa"] - 2.0) / 3.0 * 3  # 2.0-5.0 → 0-3
            + features["f_olympiad_has_prize"] * 2
        )
        radar["Академические"] = self._to_scale(academic, 0, 5)

        # Leadership (1-5): team size + role progression + social projects
        leadership = (
            min(features["f_max_team_size"] / 10, 2)
            + features["f_role_progression"] + 1  # shift from [-1,2] to [0,3]
            + features["f_has_social_project"]
        )
        radar["Лидерство"] = self._to_scale(leadership, 0, 5)

        # Diversity (1-5): project diversity + skill growth
        diversity = (
            features["f_project_diversity"]
            + features["f_skill_diversity_growth"]
        )
        radar["Разнообразие"] = self._to_scale(diversity, 0, 6)

        return radar

    @staticmethod
    def _to_scale(value: float, min_val: float, max_val: float) -> int:
        """Convert a raw value to 1-5 scale."""
        if max_val == min_val:
            return 3
        normalized = (value - min_val) / (max_val - min_val)
        return int(np.clip(round(normalized * 4) + 1, 1, 5))

    # ============================================================
    # Flags builder
    # ============================================================

    def _build_flags(self, features: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """
        Generate warning/info flags for the commission.
        """
        flags = {}

        # Coherence flag (placeholder — will be filled by NLP module later)
        flags["coherence"] = {
            "status": "pending",
            "label": "Когерентность профиля",
            "detail": "Будет рассчитано NLP-модулем",
        }

        # AI detection flag (placeholder)
        flags["ai_detection"] = {
            "status": "pending",
            "label": "AI-детекция эссе",
            "detail": "Будет рассчитано AI-детектором",
        }

        # No projects flag
        if features["f_project_count"] == 0:
            flags["no_projects"] = {
                "status": "warning",
                "label": "Нет проектов",
                "detail": "Кандидат не указал ни одного проекта",
            }

        # Low initiative flag
        if features["f_founder_ratio"] == 0 and features["f_project_count"] > 0:
            flags["low_initiative"] = {
                "status": "info",
                "label": "Низкая инициативность",
                "detail": "Участвовал в проектах, но не основал ни одного",
            }

        # Stale activity flag
        if features["f_activity_recency"] >= 2:
            flags["stale_activity"] = {
                "status": "warning",
                "label": "Давняя активность",
                "detail": f"Последняя активность {int(features['f_activity_recency'])} лет назад",
            }

        # Strong trajectory flag
        if features["f_role_progression"] > 1 and features["f_skill_diversity_growth"] >= 3:
            flags["strong_trajectory"] = {
                "status": "positive",
                "label": "Сильная траектория роста",
                "detail": "Выраженный рост ролей и навыков",
            }

        return flags

    # ============================================================
    # Trajectory builder
    # ============================================================

    def _build_trajectory(self, candidate: Dict[str, Any]) -> list:
        """
        Build chronological trajectory for timeline visualization.
        """
        events = []

        # Projects
        for p in candidate.get("experience", {}).get("projects", []):
            events.append({
                "year": p.get("year", 0),
                "type": "project",
                "title": p.get("name", "Без названия"),
                "role": p.get("role", "participant"),
                "category": p.get("type", "other"),
            })

        # Olympiads
        for o in candidate.get("education", {}).get("olympiads", []):
            events.append({
                "year": o.get("year", 0),
                "type": "olympiad",
                "title": f"Олимпиада: {o.get('subject', '?')}",
                "level": o.get("level", "?"),
                "result": o.get("result", "participant"),
            })

        # Sort chronologically
        events.sort(key=lambda e: e["year"])

        return events


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scorer.py <candidate.json> [model.pkl]")
        sys.exit(1)

    candidate_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else None

    with open(candidate_path, "r", encoding="utf-8") as f:
        candidate = json.load(f)

    scorer = CandidateScorer(model_path)
    result = scorer.score(candidate)

    print("\n" + "=" * 60)
    print(f"CANDIDATE: {candidate.get('personal', {}).get('name', 'Unknown')}")
    print(f"ID: {result['candidate_id']}")
    print("=" * 60)

    print(f"\nPrediction:  {result['prediction'].upper()}")
    print(f"Confidence:  {result['confidence']:.1%}")
    print(f"Probabilities:")
    for label, prob in result["probabilities"].items():
        bar = "█" * int(prob * 30)
        print(f"  {label:12s} {bar} {prob:.1%}")

    print(f"\n--- Сильные стороны ---")
    for f in result["explanation"]["top_positive_factors"]:
        print(f"  ✅ {f['description']} (вклад: +{f['impact']:.4f})")

    print(f"\n--- Слабые стороны ---")
    for f in result["explanation"]["top_negative_factors"]:
        print(f"  ⚠️  {f['description']} (вклад: {f['impact']:.4f})")

    print(f"\n--- Radar ---")
    for dim, val in result["radar"].items():
        print(f"  {dim:20s} {'★' * val}{'☆' * (5 - val)}")

    print(f"\n--- Flags ---")
    for key, flag in result["flags"].items():
        icon = {"positive": "🟢", "warning": "🟡", "info": "🔵", "pending": "⏳"}.get(
            flag["status"], "❓"
        )
        print(f"  {icon} {flag['label']}: {flag['detail']}")

    print(f"\n--- Trajectory ---")
    for event in result["trajectory"]:
        print(f"  {event['year']} | {event['title']} ({event.get('role', event.get('result', ''))})")

    # Save full result
    output_path = f"outputs/score_{result['candidate_id']}.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nFull result saved to {output_path}")
