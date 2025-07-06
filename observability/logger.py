"""Structured JSON logger for SmallHands."""

import json
import logging
from datetime import datetime

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        self.logger.addHandler(handler)

    def log(self, event: str, **data):
         record = {"timestamp": datetime.utcnow().isoformat(), "event": event, **data}
         self.logger.info(json.dumps(record))
