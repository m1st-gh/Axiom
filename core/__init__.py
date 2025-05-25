"""
core
====

This package sets up a global logger for the bot, with colorized console output
and file logging. The logger is used throughout the bot and also overrides
the default Discord.py logger to ensure consistent formatting and log levels.

- Console logs are colorized for readability.
- File logs are plain text for persistence.
- Discord.py logs are set to WARNING level by default.
"""

import logging
import sys


# --- Color Formatter ---
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[37m",  # White
        logging.INFO: "\033[36m",  # Cyan
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


# --- Logger Setup ---
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler with color
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(
        ColorFormatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # File handler (no color)
    fh = logging.FileHandler("bot.log", encoding="utf-8", mode="w")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(ch)
    logger.addHandler(fh)

    # Overwrite discord.py's logger
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)
    for handler in discord_logger.handlers[:]:
        discord_logger.removeHandler(handler)
    discord_logger.addHandler(ch)
    discord_logger.addHandler(fh)

    return logger


# Global logger for the package
logger = setup_logger()
