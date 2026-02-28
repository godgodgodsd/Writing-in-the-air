"""
Enterprise Logger
Production-grade structured logging.
"""

import logging
import os

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
