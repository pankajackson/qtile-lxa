from importlib.metadata import version as pkg_version, PackageNotFoundError
from pathlib import Path
from dataclasses import dataclass, field
from libqtile.log_utils import logger


__BASE_DIR__ = Path(__file__).resolve().parent
logger.error("qtile-lxa basedir: {}".format(__BASE_DIR__))


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


@dataclass(frozen=True)
class VidWallDefaults:
    playlist_path: Path = Path.home() / "vidwall_playlists.json"


@dataclass(frozen=True)
class ThemeManagerDefaults:
    pywall: PyWallDefaults = PyWallDefaults()
    vidwall: VidWallDefaults = VidWallDefaults()
    config_path: Path = Path.home() / ".lxa_theme_config.json"


@dataclass(frozen=True)
class __Defaults__:
    theme_manager: ThemeManagerDefaults = ThemeManagerDefaults()


__DEFAULTS__ = __Defaults__()
