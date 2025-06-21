import threading
from qtile_extras import widget
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.widget.theme.config import decorations
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__

theme_config = ThemeConfig()


class DecorationChanger(widget.TextBox):
    def __init__(self, display_name=False, **config):
        super().__init__(**config)
        self.decorations_list = list(decorations.keys())
        self.text_template = f"󰟾: {{current_decor}}"  # Icon and index
        self.current_decoration = self.get_current_decoration()
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
                "Button1": self.next_decoration,
                "Button3": self.prev_decoration,
            }
        )
        self.update_text()

    def get_current_decoration(self):
        return theme_config.load_config().get(
            "decoration", list(decorations.keys())[0]
        )

    def save_current_decoration(self, decoration_name):
        config = theme_config.load_config()
        config["decoration"] = decoration_name
        theme_config.save_config(config)

    def update_text(self):
        # Update the widget text to display the current decoration
        current_decoration = self.current_decoration
        self.text = (
            self.text_template.format(current_decor=current_decoration)
            if self.display_name
            else self.text_template.format(
                current_decor=self.decorations_list.index(current_decoration)
            )
        )
        self.draw()

    def next_decoration(self):
        current_index = self.decorations_list.index(
            self.current_decoration
        )  # Get current index
        self.current_decoration = self.decorations_list[
            (current_index + 1) % len(self.decorations_list)
        ]
        self.save_current_decoration(self.current_decoration)  # Save decoration name
        self.update_text()
        send_notification(
            title=f"Decoration: {self.current_decoration}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

        if self.conf_reload_timer and self.conf_reload_timer.is_alive():
            self.conf_reload_timer.cancel()
        self.conf_reload_timer = threading.Timer(1, theme_config.reload_qtile)
        self.conf_reload_timer.start()

    def prev_decoration(self):
        current_index = self.decorations_list.index(
            self.current_decoration
        )  # Get current index
        self.current_decoration = self.decorations_list[
            (current_index - 1) % len(self.decorations_list)
        ]
        self.save_current_decoration(self.current_decoration)  # Save decoration name
        self.update_text()
        send_notification(
            title=f"Decoration:  {self.current_decoration}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

        if self.conf_reload_timer and self.conf_reload_timer.is_alive():
            self.conf_reload_timer.cancel()
        self.conf_reload_timer = threading.Timer(1, theme_config.reload_qtile)
        self.conf_reload_timer.start()
