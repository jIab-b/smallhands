"""State models for SmallHands."""

import json
from pydantic import BaseModel
from typing import Any, Dict

class State(BaseModel):
    """
    Pydantic model capturing the planner agent's state.
    - task_status: mapping of node_id to completion flag
    - results: mapping of node_id to task result
    - environment: arbitrary context data
    - metadata: additional info (timestamps, logs)
    """
    task_status: Dict[str, bool] = {}
    results: Dict[str, Any] = {}
    environment: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    def mark_complete(self, node_id: str, result: Any) -> None:
        self.task_status[node_id] = True
        self.results[node_id] = result

    def is_complete(self) -> bool:
        return all(self.task_status.values())

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def save(self, path: str = "state.json") -> None:
        """Saves the current state to a JSON file."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def load(cls, path: str = "state.json") -> "State":
        """Loads the state from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)
