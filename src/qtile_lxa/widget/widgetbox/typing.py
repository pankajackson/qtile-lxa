from dataclasses import dataclass
from libqtile.widget.base import _Widget


@dataclass
class WidgetBoxConfig:
    widgets: list[_Widget]
    name: str | None = None
    close_button_location: str = "left"
    text_closed: str = "  "
    text_open: str = "  "
    timeout: int = 5
