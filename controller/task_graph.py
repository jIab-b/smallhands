"""DAG engine for SmallHands tasks."""

from collections import defaultdict
from typing import Any, Callable, Dict, List, Set

class TaskNode:
    def __init__(self, node_id: str, task_fn: Callable[..., Any], deps: List[str] = None):
        self.node_id = node_id
        self.task_fn = task_fn
        self.deps = deps or []
        self.completed = False
        self.result = None

class TaskGraph:
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.dependents: Dict[str, Set[str]] = defaultdict(set)

    def add_task(self, node_id: str, task_fn: Callable[..., Any], deps: List[str] = None):
        if node_id in self.nodes:
            return
        self.nodes[node_id] = TaskNode(node_id, task_fn, deps)
        for dep in deps or []:
            self.dependents[dep].add(node_id)

    def get_ready_tasks(self) -> List[TaskNode]:
        return [
            node for node in self.nodes.values()
            if not node.completed and all(self.nodes[dep].completed for dep in node.deps)
        ]

    def mark_complete(self, node_id: str, result: Any):
        node = self.nodes.get(node_id)
        if node:
            node.completed = True
            node.result = result

    def is_complete(self) -> bool:
        return all(node.completed for node in self.nodes.values())
