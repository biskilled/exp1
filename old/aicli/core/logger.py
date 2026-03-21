# core/logger.py

import os
import json
from datetime import datetime, timezone


class StructuredLogger:

    LEVELS = ["debug", "info", "warning", "error"]

    def __init__(self, config):

        self.log_level = config.get("log_level", "info")
        self.log_path = config.get("log_path", ".aicli/logs.jsonl")

        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def _should_log(self, level):
        return self.LEVELS.index(level) >= self.LEVELS.index(self.log_level)

    def log(self, level, event, **data):

        if not self._should_log(level):
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "data": data
        }

        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    # Convenience methods
    def debug(self, event, **data):
        self.log("debug", event, **data)

    def info(self, event, **data):
        self.log("info", event, **data)

    def warning(self, event, **data):
        self.log("warning", event, **data)

    def error(self, event, **data):
        self.log("error", event, **data)