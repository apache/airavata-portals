import logging


class SafeFormatter(logging.Formatter):
    """Strip CR/LF from formatted log records to prevent log injection."""

    def format(self, record):
        return super().format(record).replace('\r', '').replace('\n', '')
