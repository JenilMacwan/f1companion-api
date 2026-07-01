"""
Centralized logging configuration.

Provides a shared logger for the entire application, replacing ad-hoc
print() statements with structured logging.
"""

import logging

# Create the application-wide logger
logger = logging.getLogger("f1companion")
logger.setLevel(logging.INFO)

# Console handler with a clean format
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
