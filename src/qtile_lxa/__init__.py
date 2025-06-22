from importlib.metadata import version as pkg_version, PackageNotFoundError
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal
from libqtile.log_utils import logger


__BASE_DIR__ = Path(__file__).resolve().parent
__ASSETS_DIR__ = __BASE_DIR__ / "assets"


try:
    __VERSION__ = pkg_version("qtile-lxa")
except PackageNotFoundError:
    __VERSION__ = "0.0.0"


@dataclass(frozen=True)
class PyWallDefaults:
    pywal_color_scheme_path: Path = Path.home() / ".cache/wal/colors.json"
    wallpaper_dir: Path = Path.home() / "Pictures/lxa_desktop_backgrounds"
    wallpaper_repos: list[str] = field(
        default_factory=lambda: ["https://github.com/pankajackson/wallpapers.git"]
    )
    screenlock_effect: str = "blur"


@dataclass(frozen=True)
class VidWallDefaults:
    playlist_path: Path = Path.home() / "vidwall_playlists.json"


@dataclass(frozen=True)
class ThemeManagerDefaults:
    pywall: PyWallDefaults = PyWallDefaults()
    vidwall: VidWallDefaults = VidWallDefaults()
    config_path: Path = Path.home() / ".lxa_theme_config.json"


@dataclass(frozen=True)
class PowerMenu:
    sleep_mode: Literal["sleep", "hibernate", "hybrid-sleep"] = "sleep"


@dataclass(frozen=True)
class Media:
    max_volume: int = 150


@dataclass(frozen=True)
class Screen:
    profile: str = "my_desktop_screen"


@dataclass(frozen=True)
class Docker:
    network: str = "lxa-docker-bridge"
    subnet: str = "10.11.0.0/24"


@dataclass(frozen=True)
class Podman:
    network: str = "lxa-podman-bridge"
    subnet: str = "10.12.0.0/24"


@dataclass(frozen=True)
class __Defaults__:
    theme_manager: ThemeManagerDefaults = ThemeManagerDefaults()
    power_menu: PowerMenu = PowerMenu()
    media = Media()
    docker = Docker()
    podman = Podman()
    screen = Screen()


__DEFAULTS__ = __Defaults__()
