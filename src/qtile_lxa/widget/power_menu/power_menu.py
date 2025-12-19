from typing import Literal, Any
from pathlib import Path
from libqtile.lazy import lazy
from qtile_extras.popup.toolkit import PopupRelativeLayout, PopupImage, PopupText
from qtile_lxa import __DEFAULTS__, __ASSETS_DIR__
from .typing import PowerMenuConfig
from ..theme.config import Theme, ThemeAware
from ..theme.utils.colors import rgba


class PowerMenu(ThemeAware):
    menu_instance = None

    def __init__(
        self,
        qtile,
        theme_config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        config: PowerMenuConfig = PowerMenuConfig(),
    ):
        ThemeAware.__init__(self, theme=theme, config_file=theme_config_file)
        self.qtile = qtile
        self.config = config
        self.controls = []
        self.layout = None
        self.active_color = rgba(self.theme.color.scheme.palette.active, 0.4)
        self.inactive_color = rgba(self.theme.color.scheme.palette.inactive, 0.4)
        self.create_controls()

    def create_controls(self):

        menu_items = [
            (
                "lock.png",
                "Lock",
                lazy.spawn(f"betterlockscreen -l {self.config.screenlock_effect}"),
            ),
            ("logout.png", "Logout", lazy.shutdown()),
            (
                "sleep.png",
                self.config.sleep_mode.name.capitalize(),
                lazy.spawn(self.config.sleep_mode.value),
            ),
            ("restart.png", "Restart", lazy.spawn("systemctl reboot")),
            ("shutdown.png", "Shutdown", lazy.spawn("systemctl poweroff")),
        ]

        for i, (icon, label, action) in enumerate(menu_items):
            pos_x = 0.05 + i * 0.2
            self.controls.append(
                PopupImage(
                    filename=str(__ASSETS_DIR__ / f"icons/{icon}"),
                    pos_x=pos_x,
                    pos_y=0.2,
                    width=0.1,
                    height=0.5,
                    highlight_radius=35,
                    highlight_method="border",
                    highlight=self.active_color,
                    mouse_callbacks={"Button1": action},
                )
            )
            self.controls.append(
                PopupText(
                    text=label,
                    pos_x=pos_x,
                    pos_y=0.75,
                    width=0.1,
                    height=0.2,
                    h_align="center",
                )
            )

        # "Close" button
        self.controls.append(
            PopupImage(
                filename=str(__ASSETS_DIR__ / "icons/close.png"),
                pos_x=0.95,
                pos_y=0.01,
                width=0.02,
                height=0.09,
                highlight_radius=10,
                highlight="D91656",
                mouse_callbacks={"Button1": self.hide},
            )
        )

    def show(self):
        if PowerMenu.menu_instance:
            return

        self.layout = PopupRelativeLayout(
            self.qtile,
            width=1000,
            height=250,
            controls=self.controls,
            background=self.inactive_color,
            border=self.active_color,
            border_width=2,
            initial_focus=None,
            close_on_click=True,
            hide_on_mouse_leave=True,
        )
        self.layout.show(centered=True)
        PowerMenu.menu_instance = self

    def hide(self):
        """Hide the PowerMenu."""
        if self.layout:
            self.layout.hide()
            self.layout = None
            PowerMenu.menu_instance = None


def show_power_menu(qtile):
    if not PowerMenu.menu_instance:
        menu = PowerMenu(qtile)
        menu.show()
    else:
        PowerMenu.menu_instance.hide()
        menu = PowerMenu(qtile)
        menu.show()
