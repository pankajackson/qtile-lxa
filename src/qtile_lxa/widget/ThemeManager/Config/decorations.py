from typing import Literal
from libqtile.log_utils import logger
from qtile_extras.widget.decorations import PowerLineDecoration


decorations = {
    "arrows": {
        "left_decoration": [PowerLineDecoration(path="arrow_left")],
        "right_decoration": [PowerLineDecoration(path="arrow_right")],
    },
    "rounded": {
        "left_decoration": [PowerLineDecoration(path="rounded_left")],
        "right_decoration": [PowerLineDecoration(path="rounded_right")],
    },
    "slash": {
        "left_decoration": [PowerLineDecoration(path="back_slash")],
        "right_decoration": [PowerLineDecoration(path="forward_slash")],
    },
    "zig_zag": {
        "left_decoration": [PowerLineDecoration(path="zig_zag")],
        "right_decoration": [PowerLineDecoration(path="zig_zag")],
    },
}


def get_decoration(
    theme: Literal["arrows", "rounded", "slash", "zig_zag"] = "arrows",
):
    try:
        return decorations[theme]
    except Exception as e:
        logger.error(f"failed to get decoration for theme {theme}!")
        return decorations["arrows"]
