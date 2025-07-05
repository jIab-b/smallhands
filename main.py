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

def main():
    logger = Logger("smallhands")
    guard = Guardrails()
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

    def sample_task(task_id: str):
        guard.validate_input(task_id)
        logger.log("task_start", task=task_id)
        result = f"Executed {task_id}"
        logger.log("task_end", task=task_id, result=result)
        guard.validate_output(result)
        return result

    tg.add_task("task1", sample_task)
    tg.add_task("task2", sample_task, deps=["task1"])

    while not tg.is_complete():
        for node in tg.get_ready_tasks():
            async_res = executor.submit(node.task_fn, node.node_id)
            result = async_res.get()
            state.mark_complete(node.node_id, result)
            tg.mark_complete(node.node_id, result)

    executor.shutdown()
    logger.log("workflow_complete", tasks=list(state.task_status.keys()))

if __name__ == "__main__":
    main()
