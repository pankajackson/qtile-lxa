import subprocess
from pathlib import Path
import json
from libqtile.log_utils import logger
from .colors import color_schemes
from .decorations import decorations
from typing import Any
from qtile_lxa import __DEFAULTS__


class ThemeConfig:
    def __init__(
        self,
        config: dict[Any, Any] | None = None,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        **kwargs: Any,
    ):
        self.config = config
        self.config_file = config_file
        self.default_config = {
            "wallpaper": {
                "source_id": None,
                "sources": {},
            },
            "color": {
                "scheme": list(color_schemes.keys())[0],
                "rainbow": False,
            },
            "bar": {
                "split": False,
                "transparent": False,
            },
            "decoration": list(decorations.keys())[0],
            "video_wallpaper": {
                "playlist": None,
                "song": None,
                "mute": True,
                "loop": True,
                "enabled": False,
            },
        }

    def save_config(self, config: dict):
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error("Failed to save config: %s", e)

    def load_config(self):
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(
                "Failed to load theme config, Initializing default config: %s",
                e,
            )
            self.save_config(self.default_config)
            return self.default_config

    def reload_qtile(self):
        subprocess.run(["qtile", "cmd-obj", "-o", "cmd", "-f", "reload_config"])
