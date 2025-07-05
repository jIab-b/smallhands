"""Stores examples of successful tool use."""

from typing import Any, List, Dict

class ToolExemplarStore:
    """In-memory store for task, tool_call, and result tuples."""

    def __init__(self):
        self.exemplars: List[Dict[str, Any]] = []

    def add_exemplar(self, task: str, tool_call: Dict[str, Any], result: Any) -> None:
        self.exemplars.append({'task': task, 'tool_call': tool_call, 'result': result})

    def query(self, task: str) -> List[Dict[str, Any]]:
        return [e for e in self.exemplars if e['task'] == task]
