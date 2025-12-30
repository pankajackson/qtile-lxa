from dataclasses import dataclass, field, asdict, is_dataclass
import subprocess
from pathlib import Path
import json
from libqtile.log_utils import logger
from typing import TypeAlias
from collections.abc import Callable

from .color import ColorScheme
from .decoration import Decoration
from qtile_lxa import __DEFAULTS__
from qtile_lxa.utils.process_lock import ProcessLocker
from qtile_lxa.utils.atomic_writer import atomic_write_content


@dataclass
class WallpaperSource:
    active_index: int
    wallpapers: list[str]
    group: str | None = None
    collection: str | None = None


@dataclass
class Wallpaper:
    source_id: str | None = None
    sources: dict[str, WallpaperSource] = field(default_factory=dict)


@dataclass
class Color:
    scheme: ColorScheme = ColorScheme.PYWAL
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
    _locker = ProcessLocker(str(config_file))

    def to_dict(self) -> dict:
        """Convert nested dataclasses to a JSON-safe dict."""
        raw = asdict(self)
        raw["decoration"] = self.decoration.name  # Store enum as string
        raw["color"]["scheme"] = self.color.scheme.name
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
                scheme=ColorScheme[data["color"]["scheme"]],
                rainbow=data["color"]["rainbow"],
            ),
            bar=Bar(**data["bar"]),
            decoration=Decoration[data["decoration"]],
            video_wallpaper=VideoWallpaper(**data["video_wallpaper"]),
        )

    def _save_unlocked(self):
        try:
            atomic_write_content(self.config_file, self.to_dict())
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    @_locker
    def save(self):
        self._save_unlocked()

    def load(self):
        fd = self._locker.acquire_lock(wait=True)
        if not fd:
            return self

        try:
            if not self.config_file.exists():
                self._save_unlocked()
                return self

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
            self._save_unlocked()
            return self

        finally:
            self._locker.release_lock(fd)

    def reload_qtile(self):
        subprocess.run(["qtile", "cmd-obj", "-o", "cmd", "-f", "reload_config"])


ThemeCallback: TypeAlias = Callable[["ThemeAware", str | None], None]


class ThemeAware:
    def __init__(
        self,
        *,
        theme: Theme | None = None,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
    ):
        self.theme: Theme = theme or Theme(config_file=config_file).load()
        self._theme_callbacks: list[ThemeCallback] = []

    # ───────── theme control ─────────

    def set_theme(
        self,
        theme: Theme,
        *,
        event: str = "theme_changed",
        skip_notify: bool = False,
    ) -> None:
        if self.theme is theme:
            return
        self.theme = theme
        if not skip_notify:
            self.notify_theme(event)

    # ───────── observer API ─────────

    def subscribe(self, fn: ThemeCallback) -> None:
        if fn not in self._theme_callbacks:
            self._theme_callbacks.append(fn)

    def unsubscribe(self, fn: ThemeCallback) -> None:
        if fn in self._theme_callbacks:
            self._theme_callbacks.remove(fn)

    def notify_theme(self, event: str | None = None) -> None:
        for cb in list(self._theme_callbacks):
            try:
                cb(self, event)
            except Exception as e:
                logger.error(f"Theme callback failed: {e}")
