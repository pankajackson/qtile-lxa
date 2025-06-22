import threading
from qtile_extras import widget
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.widget.theme.config import color_schemes
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__

theme_config = ThemeConfig()


class ColorSchemeChanger(widget.TextBox):
    def __init__(self, display_name=False, **config):
        super().__init__(**config)
        self.color_schemes_list = list(color_schemes.keys())
        self.text_template = f"󰸌: {{current_scheme}}"  # Icon and scheme name
        self.current_scheme = self.get_current_scheme()
        self.display_name = display_name
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
                "Button1": self.next_scheme,
                "Button3": self.prev_scheme,
            }
        )
        self.update_text()

    def get_current_scheme(self):
        return (
            theme_config.load_config()
            .get("color", {})
            .get("scheme", self.color_schemes_list[0])
        )

    def save_current_scheme(self, scheme_name):
        config = theme_config.load_config()
        config["color"]["scheme"] = scheme_name
        theme_config.save_config(config)

    def update_text(self):
        current_scheme = self.current_scheme
        self.text = (
            self.text_template.format(current_scheme=current_scheme)
            if self.display_name
            else self.text_template.format(
                current_scheme=self.color_schemes_list.index(current_scheme)
            )
        )
        self.draw()

    def next_scheme(self):
        current_index = self.color_schemes_list.index(self.current_scheme)
        self.current_scheme = self.color_schemes_list[
            (current_index + 1) % len(self.color_schemes_list)
        ]
        self.save_current_scheme(self.current_scheme)
        self.update_text()
        send_notification(
            title=f"Color Scheme: {self.current_scheme}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

        if self.conf_reload_timer and self.conf_reload_timer.is_alive():
            self.conf_reload_timer.cancel()
        self.conf_reload_timer = threading.Timer(1, theme_config.reload_qtile)
        self.conf_reload_timer.start()

    def prev_scheme(self):
        current_index = self.color_schemes_list.index(self.current_scheme)
        self.current_scheme = self.color_schemes_list[
            (current_index - 1) % len(self.color_schemes_list)
        ]
        self.save_current_scheme(self.current_scheme)
        self.update_text()
        send_notification(
            title=f"Color Scheme: {self.current_scheme}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

        if self.conf_reload_timer and self.conf_reload_timer.is_alive():
            self.conf_reload_timer.cancel()
        self.conf_reload_timer = threading.Timer(1, theme_config.reload_qtile)
        self.conf_reload_timer.start()
