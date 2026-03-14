"""
Enterprise Logger
Production-grade structured logging with rotation.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


class AppLogger:
    def __init__(
        self,
        log_dir="logs",
        log_file="app.log",
        level=logging.INFO,
        max_bytes=5 * 1024 * 1024,
        backup_count=5,
        console=False,
    ):
        os.makedirs(log_dir, exist_ok=True)
        self.log_path = os.path.join(log_dir, log_file)
        self.logger = logging.getLogger("enterprise_ai_paint")
        self.logger.setLevel(level)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )

            file_handler = RotatingFileHandler(
                self.log_path, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            if console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def exception(self, msg):
        self.logger.exception(msg)

    def get_logger(self):
        return self.logger

    def clear_logs(self):
        for handler in list(self.logger.handlers):
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass
            try:
                self.logger.removeHandler(handler)
            except Exception:
                pass

        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except Exception:
                pass

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        file_handler = RotatingFileHandler(
            self.log_path, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
