import threading
from typing import Any
from qtile_extras import widget
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__

theme_config = ThemeConfig()


class BarTransparencyModeChanger(widget.TextBox):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.text_template = "󱡓 : {}"
        self.current_bar_mode = self.get_current_bar_mode()
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
                "Button1": self.toggle_bar_mode,
            }
        )
        self.update_text()

    def get_current_bar_mode(self):
        return theme_config.load_config().get("bar", {}).get("transparent", False)

    def save_bar_mode(self, bar_mode):
        config = theme_config.load_config()
        config["bar"]["transparent"] = bar_mode
        theme_config.save_config(config=config)

    def update_text(self):
        current_status = "1" if self.current_bar_mode else "0"
        self.text = self.text_template.format(current_status)
        self.draw()

    def toggle_bar_mode(self):
        self.current_bar_mode = not self.current_bar_mode
        self.save_bar_mode(self.current_bar_mode)
        self.update_text()
        send_notification(
            title=f"Bar Transparency: {self.current_bar_mode}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

        if self.conf_reload_timer and self.conf_reload_timer.is_alive():
            self.conf_reload_timer.cancel()
        self.conf_reload_timer = threading.Timer(1, theme_config.reload_qtile)
        self.conf_reload_timer.start()
