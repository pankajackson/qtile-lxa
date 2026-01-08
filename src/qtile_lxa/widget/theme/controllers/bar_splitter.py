from pathlib import Path
from typing import Any
from qtile_extras import widget
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__
from ..config import Theme, ThemeAware


class BarSplitModeChanger(ThemeAware, widget.TextBox):
    def __init__(
        self,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        **kwargs: Any,
    ):
        ThemeAware.__init__(self, theme=theme, config_file=config_file)
        widget.TextBox.__init__(self, **kwargs)
        self.text_template = "󰤼 : {}"
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
        return self.theme.bar.split

    def save_bar_mode(self, bar_mode: bool):
        config = self.theme
        config.bar.split = bar_mode
        config.save()

    def update_text(self):
        current_status = "1" if self.current_bar_mode else "0"
        self.text = self.text_template.format(current_status)
        self.draw()

    def toggle_bar_mode(self):
        self.current_bar_mode = not self.current_bar_mode
        self.save_bar_mode(self.current_bar_mode)
        self.notify_theme("bar_split_mode")
        self.update_text()
        send_notification(
            title=f"Bar Split: {self.current_bar_mode}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )
