import logging
from typing import override


class SafeFormatter(logging.Formatter):
    """Strip CR/LF from formatted log records to prevent log injection."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record).replace("\r", "").replace("\n", "")
