from typing import Any
from libqtile import bar
from libqtile.log_utils import logger
from qtile_extras import widget
from qtile_lxa.widget.theme.utils.colors import rgba, invert_hex_color_of
from qtile_lxa.widget.theme.utils.config import get_active_config


class DecoratedBar:
    def __init__(
        self,
        left_widgets: list = [],
        right_widgets: list = [],
        height: int = 30,
        opacity: float = 0.92,
        transparent: bool = True,
    ):
        self.left_widget = left_widgets
        self.right_widget = right_widgets
        self.height = height
        self.opacity = opacity
        self.transparent = transparent
        self.decoration = get_active_config("decoration")
        self.color_scheme: Any = get_active_config("color_scheme")
        self.colors_rainbow_mode = get_active_config("rainbow_mode")
        self.bar_split_mode = get_active_config("split_mode")
        self.bar_transparent_mode = get_active_config("transparency_mode")

    def get_bar(self):
        return bar.Bar(
            widgets=self.get_decorated_widgets(),
            size=self.height,
            opacity=self.opacity,
            margin=4,
            background=rgba(
                self.color_scheme["color_sequence"][0], 0 if self.transparent else 1
            ),
        )

    def get_decorated_widgets(self):
        widgets = []

        def set_properties(wid, attributes):
            for attr in attributes.keys():
                if self.bar_transparent_mode:
                    if attr == "background":
                        attributes[attr] = rgba(attributes[attr], 0)
                elif self.bar_split_mode:
                    if attr == "background" and (
                        isinstance(wid, widget.WindowName)
                        or isinstance(wid, widget.TaskList)
                    ):
                        attributes[attr] = rgba(attributes[attr], 0)
                setattr(wid, attr, attributes[attr])

        for i, wid in enumerate(self.left_widget):
            if self.colors_rainbow_mode:
                background_color = self.color_scheme["color_sequence"][
                    -i % len(self.color_scheme["color_sequence"])
                ]
                foreground_color = invert_hex_color_of(background_color)
            else:
                background_color = self.color_scheme["highlight"]
                foreground_color = (
                    self.color_scheme["active"]
                    if self.color_scheme["active"] != background_color
                    else invert_hex_color_of(background_color)
                )
            widget_attr = {
                "background": background_color,
                "foreground": foreground_color,
                "decorations": self.decoration["left_decoration"],
            }
            set_properties(wid=wid, attributes=widget_attr)
        widgets.extend(self.left_widget)

        for i, wid in enumerate(self.right_widget):
            if self.colors_rainbow_mode:
                background_color = self.color_scheme["color_sequence"][
                    i % len(self.color_scheme["color_sequence"])
                ]
                foreground_color = invert_hex_color_of(background_color)
            else:
                background_color = self.color_scheme["inactive"]
                foreground_color = (
                    self.color_scheme["active"]
                    if self.color_scheme["active"] != background_color
                    else invert_hex_color_of(background_color)
                )
            widget_attr = {
                "background": background_color,
                "foreground": foreground_color,
            }
            if wid != self.right_widget[-1]:
                widget_attr["decorations"] = self.decoration["right_decoration"]

            set_properties(wid=wid, attributes=widget_attr)

        widgets = self.left_widget + self.right_widget
        return widgets
