"""Core dev tools."""
import subprocess

def run_tests():
    """Run pytest suite and return results."""
    result = subprocess.run(["pytest"], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def lint_code():
    """Run flake8 lint and return results."""
    result = subprocess.run(["flake8"], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def format_code():
    """Run Black formatter across the repository."""
    result = subprocess.run(["black", "."], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def search_repo(query: str) -> dict:
    """Search repository for a query using grep."""
    result = subprocess.run(["grep", "-R", query, "."], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout}

def commit_git(message: str) -> dict:
    """Commit staged changes with a commit message."""
    result = subprocess.run(["git", "commit", "-am", message], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

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
