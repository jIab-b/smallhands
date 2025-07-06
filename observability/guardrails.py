"""Guardrails for SmallHands."""

import re
import json

class Guardrails:
    """Validates inputs and outputs for safety and compliance."""

    def __init__(self):
        self.forbidden_patterns = [
            r"rm\s+-rf",
            r"import\s+os",
            r"subprocess",
        ]

    def validate_input(self, data):
        s = str(data)
        for pat in self.forbidden_patterns:
            if re.search(pat, s):
                raise ValueError(f"Input contains forbidden pattern: {pat}")

    def validate_output(self, data):
        s = str(data)
        for pat in self.forbidden_patterns:
            if re.search(pat, s):
                raise ValueError(f"Output contains forbidden pattern: {pat}")

    def validate_json(self, data: str):
        """Validate that a string is valid JSON."""
        try:
            json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON output: {e}")
