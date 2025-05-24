import os
import sys
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for the Axiom bot."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        load_dotenv()
        self._config = {}
        self._initialized = True

    def require_env_vars(self, *names: str) -> Dict[str, Any]:
        """Load required environment variables, exit if any are missing."""
        missing_vars: List[str] = []

        for name in names:
            value = os.getenv(name)
            if value is None:
                missing_vars.append(name)
            else:
                # Parse comma-separated values as lists
                if "," in value:
                    self._config[name] = [item.strip() for item in value.split(",")]
                else:
                    self._config[name] = value

        if missing_vars:
            error_message = (
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            print(f"CRITICAL: {error_message}", file=sys.stderr)
            sys.exit(1)

        return self._config

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def get_guild_ids(self) -> List[int]:
        """Get guild IDs as integers."""
        guild_id_value = self._config.get("DISCORD_GUILD_ID")

        try:
            if isinstance(guild_id_value, list):
                return [int(gid) for gid in guild_id_value]
            else:
                return [int(guild_id_value)]
        except ValueError:
            print("CRITICAL: DISCORD_GUILD_ID must be integer(s).", file=sys.stderr)
            sys.exit(1)


# Create a singleton instance
config = Config()
