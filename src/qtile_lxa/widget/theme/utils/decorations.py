from typing import Literal
from libqtile.log_utils import logger
from ..config.decorations import decorations


def get_decoration(
    theme: Literal["arrows", "rounded", "slash", "zig_zag"] = "arrows",
):
    try:
        return decorations[theme]
    except Exception as e:
        logger.error(f"failed to get decoration for theme {theme}!")
        return decorations["arrows"]
