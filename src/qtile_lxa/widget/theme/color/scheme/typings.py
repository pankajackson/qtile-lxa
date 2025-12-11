from dataclasses import dataclass
from pathlib import Path
from libqtile.log_utils import logger
import json
from qtile_lxa import __DEFAULTS__
from ..utils import invert_hex_color_of


@dataclass
class ColorScheme:
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
