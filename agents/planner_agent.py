"""Planner agent for SmallHands."""

import json
from typing import Any, Dict

from .base import Agent
from controller.task_graph import TaskGraph
from llm.model_manager import ModelManager
from memory.hybrid_search import HybridSearch
from memory.semantic_indexer import SemanticIndexer

class PlannerAgent(Agent):
    """
    Agent that builds the initial task graph based on a high-level user query.
    """
    def __init__(
        self,
        model_manager: ModelManager,
        task_graph: TaskGraph,
        semantic_indexer: SemanticIndexer,
        memory: HybridSearch
    ):
        self.model_manager = model_manager
        self.task_graph = task_graph
        self.semantic_indexer = semantic_indexer
        self.memory = memory

    def _create_planning_prompt(self, query: str, context: str) -> str:
        """Creates the prompt for the orchestrator LLM to generate a task plan."""
        return f"""
Based on the following user query and context, please generate a detailed, step-by-step execution plan.
The plan should be a JSON array of objects, where each object represents a single, atomic task.
Each task object must have the following fields:
- "id": A short, unique, descriptive identifier for the task (e.g., "setup_project", "write_tests", "implement_feature").
- "description": A clear and concise description of what needs to be done for this task. This will be passed to a worker agent.
- "deps": A list of task IDs that must be completed before this task can start. Use an empty list for tasks with no dependencies.

The final output must be ONLY the JSON array, with no other text before or after it.

USER QUERY: "{query}"

CONTEXT:
---
{context}
---
"""

    def _decide_indexing(self, user_query: str) -> bool:
        """
        Decides whether to index the repository based on the user query.
        Uses a simple heuristic for now.
        """
        keywords = ["refactor", "debug", "add to", "analyze", "test", ".py"]
        return any(keyword in user_query.lower() for keyword in keywords)

    def run(self, user_query: str):
        """
        Takes a user query, generates a task plan, and populates the task graph.
        """
        print(f"PlannerAgent received query: {user_query}")

        if self._decide_indexing(user_query):
            print("Planner decided to index the repository.")
            self.semantic_indexer.index_repo()
            all_chunks = [chunk for chunks in self.semantic_indexer.index.values() for chunk in chunks]
            self.memory.index(all_chunks)
            # Retrieve relevant context from memory
            chunks = self.memory.search(user_query)
            relevant_context = "\n\n".join([chunk for chunk, _ in chunks]) or "No context available."
        else:
            print("Planner decided to skip indexing.")
            relevant_context = "No repository context available."

        prompt = self._create_planning_prompt(user_query, relevant_context)

        print("Generating task plan with orchestrator model...")
        plan_str = self.model_manager.plan_task(prompt)
        print(f"Received plan from LLM:\n{plan_str}")

        plan = json.loads(plan_str)

        if not isinstance(plan, list):
            print("Error: LLM did not return a JSON list. Cannot build task graph.")
            return

        print("Populating task graph...")
        for task_data in plan:
            self.task_graph.add_task(
                node_id=task_data['id'],
                task_fn=task_data['description'],
                deps=task_data.get('deps', [])
            )
        
        print(f"Task graph populated with {len(self.task_graph.nodes)} tasks.")
