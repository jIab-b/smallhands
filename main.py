"""
SmallHands: Main entry point for the lean code assistant.
"""
import os
import sys
import json
from llm.openai_model import OpenAIModel
from sandbox.wsl_sandbox import WSLSandbox
from tools.registry import ToolRegistry
from observability.logger import Logger
from observability.guardrails import Guardrails

class ToolAgent:
    """
    A simple agent that selects and executes a single tool based on a user prompt.
    """
    def __init__(self, model: OpenAIModel, tool_registry: ToolRegistry, sandbox: WSLSandbox):
        self.model = model
        self.tool_registry = tool_registry
        self.sandbox = sandbox

    def _create_prompt(self, query: str, tools: str) -> str:
        """Creates a prompt for the LLM to select a tool."""
        return f"""
You are a helpful AI assistant. Your goal is to select the best tool to respond to the user's query.
Your output must be a single JSON object with two fields:
- "tool_name": The name of the tool to use.
- "args": A dictionary of arguments to pass to the tool.

USER QUERY: "{query}"

AVAILABLE TOOLS:
---
{tools}
---

Your response must be ONLY the JSON object.
"""

    def _clean_llm_response(self, response: str) -> str:
        """Strips markdown fences from the LLM's JSON output."""
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()

    def run(self, query: str) -> dict:
        """Selects and runs a tool, returning the result."""
        available_tools = self.tool_registry.get_tool_definitions_str()
        prompt = self._create_prompt(query, available_tools)
        
        print("Selecting tool with model...")
        llm_response = self.model.complete(prompt)
        print(f"Received tool call from LLM: {llm_response}")

        cleaned_response = self._clean_llm_response(llm_response)
        
        try:
            tool_call = json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {"success": False, "output": "Error: LLM returned invalid JSON."}

        tool_name = tool_call.get("tool_name")
        tool_args = tool_call.get("args", {})
        
        tool_fn = self.tool_registry.get_tool(tool_name)
        if not tool_fn:
            return {"success": False, "output": f"Error: LLM selected a non-existent tool: {tool_name}"}

        print(f"Executing tool '{tool_name}' with args: {tool_args}")
        with self.sandbox as sb:
            execution_result = sb.run(tool_fn, **tool_args)
        
        print(f"Task finished. Result: {execution_result}")
        return execution_result

def main():
    """Main application loop."""
    logger = Logger("smallhands")
    guard = Guardrails()
    
    # Initialize core components
    model = OpenAIModel(os.getenv("OPENAI_MODEL", "o4-mini"))
    tool_registry = ToolRegistry()
    sandbox = WSLSandbox()
    agent = ToolAgent(model, tool_registry, sandbox)

    # Get user query from command line or input
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = input("Enter your task: ")

    guard.validate_input(user_query)
    logger.log("query_start", query=user_query)

    # Run the agent and get the result
    result = agent.run(user_query)
    guard.validate_output(result)

    logger.log("query_complete", result=result)
    print("\n--- Final Result ---")
    print(result.get('output', 'No output from tool.'))
    print("--------------------")

if __name__ == "__main__":
    main()
