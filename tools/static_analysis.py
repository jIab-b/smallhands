"""Static analysis tools for SmallHands."""

import subprocess

def semgrep_scan(path: str = ".") -> dict:
    result = subprocess.run(["semgrep", "--config", "auto", path], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}

def bandit_scan(path: str = ".") -> dict:
    result = subprocess.run(["bandit", "-r", path, "-f", "json"], capture_output=True, text=True)
    return {"success": result.returncode == 0, "output": result.stdout + result.stderr}
