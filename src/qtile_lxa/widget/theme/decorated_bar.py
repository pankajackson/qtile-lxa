from pathlib import Path
from typing import Any
from libqtile.bar import Bar
from libqtile.widget.base import _Widget
from qtile_extras import widget
from qtile_lxa import __DEFAULTS__
from .config import Theme, ThemeAware
from .utils.colors import rgba, invert_hex_color_of


class DecoratedBar(ThemeAware):
    def __init__(
        self,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        left_widgets: list[_Widget] | None = None,
        right_widgets: list[_Widget] | None = None,
        transparent: bool = True,
        **bar_kwargs,
    ):
        super().__init__(theme=theme, config_file=config_file)
        self.left_widgets = left_widgets or []
        self.right_widgets = right_widgets or []
        self.transparent = transparent
        self.bar: Bar = Bar(
            widgets=[*self.left_widgets, *self.right_widgets],
            background=rgba(
                self.theme.color.scheme.palette.background, 0 if self.transparent else 1
            ),
            **bar_kwargs,
        )

    def apply_theme(self):
        decoration = self.theme.decoration
        color_scheme = self.theme.color.scheme.palette
        colors_rainbow_mode = self.theme.color.rainbow
        bar_split_mode = self.theme.bar.split
        bar_transparent_mode = self.theme.bar.transparent
        setattr(
            self.bar,
            "background",
            rgba(
                self.theme.color.scheme.palette.background,
                0 if self.transparent else 1,
            ),
        )

        def set_properties(wid: _Widget, attributes: dict[str, Any]):
            for attr, value in attributes.items():
                if attr == "background":
                    if bar_transparent_mode:
                        value = rgba(value, 0)
                    elif bar_split_mode and isinstance(
                        wid, (widget.WindowName, widget.TaskList)
                    ):
                        value = rgba(value, 0)
                setattr(wid, attr, value)
            if hasattr(wid, "draw"):
                wid.draw()

        for i, wid in enumerate(self.left_widgets):
            if colors_rainbow_mode:
                background_color = color_scheme.color_sequence[
                    -i % len(color_scheme.color_sequence)
                ]
                foreground_color = invert_hex_color_of(background_color)
            else:
                background_color = color_scheme.highlight
                foreground_color = (
                    color_scheme.active
                    if color_scheme.active != background_color
                    else (
                        invert_hex_color_of(background_color)
                        if background_color
                        else None
                    )
                )
            widget_attr: dict[str, Any] = {
                "background": background_color,
                "foreground": foreground_color,
                "decorations": decoration.instance.left_decoration,
            }
            set_properties(wid=wid, attributes=widget_attr)

        for i, wid in enumerate(self.right_widgets):
            if colors_rainbow_mode:
                background_color = color_scheme.color_sequence[
                    i % len(color_scheme.color_sequence)
                ]
                foreground_color = invert_hex_color_of(background_color)
            else:
                background_color = color_scheme.inactive
                foreground_color = (
                    color_scheme.active
                    if color_scheme.active != background_color
                    else (
                        invert_hex_color_of(background_color)
                        if background_color
                        else None
                    )
                )
            widget_attr: dict[str, Any] = {
                "background": background_color,
                "foreground": foreground_color,
            }
            if wid != self.right_widgets[-1]:
                widget_attr["decorations"] = decoration.instance.right_decoration

            set_properties(wid=wid, attributes=widget_attr)

        if self.bar.screen:
            self.bar.draw()
