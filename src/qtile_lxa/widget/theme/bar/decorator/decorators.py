from dataclasses import dataclass
from qtile_extras.widget.decorations import PowerLineDecoration
from .typings import Decoration
from enum import Enum


class Decorations(str, Enum):
    ARROW = "arrow"
    ROUNDED = "rounded"
    SLASH = "slash"
    ZIGZAG = "zigzag"

    @property
    def obj(self) -> Decoration:
        """Return the actual Decoration object."""
        return _DECORATION_MAP[self]


_DECORATION_MAP = {
    Decorations.ARROW: Decoration(
        left_decoration=[PowerLineDecoration(path="arrow_left")],
        right_decoration=[PowerLineDecoration(path="arrow_right")],
    ),
    Decorations.ROUNDED: Decoration(
        left_decoration=[PowerLineDecoration(path="rounded_left")],
        right_decoration=[PowerLineDecoration(path="rounded_right")],
    ),
    Decorations.SLASH: Decoration(
        left_decoration=[PowerLineDecoration(path="back_slash")],
        right_decoration=[PowerLineDecoration(path="forward_slash")],
    ),
    Decorations.ZIGZAG: Decoration(
        left_decoration=[PowerLineDecoration(path="zig_zag")],
        right_decoration=[PowerLineDecoration(path="zig_zag")],
    ),
}
