from pathlib import Path
from qtile_extras import widget
from qtile_lxa.utils.notification import send_notification
from qtile_lxa import __DEFAULTS__
from ..config import Theme, ThemeAware, Decoration


class DecorationChanger(ThemeAware, widget.TextBox):
    def __init__(
        self,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        display_name=False,
        **config,
    ):
        ThemeAware.__init__(self, theme=theme, config_file=config_file)
        widget.TextBox.__init__(self, **config)
        self.decorations_list = [item for item in Decoration]
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
        return self.theme.decoration

    def save_current_decoration(self, decoration_name):
        config = self.theme
        config.decoration = decoration_name
        config.save()

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
        self.notify_theme("bar_decoration")
        self.update_text()
        send_notification(
            title=f"Decoration: {self.current_decoration.name}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )

    def prev_decoration(self):
        current_index = self.decorations_list.index(
            self.current_decoration
        )  # Get current index
        self.current_decoration = self.decorations_list[
            (current_index - 1) % len(self.decorations_list)
        ]
        self.save_current_decoration(self.current_decoration)  # Save decoration name
        self.notify_theme("bar_decoration")
        self.update_text()
        send_notification(
            title=f"Decoration:  {self.current_decoration.name}",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )
