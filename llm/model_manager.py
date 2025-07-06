"""LLM model manager for SmallHands.

Implements the cascading and self-correction logic described in the architecture.
"""

from typing import Any, Callable, Dict, List, Optional
import time

# A placeholder for the actual model interface
class LanguageModel:
    def complete(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        # This would contain the actual API call to a service like OpenAI
        # For now, it's a placeholder.
        print(f"--- MODEL CALL ---\nPROMPT: {prompt}\nCONTEXT: {context}\n--- END MODEL CALL ---")
        return f"LLM response to: {prompt}"

class ModelManager:
    def __init__(
        self,
        orchestrator_model: LanguageModel,
        worker_model: LanguageModel,
        max_correction_attempts: int = 3
    ):
        """
        Initializes the ModelManager.

        Args:
            orchestrator_model: A smaller, faster model for planning and routing.
            worker_model: A more powerful, potentially slower model for code generation and complex tasks.
            max_correction_attempts: The maximum number of times to attempt self-correction.
        """
        self.orchestrator_model = orchestrator_model
        self.worker_model = worker_model
        self.max_correction_attempts = max_correction_attempts

    def plan_task(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Uses the orchestrator model to generate a high-level plan.
        This is for breaking down a user query into a task graph.
        """
        # In a real scenario, the prompt would be more structured.
        return self.orchestrator_model.complete(prompt, context)

    def execute_task(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        test_fn: Optional[Callable[[str], Dict]] = None
    ) -> str:
        """
        Uses the worker model to execute a specific task, like generating code.
        If a test function is provided, it will enter a self-correction loop.

        Args:
            prompt: The prompt for the worker model.
            context: Supporting context (e.g., code snippets, memory).
            test_fn: An optional function that takes the generated code and returns a dict
                     with a 'success' boolean and an 'output' string.

        Returns:
            The final, validated code or output from the model.
        """
        if test_fn:
            return self._self_correction_loop(prompt, context, test_fn)
        else:
            return self.worker_model.complete(prompt, context)

    def _self_correction_loop(
        self,
        initial_prompt: str,
        context: Optional[Dict[str, Any]],
        test_fn: Callable[[str], Dict]
    ) -> str:
        """
        Manages the self-correction loop for code generation.
        """
        current_prompt = initial_prompt
        current_context = context.copy() if context else {}

        for attempt in range(self.max_correction_attempts):
            print(f"Self-correction attempt {attempt + 1}/{self.max_correction_attempts}")
            code_or_output = self.worker_model.complete(current_prompt, current_context)

            test_result = test_fn(code_or_output)

            if test_result.get("success"):
                print("Self-correction successful.")
                return code_or_output

            print("Test failed. Feeding back error for correction.")
            feedback = test_result.get("output", "No feedback provided.")
            
            # Update context and prompt for the next attempt
            current_context['previous_code'] = code_or_output
            current_context['test_feedback'] = feedback
            current_prompt = (
                "The previous attempt failed. Please fix the code based on the following feedback."
            )

        print("Self-correction failed after maximum attempts.")
        # Return the last failing output or raise an exception
        return code_or_output

    def ensemble_vote(self, prompts: List[str], voter_fn: Callable[[List[str]], Dict[str, int]]) -> str:
        """
        Generates multiple outputs for the same prompt and selects the best via a voter function.
        """
        outputs = [self.worker_model.complete(p) for p in prompts]
        votes = voter_fn(outputs)
        return max(votes, key=votes.get)
