"""Bayesian Knowledge Tracing — used by Django quiz submission and ML service."""
from dataclasses import dataclass
from typing import List


@dataclass
class BKTParams:
    p_init: float = 0.10
    p_transit: float = 0.20
    p_slip: float = 0.08
    p_guess: float = 0.20


DEFAULT_PARAMS = {
    "python_ml": BKTParams(p_init=0.30, p_transit=0.25, p_slip=0.05, p_guess=0.15),
    "statistics": BKTParams(p_init=0.15, p_transit=0.18, p_slip=0.08, p_guess=0.20),
    "linear_algebra": BKTParams(p_init=0.12, p_transit=0.15, p_slip=0.08, p_guess=0.18),
    "regression": BKTParams(p_init=0.20, p_transit=0.22, p_slip=0.07, p_guess=0.20),
    "classification": BKTParams(p_init=0.20, p_transit=0.22, p_slip=0.07, p_guess=0.20),
    "gradient_descent": BKTParams(p_init=0.08, p_transit=0.15, p_slip=0.10, p_guess=0.18),
    "neural_networks": BKTParams(p_init=0.06, p_transit=0.12, p_slip=0.10, p_guess=0.15),
    "ensemble_learning": BKTParams(p_init=0.12, p_transit=0.18, p_slip=0.08, p_guess=0.18),
    "evaluation_metrics": BKTParams(p_init=0.25, p_transit=0.28, p_slip=0.06, p_guess=0.22),
    "feature_engineering": BKTParams(p_init=0.20, p_transit=0.22, p_slip=0.07, p_guess=0.20),
    "clustering": BKTParams(p_init=0.15, p_transit=0.20, p_slip=0.08, p_guess=0.18),
    "pca": BKTParams(p_init=0.10, p_transit=0.15, p_slip=0.10, p_guess=0.15),
    "transformers": BKTParams(p_init=0.05, p_transit=0.10, p_slip=0.12, p_guess=0.12),
    "mlops": BKTParams(p_init=0.08, p_transit=0.15, p_slip=0.08, p_guess=0.15),
    "backpropagation": BKTParams(p_init=0.06, p_transit=0.12, p_slip=0.10, p_guess=0.15),
    "collaborative_filtering": BKTParams(p_init=0.12, p_transit=0.18, p_slip=0.08, p_guess=0.18),
    "causal_ml": BKTParams(p_init=0.05, p_transit=0.10, p_slip=0.10, p_guess=0.12),
    "reinforcement_learning": BKTParams(p_init=0.05, p_transit=0.10, p_slip=0.10, p_guess=0.12),
}


class BKTTracer:
    def __init__(self, params: BKTParams = None):
        self.params = params or BKTParams()

    def update(self, p_known: float, correct: bool) -> float:
        p = self.params
        p_obs_given_known = (1 - p.p_slip) if correct else p.p_slip
        p_obs_given_unknown = p.p_guess if correct else (1 - p.p_guess)
        p_obs = p_obs_given_known * p_known + p_obs_given_unknown * (1 - p_known)
        if p_obs == 0:
            return p_known
        p_known_post = (p_obs_given_known * p_known) / p_obs
        p_known_new = p_known_post + (1 - p_known_post) * p.p_transit
        return round(min(1.0, max(0.0, p_known_new)), 4)

    def estimate_from_history(self, response_history: List[bool], concept_tag: str) -> dict:
        params = DEFAULT_PARAMS.get(concept_tag, BKTParams())
        tracer = BKTTracer(params)
        trace = [params.p_init]
        for correct in response_history:
            trace.append(tracer.update(trace[-1], correct))
        final_p = trace[-1]
        n = len(response_history)
        correct = sum(response_history)
        return {
            "p_known": final_p,
            "mastery_score": final_p,
            "n_attempts": n,
            "n_correct": correct,
            "trace": trace,
        }
