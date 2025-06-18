from qtile_extras import widget
from typing import Any
from qtile_lxa.utils import toggle_and_auto_close_widgetbox
from .PyWall import PyWallChanger
from .VidWall import VidWallController
from .ColorScheme import ColorSchemeChanger
from .Decoration import DecorationChanger
from .ColorRainbow import ColorRainbowModeChanger
from .BarSplit import BarSplitModeChanger
from .BarTransparency import BarTransparencyModeChanger


class ThemeManager(widget.WidgetBox):
    def __init__(
        self,
        name: str = "theme_manager_widget_box",
        pywall: bool = True,
        vidwall: bool = True,
        color_scheme: bool = True,
        decoration: bool = True,
        color_rainbow: bool = True,
        bar_split: bool = True,
        bar_transparency: bool = True,
        **kwargs: Any,
    ):
        self.name = name
        self.pywall = pywall
        self.vidwall = vidwall
        self.color_scheme = color_scheme
        self.decoration = decoration
        self.color_rainbow = color_rainbow
        self.bar_split = bar_split
        self.bar_transparency = bar_transparency
        self.controller_list = self.get_enabled_controllers()

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
            controllers.append(PyWallChanger(update_screenlock=True))
        if self.vidwall:
            controllers.append(VidWallController())
        if self.color_scheme:
            controllers.append(ColorSchemeChanger())
        if self.decoration:
            controllers.append(DecorationChanger())
        if self.color_rainbow:
            controllers.append(ColorRainbowModeChanger())
        if self.bar_split:
            controllers.append(BarSplitModeChanger())
        if self.bar_transparency:
            controllers.append(BarTransparencyModeChanger())
        return controllers
