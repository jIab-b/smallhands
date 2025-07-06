"""Worker agent for SmallHands."""

import json
from typing import Any, Callable, Dict

from .base import Agent
from llm.model_manager import ModelManager
from memory.hybrid_search import HybridSearch
from memory.tool_exemplar_store import ToolExemplarStore
from sandbox.wsl_sandbox import WSLSandbox
from tools.registry import ToolRegistry

class WorkerAgent(Agent):
    """
    Executes a single, specific task from the task graph using a suite of tools.
    """
    def __init__(
        self,
        model_manager: ModelManager,
        memory: HybridSearch,
        tool_exemplar_store: ToolExemplarStore,
        sandbox: WSLSandbox,
        tool_registry: ToolRegistry,
    ):
        self.model_manager = model_manager
        self.memory = memory
        self.tool_exemplar_store = tool_exemplar_store
        self.sandbox = sandbox
        self.tool_registry = tool_registry

    def _create_tool_selection_prompt(self, task_description: str, context: str, tools: str, exemplars: list) -> str:
        """Creates the prompt for the worker LLM to select a tool and its arguments."""
        exemplar_str = "\n".join([f"- Task: {e['task']}\n  Tool Call: {e['tool_call']}" for e in exemplars])
        return f"""
You are a worker agent responsible for executing a task. Based on the task description, context, and available tools, select the single best tool to use.
Your output must be a single JSON object with two fields:
- "tool_name": The name of the tool to use (e.g., "run_tests", "lint_code").
- "args": A dictionary of arguments to pass to the tool.

Here are some examples of successful past tool uses:
---
{exemplar_str}
---

TASK DESCRIPTION: "{task_description}"

AVAILABLE TOOLS:
---
{tools}
---

CONTEXT:
---
{context}
---

Your response must be ONLY the JSON object.
"""

    def run(self, task_description: str) -> str:
        """
        Executes a single task.

        Args:
            task_description: The description of the task from the TaskGraph node.

        Returns:
            A string representing the result of the task execution.
        """
        print(f"WorkerAgent received task: {task_description}")

        # 1. Gather context
        # Retrieve relevant context from memory
        chunks = self.memory.search(task_description)
        relevant_context = "\n\n".join(chunk for chunk, _ in chunks) or "No context available."
        available_tools = self.tool_registry.get_tool_definitions_str()

        # 2. Select tool using the LLM
        exemplars = self.tool_exemplar_store.get_exemplars(task_description, k=3)
        prompt = self._create_tool_selection_prompt(task_description, relevant_context, available_tools, exemplars)
        print("Selecting tool with worker model...")
        tool_call_str = self.model_manager.execute_task(prompt)
        print(f"Received tool call from LLM: {tool_call_str}")

        # 3. Execute the tool
        tool_call = json.loads(tool_call_str)
        tool_name = tool_call.get("tool_name")
        tool_args = tool_call.get("args", {})

        tool_fn = self.tool_registry.get_tool(tool_name)
        if not tool_fn:
            error_msg = f"Error: LLM selected a non-existent tool: {tool_name}"
            print(error_msg)
            return error_msg

        print(f"Executing tool '{tool_name}' with args: {tool_args}")
        with self.sandbox as sb:
            execution_result = sb.run(tool_fn, **tool_args)
        self.tool_exemplar_store.add_exemplar(task_description, tool_call, execution_result)
        print(f"Task finished. Result: {execution_result}")
        return execution_result
