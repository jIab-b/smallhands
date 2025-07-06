# SmallHands Implementation Plan

This document outlines the concrete steps required to address the architectural gaps identified during the project evaluation. The goal is to implement the missing features for state management, intelligent tool use, self-correction, and end-to-end tooling.

## 1. Implement State Persistence and Resumability

**Objective**: Make the system resilient to interruptions by saving and loading the application state.

### 1.1. Enhance `State` Class

The `controller/state.py` file will be modified to include `save` and `load` methods. We will use JSON for simple, human-readable serialization.

**File to Modify**: [`controller/state.py`](controller/state.py)

**Proposed Changes**:
```python
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
```

### 1.2. Update `main.py` to Manage State

The main entry point will be updated to load state if it exists and save it after every task completion.

**File to Modify**: [`main.py`](main.py)

**Proposed Changes**:
- At startup, check for `state.json` and load it.
- In the main execution loop, call `state.save()` after `state.mark_complete()`.

```python
# In main()
state_file = "state.json"
if os.path.exists(state_file):
    state = State.load(state_file)
else:
    state = State()

# ... inside the while loop ...
state.mark_complete(node.node_id, result)
state.save(state_file) # Persist state after each task
tg.mark_complete(node.node_id, result)
```

## 2. Enhance Tool Selection with Exemplars

**Objective**: Improve tool selection accuracy by providing the LLM with examples of successful past tool usage.

### 2.1. Modify `WorkerAgent`

The `agents/worker_agent.py` will be updated to query the `ToolExemplarStore` and inject the retrieved exemplars into the prompt.

**File to Modify**: [`agents/worker_agent.py`](agents/worker_agent.py)

**Proposed Changes**:
- The `run` method will first query the `tool_exemplar_store`.
- The `_create_tool_selection_prompt` method will be updated to include these exemplars.

```python
# In WorkerAgent.run()
exemplars = self.tool_exemplar_store.get_exemplars(task_description, k=3)
prompt = self._create_tool_selection_prompt(task_description, relevant_context, available_tools, exemplars)

# In WorkerAgent._create_tool_selection_prompt()
def _create_tool_selection_prompt(self, task_description: str, context: str, tools: str, exemplars: list) -> str:
    exemplar_str = "\n".join([f"- Task: {e['task']}\n  Tool Call: {e['tool_call']}" for e in exemplars])
    return f"""
You are a worker agent...
Your output must be a single JSON object...

Here are some examples of successful past tool uses:
---
{exemplar_str}
---

TASK DESCRIPTION: "{task_description}"
...
"""
```

## 3. Introduce a Self-Correction Loop

**Objective**: Enable the agent to autonomously detect and fix errors, particularly from running tests.

### 3.1. Update `main.py` Execution Loop

The main loop in `main.py` will be modified to inspect the result of a task. If a task was to run tests and the tests failed, it will generate a new "fix" task and add it to the task graph.

**File to Modify**: [`main.py`](main.py)

**Proposed Workflow**:

```mermaid
graph TD
    A[Start Task] --> B{Is tool `run_tests`?};
    B -- No --> C[Mark Task Complete];
    B -- Yes --> D{Did tests succeed?};
    D -- Yes --> C;
    D -- No --> E[Generate "fix the code" task];
    E --> F[Add new task to TaskGraph];
    F --> G[Continue Execution];
    C --> G;
```

**Proposed Changes**:
```python
# In main() while loop
result = async_res.get()
guard.validate_output(result)

# Self-correction logic
if node.tool_name == "run_tests" and not result.get("success"):
    failure_log = result.get("output")
    fix_task_desc = f"The tests failed. Read the following test output and fix the code to make the tests pass:\n{failure_log}"
    
    # Assume the previous node was the code generation task
    code_gen_node_id = tg.get_predecessors(node.node_id)[0] 
    
    # Create a new node for the fix task
    fix_node = tg.add_node(f"fix_{code_gen_node_id}", fix_task_desc)
    
    # Add dependency
    tg.add_edge(code_gen_node_id, fix_node.node_id)
    
    logger.log("self_correction_triggered", failed_task=node.node_id, fix_task=fix_node.node_id)
else:
    state.mark_complete(node.node_id, result)
    state.save(state_file)
    tg.mark_complete(node.node_id, result)

logger.log("task_complete", task=node.node_id, result=result)
```

## 4. Complete the Toolchain for End-to-End Execution

**Objective**: Implement the `create_pr` tool to allow the agent to complete a full development workflow.

### 4.1. Implement `create_pr` Tool

The `tools/dev_tools.py` file will be updated with a functional `create_pr` tool. This implementation will use the official GitHub CLI (`gh`).

**File to Modify**: [`tools/dev_tools.py`](tools/dev_tools.py)

**Proposed Changes**:
```python
def create_pr(title: str, body: str, branch: str) -> dict:
    """Create a pull request using the GitHub CLI."""
    try:
        # Ensure the branch is pushed to remote
        subprocess.run(["git", "push", "origin", branch], check=True, capture_output=True, text=True)
        
        # Create the pull request
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body, "--head", branch],
            check=True, capture_output=True, text=True
        )
        return {"success": True, "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "output": e.stderr}

# Update the old placeholder function
# def create_pr(branch: str) -> dict:
#     """Create a pull request (not implemented)."""
#     # Placeholder for future GitHub/GitLab integration
#     return {"success": False, "output": "create_pr not implemented"}
```

This plan provides a clear roadmap to significantly improve the SmallHands system. Once you approve this plan, I can switch to a code-focused mode to begin implementation.