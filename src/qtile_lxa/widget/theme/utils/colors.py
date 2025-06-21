from ..config.colors import color_schemes
from typing import Any, Literal
from libqtile.log_utils import logger


def invert_hex_color_of(hex_color: str):
    hex_color = hex_color.lstrip("#")  # Remove '#' if present
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # Convert hex to RGB
    inverted_rgb = tuple(255 - value for value in rgb)  # Invert RGB
    inverted_hex = "#%02x%02x%02x" % inverted_rgb  # Convert RGB to hex
    return inverted_hex


def rgba(hex_color: Any, alpha: float):
    hex_color = hex_color.lstrip("#")
    return f"#{hex_color}{int(alpha * 255):02x}"


def get_color_scheme(
    theme: Literal["pywal", "dark_pl", "bright_pl", "black_n_white"] = "dark_pl",
):
    cs = None
    try:
        if theme in color_schemes and color_schemes[theme]:
            cs = color_schemes[theme]
        else:
            logger.error(f"Unable to find color_schemes for theme {theme}!")
    except Exception as e:
        logger.error(f"failed to get color_schemes for theme {theme}!")

    if not cs:
        cs = color_schemes["dark_pl"]

    cs["active"] = cs["color_sequence"][-1]
    cs["highlight"] = cs["color_sequence"][0]
    if len(cs["color_sequence"]) > 1:
        cs["inactive"] = cs["color_sequence"][1]
    else:
        cs["inactive"] = invert_hex_color_of(cs["color_sequence"][0])
    return cs
