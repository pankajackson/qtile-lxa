from pathlib import Path
from qtile_extras import widget
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__
from ..config import Theme, ThemeAware


class ColorRainbowModeChanger(ThemeAware, widget.TextBox):
    def __init__(
        self,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        **config,
    ):
        ThemeAware.__init__(self, theme=theme, config_file=config_file)
        widget.TextBox.__init__(self, **config)
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
        return self.theme.color.rainbow

    def save_rainbow_mode(self, rainbow_mode: bool):
        config = self.theme
        config.color.rainbow = rainbow_mode
        config.save()

    def update_text(self):
        current_status = "1" if self.current_rainbow_mode else "0"
        self.text = self.text_template.format(current_status)
        self.draw()

    def toggle_rainbow_mode(self):
        self.current_rainbow_mode = not self.current_rainbow_mode
        self.save_rainbow_mode(self.current_rainbow_mode)
        self.notify_theme("bar_rainbow_mode")
        self.update_text()
        send_notification(
            title=f"Rainbow Mode: {self.current_rainbow_mode}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )
