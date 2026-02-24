"""
Enterprise Logger
Production-grade structured logging.
"""

import logging
import os
from datetime import datetime


class Logger:

    _instance = None

    @staticmethod
    def get():
        if Logger._instance is None:
            Logger._instance = Logger()
        return Logger._instance

    def __init__(self):
        if Logger._instance is not None:
            return

        self.logger = logging.getLogger("EnterpriseAIPaint")
        self.logger.setLevel(logging.DEBUG)

        os.makedirs("logs", exist_ok=True)
        filename = datetime.now().strftime("logs/session_%Y%m%d_%H%M%S.log")

        file_handler = logging.FileHandler(filename)
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)

class AppLogger:

    def __init__(self):
        os.makedirs("logs", exist_ok=True)

        logging.basicConfig(
            filename="logs/app.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    @staticmethod
    def info(msg):
        logging.info(msg)

    @staticmethod
    def error(msg):
        logging.error(msg)