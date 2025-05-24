import logging
import sys
from discord.utils import _ColourFormatter


# Configure root logger
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler with color formatting
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(_ColourFormatter())
    logger.addHandler(console_handler)

    # File handler for persistent logs
    file_handler = logging.FileHandler(filename="axiom.log", encoding="utf-8", mode="w")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    # Override discord's default logger
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)

    # Make handlers propagate to our custom logger
    for handler in discord_logger.handlers:
        discord_logger.removeHandler(handler)

    return logger


# Initialize global logger
logger = setup_logging()
