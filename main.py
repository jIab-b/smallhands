"""
SmallHands: Main entry point
"""
import os
from controller.task_graph import TaskGraph
from controller.state import State
from execution.local_executor import LocalExecutor
from llm.openai_model import OpenAIModel
from llm.model_manager import ModelManager
from memory.vector_store import FaissVectorStore
from memory.semantic_indexer import SemanticIndexer
from memory.hybrid_search import HybridSearch
from memory.tool_exemplar_store import ToolExemplarStore
from sandbox.wsl_sandbox import WSLSandbox
from observability.logger import Logger
from observability.guardrails import Guardrails
import sys
from agents.planner_agent import PlannerAgent
from agents.worker_agent import WorkerAgent
from tools.registry import ToolRegistry

def main():
    logger = Logger("smallhands")
    guard = Guardrails()
    state_file = "state.json"
    if os.path.exists(state_file):
        state = State.load(state_file)
    else:
        state = State()
    tg = TaskGraph()

    orchestrator_llm = OpenAIModel(os.getenv("OPENAI_MODEL", "o4-mini"))
    worker_llm = OpenAIModel(os.getenv("WORKER_MODEL", "gpt-4.1-mini"))
    model_manager = ModelManager(orchestrator_llm, worker_llm)

    vector_store = FaissVectorStore()
    semantic_indexer = SemanticIndexer()
    hybrid_search = HybridSearch()
    exemplar_store = ToolExemplarStore()

    sandbox = WSLSandbox()
    executor = LocalExecutor()

    # Index repository code into memory for context
    semantic_indexer.index_repo()
    all_chunks = [chunk for chunks in semantic_indexer.index.values() for chunk in chunks]
    hybrid_search.index(all_chunks)

    # Initialize tool registry and agents
    tool_registry = ToolRegistry()
    planner_agent = PlannerAgent(model_manager, tg, hybrid_search)
    worker_agent = WorkerAgent(model_manager, hybrid_search, exemplar_store, sandbox, tool_registry)

    # Obtain user query
    if len(sys.argv) > 1:
        user_query = sys.argv[1]
    else:
        user_query = input("Enter your task: ")

    guard.validate_input(user_query)
    logger.log("plan_start", query=user_query)

    # Build task graph from user query
    planner_agent.run(user_query)
    logger.log("plan_complete", tasks=list(tg.nodes.keys()))

    while not tg.is_complete():
        for node in tg.get_ready_tasks():
            task_desc = node.task_fn
            async_res = executor.submit(worker_agent.run, task_desc)
            result = async_res.get()
            guard.validate_output(result)

            # Self-correction logic
            if "run_tests" in task_desc and not result.get("success"):
                failure_log = result.get("output")
                fix_task_desc = f"The tests failed. Read the following test output and fix the code to make the tests pass:\n{failure_log}"
                
                # Assume the previous node was the code generation task
                code_gen_node_id = node.deps[0]
                
                # Create a new node for the fix task
                fix_node_id = f"fix_{code_gen_node_id}"
                tg.add_task(fix_node_id, fix_task_desc, deps=[code_gen_node_id])
                
                logger.log("self_correction_triggered", failed_task=node.node_id, fix_task=fix_node_id)
            else:
                state.mark_complete(node.node_id, result)
                state.save(state_file)
                tg.mark_complete(node.node_id, result)

            logger.log("task_complete", task=node.node_id, result=result)

    executor.shutdown()
    logger.log("workflow_complete", tasks=list(state.task_status.keys()))

if __name__ == "__main__":
    main()
