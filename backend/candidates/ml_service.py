import os
import sys
import logging
from django.conf import settings
logger = logging.getLogger(__name__)
_scorer = None
def get_scorer():
    global _scorer
    if _scorer is not None:
        return _scorer
    pipeline_dir = settings.ML_PIPELINE_DIR
    if pipeline_dir not in sys.path:
        sys.path.insert(0, pipeline_dir)
    pipeline_dir = settings.ML_PIPELINE_DIR
    if pipeline_dir not in sys.path:
        sys.path.insert(0, pipeline_dir)
    model_path = settings.ML_MODEL_PATH
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Модель не найдена: {model_path}\n"
            f"Сначала обучите модель:\n"
            f"  cd {pipeline_dir}\n"
            f"  python run_pipeline.py --dataset ../data/synthetic_dataset.json"
        )
    from scorer import CandidateScorer
    logger.info(f"Loading ML model from {model_path}")
    _scorer = CandidateScorer(model_path=model_path)
    logger.info("ML model loaded successfully")
    return _scorer
def score_candidate(candidate_dict):
    scorer = get_scorer()
    return scorer.score(candidate_dict)
def rank_candidates(candidate_dicts):
    scorer = get_scorer()
    return scorer.rank(candidate_dicts)
