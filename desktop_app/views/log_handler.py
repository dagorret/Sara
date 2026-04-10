from __future__ import annotations

import logging


class QtLogHandler(logging.Handler):
    def __init__(self, append_callback) -> None:
        super().__init__()
        self.append_callback = append_callback
        self.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        self.append_callback(message)
