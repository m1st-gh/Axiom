import json
from pathlib import Path
from typing import List, Optional

class Config:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Config, cls).__new__(cls)
        return cls.__instance

    def __init__(self, config_file: Optional[Path] = None):
        if hasattr(self, '_initialized'):
            return
        if config_file is None:
            config_file = Path(__file__).parent.parent / 'config.json'
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        self.discord_api_token: str = config_data['discord_api_token']
        self.openrouter_api_token: str = config_data['openrouter_api_token']
        self.guild_ids: List[int] = config_data['guild_ids']
        self.model: str = config_data['model']
        self.max_tokens: int = config_data['max_tokens']
        self._initialized = True

# Global instance
config = Config()
