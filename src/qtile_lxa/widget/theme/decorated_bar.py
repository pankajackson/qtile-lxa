from pathlib import Path
from typing import Any
from libqtile.bar import Bar
from libqtile.widget.base import _Widget
from qtile_extras import widget
from qtile_lxa import __DEFAULTS__
from .config import Theme, ThemeAware
from .utils.colors import rgba, invert_hex_color_of
from .manager import ThemeManager
from .controllers import (
    BarTransparencyModeChanger,
    ColorSchemeChanger,
    DecorationChanger,
    BarSplitModeChanger,
    ColorRainbowModeChanger,
)
from qtile_extras.widget.decorations import PowerLineDecoration


class DecoratedBar:
    def __init__(
        self,
        manager: ThemeManager,
        left_widgets: list[_Widget] | None = None,
        right_widgets: list[_Widget] | None = None,
        size: int = 30,
        **bar_kwargs,
    ):
        self.manager = manager
        self.theme = self.manager.theme
        self.left_widgets = left_widgets or []
        self.right_widgets = right_widgets or []
        self.bar: Bar = Bar(
            widgets=[*self.left_widgets, *self.right_widgets],
            background=rgba(
                self.theme.color.scheme.palette.background,
                0 if self.theme.bar.transparent else 1,
            ),
            size=size,
            **bar_kwargs,
        )
        if isinstance(self.manager.bar_transparency, BarTransparencyModeChanger):
            self.manager.bar_transparency.subscribe(self.apply_theme)

        if isinstance(self.manager.bar_split, BarSplitModeChanger):
            self.manager.bar_split.subscribe(self.apply_theme)

        if isinstance(self.manager.color_scheme, ColorSchemeChanger):
            self.manager.color_scheme.subscribe(self.apply_theme)

        if isinstance(self.manager.color_rainbow, ColorRainbowModeChanger):
            self.manager.color_rainbow.subscribe(self.apply_theme)

        if isinstance(self.manager.decoration, DecorationChanger):
            self.manager.decoration.subscribe(self.apply_theme)

    def apply_theme(self, *_args):
        decoration = self.theme.decoration
        color_scheme = self.theme.color.scheme.palette
        colors_rainbow_mode = self.theme.color.rainbow
        bar_split_mode = self.theme.bar.split
        bar_transparent_mode = self.theme.bar.transparent

        setattr(
            self.bar,
            "background",
            rgba(color_scheme.background, 0 if bar_transparent_mode else 1),
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

        for i, wid in enumerate(self.left_widgets):
            if colors_rainbow_mode:
                bg = color_scheme.color_sequence[-i % len(color_scheme.color_sequence)]
                fg = invert_hex_color_of(bg)
            else:
                bg = color_scheme.highlight
                fg = (
                    color_scheme.active
                    if color_scheme.active != bg
                    else invert_hex_color_of(bg) if bg else None
                )

            attrs: dict[str, Any] = {
                "background": bg,
                "foreground": fg,
                # "decorations": decoration.instance.left_decoration,
            }

            set_properties(wid, attrs)

        for i, wid in enumerate(self.right_widgets):
            if colors_rainbow_mode:
                bg = color_scheme.color_sequence[i % len(color_scheme.color_sequence)]
                fg = invert_hex_color_of(bg)
            else:
                bg = color_scheme.inactive
                fg = (
                    color_scheme.active
                    if color_scheme.active != bg
                    else invert_hex_color_of(bg) if bg else None
                )

            attrs: dict[str, Any] = {
                "background": bg,
                "foreground": fg,
            }

            # if wid is not self.right_widgets[-1]:
            #     attrs["decorations"] = decoration.instance.right_decoration

            set_properties(wid, attrs)

        if self.bar.screen:
            self.bar.draw()
            self.bar.screen.group.layout_all()
