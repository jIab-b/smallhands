"""Semantic indexer for code-aware chunking."""

from typing import List, Dict
import os

class SemanticIndexer:
    """Naive semantic indexer splitting code into chunks."""

    def __init__(self):
        self.index: Dict[str, List[str]] = {}

    def index_file(self, path: str) -> None:
        """Read file and split into semantic chunks."""
        with open(path, 'r') as f:
            content = f.read()
        chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
        self.index[path] = chunks

    def query(self, pattern: str) -> List[str]:
        """Return chunks containing the given pattern."""
        results = []
        for chunks in self.index.values():
            for chunk in chunks:
                if pattern in chunk:
                    results.append(chunk)
        return results

    def index_repo(self, root: str = ".") -> None:
        """Index all .py files in the repository into semantic chunks."""
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".py"):
                    path = os.path.join(dirpath, filename)
                    self.index_file(path)
