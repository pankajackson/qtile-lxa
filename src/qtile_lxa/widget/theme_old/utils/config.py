# from typing import Literal
# from ..color import ColorSchemes
# from ..bar import Decorations
# from qtile_lxa.widget.theme.config import ThemeConfig


# def get_active_config(
#     config: Literal[
#         "decoration",
#         "color_scheme",
#         "rainbow_mode",
#         "split_mode",
#         "transparency_mode",
#     ],
# ):
#     theme_config = ThemeConfig().load_config()

#     if config == "decoration":
#         decoration = decorations[theme_config.get("decoration", "slash")]
#         return decoration
#     elif config == "color_scheme":
#         color_scheme = color_schemes[
#             theme_config.get("color", {}).get("scheme", "pywal")
#         ]
#         return color_scheme
#     elif config == "rainbow_mode":
#         colors_rainbow_mode = theme_config.get("color", {}).get("rainbow", False)
#         return colors_rainbow_mode
#     elif config == "split_mode":
#         bar_split_mode = theme_config.get("bar", {}).get("split", False)
#         return bar_split_mode
#     elif config == "transparency_mode":
#         bar_transparent_mode = theme_config.get("bar", {}).get("transparent", False)
#         return bar_transparent_mode
#     else:
#         raise ValueError(f"Invalid config: {config}")
