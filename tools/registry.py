"""Tool registry for SmallHands."""
from .dev_tools import run_tests, lint_code, format_code, search_repo, commit_git, create_pr
from .static_analysis import semgrep_scan, bandit_scan

TOOLS = {
    "run_tests": run_tests,
    "lint_code": lint_code,
    "format_code": format_code,
    "search_repo": search_repo,
    "commit_git": commit_git,
    "create_pr": create_pr,
    "semgrep_scan": semgrep_scan,
    "bandit_scan": bandit_scan,
}

class ToolRegistry:
    """Registry for available tools."""
    def __init__(self):
        self.tools = TOOLS

    def get_tool(self, name: str):
        return self.tools.get(name)

    def get_tool_definitions_str(self) -> str:
        return "\n".join([f"{name}: {fn.__doc__ or ''}" for name, fn in self.tools.items()])

def get_tool(name: str):
    return TOOLS.get(name)
