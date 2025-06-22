import threading
from typing import Any
from qtile_extras import widget
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__

theme_config = ThemeConfig()


class ColorRainbowModeChanger(widget.TextBox):
    def __init__(self, **config):
        super().__init__(**config)
        self.text_template = " : {}"
        self.current_rainbow_mode = self.get_current_rainbow_mode()
        self.conf_reload_timer = None
        self.decorations = [
            widget.decorations.RectDecoration(
                colour="#004040",
                radius=10,
                filled=True,
                padding_y=4,
                group=True,
                extrawidth=5,
            )
        ]
        self.add_callbacks(
            {
                "Button1": self.toggle_rainbow_mode,
            }
        )
        self.update_text()

    def get_current_rainbow_mode(self):
        return theme_config.load_config().get("color", {}).get("rainbow", True)

    def save_rainbow_mode(self, rainbow_mode):
        config = theme_config.load_config()
        config["color"]["rainbow"] = rainbow_mode
        theme_config.save_config(config)

    def update_text(self):
        current_status = "1" if self.current_rainbow_mode else "0"
        self.text = self.text_template.format(current_status)
        self.draw()

    def toggle_rainbow_mode(self):
        self.current_rainbow_mode = not self.current_rainbow_mode
        self.save_rainbow_mode(self.current_rainbow_mode)
        self.update_text()
        send_notification(
            title=f"Rainbow Mode: {self.current_rainbow_mode}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

        if self.conf_reload_timer and self.conf_reload_timer.is_alive():
            self.conf_reload_timer.cancel()
        self.conf_reload_timer = threading.Timer(1, theme_config.reload_qtile)
        self.conf_reload_timer.start()
