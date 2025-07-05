"""WSL sandbox for SmallHands."""

import os
import shutil
import tempfile
import subprocess

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
        return fn(*args, **kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.work_dir, ignore_errors=True)
