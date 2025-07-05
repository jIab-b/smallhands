"""LLM model manager."""

from typing import Any, List, Dict

class ModelManager:
    def __init__(self, planner_model: Any, synthesizer_model: Any):
        self.planner_model = planner_model
        self.synthesizer_model = synthesizer_model

    def route_task(self, prompt: str, context: Dict[str, Any]) -> str:
        """use planner model"""
        return self.planner_model.complete(prompt, context)

    def self_correction_loop(self, code: str, test_fn: Any) -> str:
        result = test_fn(code)
        if not result['success']:
            feedback = result['output']
            return self.synthesizer_model.complete(code, {'feedback': feedback})
        return code

    def ensemble_vote(self, prompts: List[str], voter_fn: Any) -> str:
        outputs = [self.synthesizer_model.complete(p) for p in prompts]
        votes = voter_fn(outputs)
        return max(votes, key=votes.get)
