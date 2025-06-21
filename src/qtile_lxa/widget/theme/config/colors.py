from pathlib import Path
from libqtile.log_utils import logger
import json
from qtile_lxa import __DEFAULTS__


def get_pywal_color_scheme(
    pywal_colors=__DEFAULTS__.theme_manager.pywall.pywal_color_scheme_path,
):
    if not Path.exists(pywal_colors):
        logger.error(f"pywal colors file {pywal_colors} not exist!")
        return None
    else:
        try:
            with open(pywal_colors, "r") as j:
                raw_col = json.loads(j.read())
            theme = {
                "color_sequence": list(dict(raw_col["colors"]).values()),
                "background": raw_col["special"]["background"],
                "foreground": raw_col["special"]["foreground"],
            }
            return theme
        except Exception as e:
            logger.error(f"failed to parse pywal colors file {pywal_colors}!")
            return None


color_schemes = {
    "dark_pl": {
        "color_sequence": [
            "#282a36",  # Black
            # "#ff5555",  # Red
            "#50fa7b",  # Green
            "#f1fa8c",  # Yellow
            "#bd93f9",  # Blue
            "#ff79c6",  # Magenta
            "#8be9fd",  # Cyan
            "#f8f8f2",  # White
        ],
        "background": "#282a36",
        "foreground": "#ffffff",
    },
    "bright_pl": {
        "color_sequence": [
            "#6272a4",  # Bright Black
            # "#ff6e6e",  # Bright Red
            "#69ff94",  # Bright Green
            "#ffffa5",  # Bright Yellow
            "#d6acff",  # Bright Blue
            "#ff92df",  # Bright Magenta
            "#a4ffff",  # Bright Cyan
            "#ffffff",  # Bright White
        ],
        "background": "#282a36",
        "foreground": "#f8f8f2",
    },
    "black_n_white": {
        "color_sequence": [
            "#FFFFFF",  # White
            "#000000",  # Black
        ],
        "background": "#FFFFFF",
        "foreground": "#000000",
    },
    "pywal": get_pywal_color_scheme(),
}
