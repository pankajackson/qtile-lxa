from typing import Any
from libqtile import bar
from libqtile.log_utils import logger
from qtile_extras import widget

# from qtile_lxa_test.widget.theme.color.utils import rgba, invert_hex_color_of
from qtile_lxa_test.theme.color.utils import rgba, invert_hex_color_of
from qtile_lxa.widget.theme.config import Theme
from qtile_lxa import __DEFAULTS__


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
        self.active_theme = Theme(
            config_file=__DEFAULTS__.theme_manager.config_path
        ).load()
        self.decoration = self.active_theme.decoration
        self.color_scheme = self.active_theme.color.schemes
        self.colors_rainbow_mode = self.active_theme.color.rainbow
        self.bar_split_mode = self.active_theme.bar.split
        self.bar_transparent_mode = self.active_theme.bar.transparent

    def get_bar(self):
        return bar.Bar(
            widgets=self.get_decorated_widgets(),
            size=self.height,
            opacity=self.opacity,
            margin=4,
            background=rgba(
                self.color_scheme.obj.background, 0 if self.transparent else 1
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
                background_color = self.color_scheme.obj.color_sequence[
                    -i % len(self.color_scheme.obj.color_sequence)
                ]
                foreground_color = invert_hex_color_of(background_color)
            else:
                background_color = self.color_scheme.obj.highlight
                foreground_color = (
                    self.color_scheme.obj.active
                    if self.color_scheme.obj.active != background_color
                    else invert_hex_color_of(background_color)
                )
            widget_attr = {
                "background": background_color,
                "foreground": foreground_color,
                "decorations": self.decoration.obj.left_decoration,
            }
            set_properties(wid=wid, attributes=widget_attr)
        widgets.extend(self.left_widget)

        for i, wid in enumerate(self.right_widget):
            if self.colors_rainbow_mode:
                background_color = self.color_scheme.obj.color_sequence[
                    i % len(self.color_scheme.obj.color_sequence)
                ]
                foreground_color = invert_hex_color_of(background_color)
            else:
                background_color = self.color_scheme.obj.inactive
                foreground_color = (
                    self.color_scheme.obj.active
                    if self.color_scheme.obj.active != background_color
                    else invert_hex_color_of(background_color)
                )
            widget_attr = {
                "background": background_color,
                "foreground": foreground_color,
            }
            if wid != self.right_widget[-1]:
                widget_attr["decorations"] = self.decoration.obj.right_decoration

            set_properties(wid=wid, attributes=widget_attr)

        widgets = self.left_widget + self.right_widget
        return widgets
