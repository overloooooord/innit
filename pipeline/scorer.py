import json
import os
import numpy as np
from typing import Dict, Any

from config import LABEL_NAMES, MODEL_PATH, FEATURE_DESCRIPTIONS
from feature_extractor import extract_features, extract_features_dict
from trainer import load_model
from explainer import CandidateExplainer


class CandidateScorer:
    def __init__(self, model_path: str = None, X_background: np.ndarray = None):
        self.model     = load_model(model_path or MODEL_PATH)
        self.explainer = CandidateExplainer(self.model, X_background)

    def score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        feature_vector = extract_features(candidate)
        feature_dict   = extract_features_dict(candidate)

        X             = feature_vector.reshape(1, -1)
        probabilities = self.model.predict_proba(X)[0]
        predicted_cls = int(np.argmax(probabilities))
        confidence    = float(probabilities[predicted_cls])

        explanation = self.explainer.explain(feature_vector, predicted_cls)
        radar       = self._build_radar(candidate)
        flags       = self._build_flags(feature_dict)
        trajectory  = self._build_trajectory(candidate)

        return {
            "candidate_id": candidate.get("id", "unknown"),
            "prediction":   LABEL_NAMES[predicted_cls],
            "confidence":   confidence,
            "probabilities": {LABEL_NAMES[i]: float(probabilities[i]) for i in range(3)},
            "explanation": {
                "top_positive_factors": [
                    {
                        "description": f["description"],
                        "value":       f["feature_value"],
                        "impact":      round(f["shap_value"], 4),
                    }
                    for f in explanation["top_positive_factors"]
                ],
                "top_negative_factors": [
                    {
                        "description": f["description"],
                        "value":       f["feature_value"],
                        "impact":      round(f["shap_value"], 4),
                    }
                    for f in explanation["top_negative_factors"]
                ],
            },
            "radar":      radar,
            "flags":      flags,
            "trajectory": trajectory,
            "feature_values": {
                FEATURE_DESCRIPTIONS.get(k, k): round(v, 4)
                for k, v in feature_dict.items()
            },
        }

    def score_batch(self, candidates: list) -> list:
        return [self.score(c) for c in candidates]

    def rank(self, candidates: list) -> list:
        scored = self.score_batch(candidates)
        scored.sort(key=lambda x: x["probabilities"]["shortlist"], reverse=True)
        for i, s in enumerate(scored):
            s["rank"]             = i + 1
            s["total_candidates"] = len(scored)
        return scored

    # ── Radar: 5 Cornell SLPI dimensions ─────────────────────────

    def _build_radar(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        5 SLPI dimensions (Cornell Student Leadership Practices Inventory).
        Source: https://scl.cornell.edu/coe/ctlc/programs/leadership-assessments/slpi

        Values come from bot_metadata.fingerprint_display — computed by
        scenario_engine.py from the candidate's choice path across 4 branching
        scenarios (20-second timer each).

        If fingerprint_reliable == False or scenario_engine not yet deployed,
        all values are None (pending).

          model_the_way      — Setting an example by demonstrating personal values and beliefs
          inspire_vision     — Creating a compelling vision and enlisting others in it
          challenge_process  — Seeking out new and innovative ways of doing things
          enable_others      — Fostering collaboration and empowering others to contribute
          encourage_heart    — Recognising and celebrating the contributions of others
        """
        meta     = candidate.get("bot_metadata", {})
        reliable = meta.get("fingerprint_reliable", False)
        display  = meta.get("fingerprint_display", {})

        if not reliable or not display:
            return {
                "model_the_way":     None,
                "inspire_vision":    None,
                "challenge_process": None,
                "enable_others":     None,
                "encourage_heart":   None,
                "status":            "pending — scenario_engine.py not yet deployed",
            }

        return {
            "model_the_way":     display.get("model_the_way"),
            "inspire_vision":    display.get("inspire_vision"),
            "challenge_process": display.get("challenge_process"),
            "enable_others":     display.get("enable_others"),
            "encourage_heart":   display.get("encourage_heart"),
            "status":            "ok",
        }

    # ── Flags ─────────────────────────────────────────────────────

    def _build_flags(self, f: Dict[str, float]) -> Dict[str, Any]:
        """
        Commission flags.
        ai_detection and coherence — placeholders for NLP module.
        These are shown to commission in the card, never enter the scoring model.
        """
        flags: Dict[str, Any] = {
            "coherence": {
                "status": "pending",
                "label":  "Когерентность профиля",
                "detail": "Будет рассчитано NLP-модулем",
            },
            "ai_detection": {
                "status": "pending",
                "label":  "AI-детекция эссе",
                "detail": "Будет рассчитано AI-детектором",
            },
        }

        if f["f_project_count"] == 0:
            flags["no_projects"] = {
                "status": "warning",
                "label":  "Нет проектов",
                "detail": "Кандидат не указал ни одного проекта",
            }

        if f["f_founder_ratio"] == 0 and f["f_project_count"] > 0:
            flags["low_initiative"] = {
                "status": "info",
                "label":  "Низкая инициативность",
                "detail": "Участвовал в проектах, но не основал ни одного",
            }

        if f["f_role_progression"] > 1 and f["f_skill_diversity_growth"] >= 3:
            flags["strong_trajectory"] = {
                "status": "positive",
                "label":  "Сильная траектория роста",
                "detail": "Выраженный рост ролей и навыков",
            }

        return flags

    # ── Trajectory timeline ───────────────────────────────────────

    def _build_trajectory(self, candidate: Dict[str, Any]) -> list:
        events = []
        for p in candidate.get("experience", {}).get("projects", []):
            events.append({
                "year":     p.get("year", 0),
                "type":     "project",
                "title":    p.get("name", "Без названия"),
                "role":     p.get("role", "participant"),
                "category": p.get("type", "other"),
            })
        for o in candidate.get("education", {}).get("olympiads", []):
            events.append({
                "year":  o.get("year", 0),
                "type":  "olympiad",
                "title": f"Олимпиада: {o.get('subject', '?')}",
                "level": o.get("level", "?"),
                "prize": o.get("prize", False),
            })
        events.sort(key=lambda e: e["year"])
        return events


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scorer.py <candidate.json> [model.pkl]")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        candidate = json.load(f)

    model_path = sys.argv[2] if len(sys.argv) > 2 else None
    scorer = CandidateScorer(model_path)
    result = scorer.score(candidate)

    print(f"\n{'=' * 60}")
    print(f"CANDIDATE: {candidate.get('personal', {}).get('name', 'Unknown')}")
    print(f"{'=' * 60}")
    print(f"\nПредсказание: {result['prediction'].upper()}")
    print(f"Уверенность:  {result['confidence']:.1%}")
    print("\nВероятности:")
    for label, prob in result["probabilities"].items():
        bar = "█" * int(prob * 30)
        print(f"  {label:12s} {bar} {prob:.1%}")
    print("\n✅ Сильные стороны:")
    for f in result["explanation"]["top_positive_factors"]:
        print(f"   {f['description']} (+{f['impact']:.4f})")
    print("\n⚠️  Слабые стороны:")
    for f in result["explanation"]["top_negative_factors"]:
        print(f"   {f['description']} ({f['impact']:.4f})")
    print("\nLeadership Fingerprint (SLPI):")
    radar = result["radar"]
    print(f"  Status: {radar.get('status')}")
    for dim in ("model_the_way", "inspire_vision", "challenge_process", "enable_others", "encourage_heart"):
        val = radar.get(dim)
        if val is not None:
            print(f"  {dim:25s} {'█' * int(val * 20)} {val:.2f}")
        else:
            print(f"  {dim:25s} pending")

    output_path = f"outputs/score_{result['candidate_id']}.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nFull result → {output_path}")
