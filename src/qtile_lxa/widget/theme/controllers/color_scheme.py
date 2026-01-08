from pathlib import Path
from qtile_extras import widget
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__
from ..config import Theme, ThemeAware, ColorScheme


class ColorSchemeChanger(ThemeAware, widget.TextBox):
    def __init__(
        self,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        display_name=False,
        **kwargs,
    ):
        ThemeAware.__init__(self, theme=theme, config_file=config_file)
        widget.TextBox.__init__(self, **kwargs)
        self.color_schemes_list = [item for item in ColorScheme]
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
        return self.theme.color.scheme

    def save_current_scheme(self, scheme_name: ColorScheme):
        config = self.theme
        config.color.scheme = scheme_name
        config.save()

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
        self.notify_theme("cs_change")
        self.update_text()
        send_notification(
            title=f"Color Scheme: {self.current_scheme.name}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

    def prev_scheme(self):
        current_index = self.color_schemes_list.index(self.current_scheme)
        self.current_scheme = self.color_schemes_list[
            (current_index - 1) % len(self.color_schemes_list)
        ]
        self.save_current_scheme(self.current_scheme)
        self.notify_theme("cs_change")
        self.update_text()
        send_notification(
            title=f"Color Scheme: {self.current_scheme.name}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )
