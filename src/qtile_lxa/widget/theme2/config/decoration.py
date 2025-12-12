from dataclasses import dataclass
from qtile_extras.widget.decorations import PowerLineDecoration
from enum import Enum
from copy import deepcopy


@dataclass
class DecorationConfig:
    left_decoration: list[PowerLineDecoration]
    right_decoration: list[PowerLineDecoration]


class Decoration(Enum):
    ARROW = DecorationConfig(
        left_decoration=[PowerLineDecoration(path="arrow_left")],
        right_decoration=[PowerLineDecoration(path="arrow_right")],
    )
    ROUNDED = DecorationConfig(
        left_decoration=[PowerLineDecoration(path="rounded_left")],
        right_decoration=[PowerLineDecoration(path="rounded_right")],
    )
    SLASH = DecorationConfig(
        left_decoration=[PowerLineDecoration(path="back_slash")],
        right_decoration=[PowerLineDecoration(path="forward_slash")],
    )
    ZIGZAG = DecorationConfig(
        left_decoration=[PowerLineDecoration(path="zig_zag")],
        right_decoration=[PowerLineDecoration(path="zig_zag")],
    )

    @property
    def instance(self) -> DecorationConfig:
        return deepcopy(self.value)
