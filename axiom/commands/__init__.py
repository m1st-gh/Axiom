import os
import importlib
from discord.ext import commands

from axiom import logger


async def load_commands(bot: commands.Bot):
    """Load all command modules from the commands directory."""
    current_dir = os.path.dirname(__file__)
    command_modules = [
        filename[:-3]
        for filename in os.listdir(current_dir)
        if filename.endswith(".py") and filename != "__init__.py"
    ]

    for module_name in command_modules:
        try:
            module_path = f"axiom.commands.{module_name}"
            module = importlib.import_module(module_path)
            await module.setup(bot)
            logger.info(f"Loaded command module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to load command module {module_name}: {e}")
