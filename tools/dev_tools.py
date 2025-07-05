"""Core dev tools."""
import subprocess

def run_tests():
    result = subprocess.run(["pytest"], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def lint_code():
    result = subprocess.run(["flake8"], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def format_code():
    result = subprocess.run(["black", "."], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def search_repo(query):
    return []

def commit_git(message):
    result = subprocess.run(["git", "commit", "-am", message], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def create_pr(branch):
    return {"success": False, "output": "create_pr not implemented"}
