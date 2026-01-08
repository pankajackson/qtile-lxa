from pathlib import Path
from typing import Any
from libqtile import qtile
from qtile_extras import widget
from qtile_lxa.utils import toggle_and_auto_close_widgetbox
from .controllers.bar_decoration import DecorationChanger
from .controllers.bar_splitter import BarSplitModeChanger
from .controllers.bar_transparency import BarTransparencyModeChanger
from .controllers.color_scheme import ColorSchemeChanger
from .controllers.color_rainbow import ColorRainbowModeChanger
from .controllers.pywall import PyWallChanger
from .controllers.vidwall import VidWallController
from .config import Theme, ThemeAware
from qtile_lxa import __DEFAULTS__


_UNSET = object()


class ThemeManager(widget.WidgetBox, ThemeAware):
    def __init__(
        self,
        name: str = "theme_manager_widget_box",
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        pywall: PyWallChanger | None | object = _UNSET,
        vidwall: VidWallController | None | object = _UNSET,
        color_scheme: ColorSchemeChanger | None | object = _UNSET,
        decoration: DecorationChanger | None | object = _UNSET,
        color_rainbow: ColorRainbowModeChanger | None | object = _UNSET,
        bar_split: BarSplitModeChanger | None | object = _UNSET,
        bar_transparency: BarTransparencyModeChanger | None | object = _UNSET,
        sync_layout: bool = True,
        **kwargs: Any,
    ):
        ThemeAware.__init__(self, theme=theme, config_file=config_file)
        widget.TextBox.__init__(self, **kwargs)
        self.name = name
        self.sync_layout = sync_layout

        self.pywall = PyWallChanger(theme=self.theme) if pywall is _UNSET else pywall

        self.vidwall = (
            VidWallController(theme=self.theme) if vidwall is _UNSET else vidwall
        )

        self.color_scheme = (
            ColorSchemeChanger(theme=self.theme)
            if color_scheme is _UNSET
            else color_scheme
        )

        self.decoration = (
            DecorationChanger(theme=self.theme) if decoration is _UNSET else decoration
        )

        self.color_rainbow = (
            ColorRainbowModeChanger(theme=self.theme)
            if color_rainbow is _UNSET
            else color_rainbow
        )

        self.bar_split = (
            BarSplitModeChanger(theme=self.theme) if bar_split is _UNSET else bar_split
        )

        self.bar_transparency = (
            BarTransparencyModeChanger(theme=self.theme)
            if bar_transparency is _UNSET
            else bar_transparency
        )

        self.controller_list = self.get_enabled_controllers()

        if self.sync_layout:
            if isinstance(self.color_scheme, ColorSchemeChanger):
                self.color_scheme.subscribe(self.update_layout_colors)

            if isinstance(self.pywall, PyWallChanger):
                self.pywall.subscribe(self.update_layout_colors)

            qtile.call_soon(self.update_layout_colors)

        super().__init__(
            name=name,
            widgets=self.controller_list,
            close_button_location="left",
            text_closed=" 󰸌 ",
            text_open="󰸌  ",
            mouse_callbacks={
                "Button1": lambda: toggle_and_auto_close_widgetbox(
                    name, close_after=120
                )
            },
            **kwargs,
        )

    def get_enabled_controllers(self):
        controllers = []
        if self.pywall:
            controllers.append(self.pywall)
        if self.vidwall:
            controllers.append(self.vidwall)
        if self.color_scheme:
            controllers.append(self.color_scheme)
        if self.decoration:
            controllers.append(self.decoration)
        if self.color_rainbow:
            controllers.append(self.color_rainbow)
        if self.bar_split:
            controllers.append(self.bar_split)
        if self.bar_transparency:
            controllers.append(self.bar_transparency)
        return controllers

    def update_layout_colors(self, *_):
        colors = self.theme.color.scheme.palette

        for group in qtile.groups:
            layout = group.layout
            if not layout:
                continue

            for attr, value in {
                "border_focus": colors.active,
                "border_normal": colors.inactive,
                "border_focus_stack": colors.active,
                "border_normal_stack": colors.inactive,
            }.items():
                if hasattr(layout, attr):
                    setattr(layout, attr, value)

            group.layout_all()

        # Floating layout (important)
        for screen in qtile.screens:
            flt = screen.group.floating_layout
            if flt:
                flt.border_focus = colors.active
                flt.border_normal = colors.inactive
