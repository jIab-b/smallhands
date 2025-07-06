"""WSL sandbox for SmallHands."""

import os
import shutil
import tempfile
import subprocess
from typing import List

class WSLSandbox:
    """Baseline sandbox using temporary workspace and optional cache mount."""

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or os.getenv("WSL_CACHE_DIR", "/mnt/cache")
        self.work_dir = None

    def __enter__(self):
        self.work_dir = tempfile.mkdtemp(prefix="smallhands_")
        # copy repository state excluding .git to sandbox
        src = os.getcwd()
        dst = self.work_dir
        subprocess.run(["rsync", "-a", "--exclude", ".git", f"{src}/", f"{dst}/"])
        return self

    def run(self, fn, *args, **kwargs):
        """
        Execute a function within the sandbox context.
        """
        current_dir = os.getcwd()
        os.chdir(self.work_dir)
        try:
            return fn(*args, **kwargs)
        finally:
            os.chdir(current_dir)

    def run_shell(self, cmd: List[str], capture_output: bool = True, text: bool = True) -> subprocess.CompletedProcess:
        """
        Execute a shell command within the sandbox workspace.
        """
        return subprocess.run(cmd, cwd=self.work_dir, capture_output=capture_output, text=text)

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.work_dir, ignore_errors=True)
