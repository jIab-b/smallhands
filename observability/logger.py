"""Structured JSON logger for SmallHands."""

import json
import logging

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        self.logger.addHandler(handler)

    def log(self, event: str, **data):
        record = {"event": event, **data}
        self.logger.info(json.dumps(record))
