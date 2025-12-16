from dataclasses import dataclass, field, asdict, is_dataclass
import subprocess
from pathlib import Path
import json
from libqtile.log_utils import logger

from .color import ColorScheme
from .decoration import Decoration
from qtile_lxa import __DEFAULTS__


@dataclass
class WallpaperSource:
    group: str
    collection: str
    active_index: int
    wallpapers: list[str]


@dataclass
class Wallpaper:
    source_id: str | None = None
    sources: dict[str, WallpaperSource] = field(default_factory=dict)


@dataclass
class Color:
    schemes: ColorScheme = ColorScheme.PYWAL
    rainbow: bool = False


@dataclass
class Bar:
    split: bool = False
    transparent: bool = False


@dataclass
class VideoWallpaper:
    playlist: str | None = None
    song: str | None = None
    mute: bool = True
    loop: bool = True
    enabled: bool = False


@dataclass
class Theme:
    config_file: Path = __DEFAULTS__.theme_manager.config_path

    wallpaper: Wallpaper = field(default_factory=Wallpaper)
    color: Color = field(default_factory=Color)
    bar: Bar = field(default_factory=Bar)
    decoration: Decoration = Decoration.SLASH
    video_wallpaper: VideoWallpaper = field(default_factory=VideoWallpaper)

    def to_dict(self) -> dict:
        """Convert nested dataclasses to a JSON-safe dict."""
        raw = asdict(self)
        raw["decoration"] = self.decoration.name  # Store enum as string
        raw["color"]["schemes"] = self.color.schemes.name
        raw.pop("config_file", None)  # Do not save path
        return raw

    @staticmethod
    def from_dict(data: dict, config_file: Path):
        """Reconstruct Theme from JSON dict."""
        return Theme(
            config_file=config_file,
            wallpaper=Wallpaper(
                source_id=data["wallpaper"].get("source_id"),
                sources={
                    key: WallpaperSource(**src)
                    for key, src in data["wallpaper"].get("sources", {}).items()
                },
            ),
            color=Color(
                schemes=ColorScheme[data["color"]["schemes"]],
                rainbow=data["color"]["rainbow"],
            ),
            bar=Bar(**data["bar"]),
            decoration=Decoration[data["decoration"]],
            video_wallpaper=VideoWallpaper(**data["video_wallpaper"]),
        )

    def save(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.to_dict(), f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def load(self):
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)

            loaded = Theme.from_dict(data, self.config_file)

            # Update current object with loaded values
            self.wallpaper = loaded.wallpaper
            self.color = loaded.color
            self.bar = loaded.bar
            self.decoration = loaded.decoration
            self.video_wallpaper = loaded.video_wallpaper

            return self

        except Exception as e:
            logger.error(f"Failed to load theme config: {e}")
            self.save()  # Save defaults
            return self

    def reload_qtile(self):
        subprocess.run(["qtile", "cmd-obj", "-o", "cmd", "-f", "reload_config"])
