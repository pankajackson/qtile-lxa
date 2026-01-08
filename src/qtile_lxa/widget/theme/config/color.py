from dataclasses import dataclass
from pathlib import Path
from libqtile.log_utils import logger
import json
from enum import Enum
from qtile_lxa import __DEFAULTS__
from ..utils.colors import invert_hex_color_of


@dataclass
class ColorSchemeConfig:
    color_sequence: list[str]
    background: str | None = None
    foreground: str | None = None
    active: str | None = None
    inactive: str | None = None
    highlight: str | None = None

    def __post_init__(self):
        if not self.background:
            self.background = self.color_sequence[0]
        if not self.foreground:
            self.foreground = self.color_sequence[-1]
        if not self.active:
            self.active = self.color_sequence[-1]
        if not self.highlight:
            self.highlight = self.color_sequence[0]
        if not self.inactive:
            if len(self.color_sequence) > 1:
                self.inactive = self.color_sequence[1]
            else:
                self.inactive = invert_hex_color_of(self.color_sequence[0])


def get_pywal_color_scheme(
    pywal_colors_json_path: Path = __DEFAULTS__.theme_manager.pywall.pywal_color_scheme_path,
):
    default_color_scheme = ColorSchemeConfig(
        color_sequence=[
            "#080D13",
            "#314E63",
            "#464F74",
            "#3C6F86",
            "#50678E",
            "#A264D7",
            "#5495AA",
            "#abd5de",
            "#77959b",
            "#314E63",
            "#464F74",
            "#3C6F86",
            "#50678E",
            "#A264D7",
            "#5495AA",
            "#abd5de",
        ],
        background="#080D13",
        foreground="#abd5de",
    )
    if not pywal_colors_json_path.exists():
        logger.warning("Pywal colors not ready yet, using default scheme")
        return default_color_scheme
    else:
        try:
            with open(pywal_colors_json_path, "r") as j:
                raw_col = json.loads(j.read())
            color_scheme = ColorSchemeConfig(
                color_sequence=list(dict(raw_col["colors"]).values()),
                background=raw_col.get("special", {}).get("background"),
                foreground=raw_col.get("special", {}).get("foreground"),
            )
            return color_scheme
        except Exception as e:
            logger.error(f"failed to parse pywal colors file {pywal_colors_json_path}!")
            return default_color_scheme


class ColorScheme(Enum):
    DARK = "DARK"
    LIGHT = "LIGHT"
    BLACK_WHITE = "BLACK_WHITE"
    PYWAL = "PYWAL"

    @property
    def palette(self) -> ColorSchemeConfig:
        if self is ColorScheme.PYWAL:
            return get_pywal_color_scheme()
        try:
            return _STATIC_SCHEMES[self]
        except KeyError:
            logger.error(f"Unknown ColorScheme: {self}, falling back to DARK")
            return _STATIC_SCHEMES[ColorScheme.DARK]


_STATIC_SCHEMES = {
    ColorScheme.DARK: ColorSchemeConfig(
        color_sequence=[
            "#282a36",  # Black
            # "#ff5555",  # Red
            "#50fa7b",  # Green
            "#f1fa8c",  # Yellow
            "#bd93f9",  # Blue
            "#ff79c6",  # Magenta
            "#8be9fd",  # Cyan
            "#f8f8f2",  # White
        ],
        background="#282a36",
        foreground="#ffffff",
    ),
    ColorScheme.LIGHT: ColorSchemeConfig(
        color_sequence=[
            "#6272a4",  # Bright Black
            # "#ff6e6e",  # Bright Red
            "#69ff94",  # Bright Green
            "#ffffa5",  # Bright Yellow
            "#d6acff",  # Bright Blue
            "#ff92df",  # Bright Magenta
            "#a4ffff",  # Bright Cyan
            "#ffffff",  # Bright White
        ],
        background="#282a36",
        foreground="#f8f8f2",
    ),
    ColorScheme.BLACK_WHITE: ColorSchemeConfig(
        color_sequence=[
            "#FFFFFF",  # White
            "#000000",  # Black
        ],
        background="#FFFFFF",
        foreground="#000000",
    ),
}
