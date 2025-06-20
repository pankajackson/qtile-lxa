from qtile_extras import widget
from typing import Any
from qtile_lxa.utils import toggle_and_auto_close_widgetbox
from ..pywall import PyWallChanger
from ..vidwall import VidWallController
from ..color import ColorSchemeChanger
from ..bar import DecorationChanger
from ..color import ColorRainbowModeChanger
from ..bar import BarSplitModeChanger
from ..bar import BarTransparencyModeChanger


class ThemeManager(widget.WidgetBox):
    def __init__(
        self,
        name: str = "theme_manager_widget_box",
        pywall: PyWallChanger | None = PyWallChanger(update_screenlock=True),
        vidwall: VidWallController | None = VidWallController(),
        color_scheme: ColorSchemeChanger | None = ColorSchemeChanger(),
        decoration: DecorationChanger | None = DecorationChanger(),
        color_rainbow: ColorRainbowModeChanger | None = ColorRainbowModeChanger(),
        bar_split: BarSplitModeChanger | None = BarSplitModeChanger(),
        bar_transparency: (
            BarTransparencyModeChanger | None
        ) = BarTransparencyModeChanger(),
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
