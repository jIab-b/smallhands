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

def get_tool(name: str):
    return TOOLS.get(name)
