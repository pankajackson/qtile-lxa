from dataclasses import dataclass
from qtile_extras.widget.decorations import PowerLineDecoration


@dataclass
class DecorationConfig:
    left_decoration: list[PowerLineDecoration]
    right_decoration: list[PowerLineDecoration]
