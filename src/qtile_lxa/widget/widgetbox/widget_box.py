import uuid
from qtile_extras import widget
from qtile_lxa.utils import toggle_and_auto_close_widgetbox
from .typing import WidgetBoxConfig


class WidgetBox(widget.WidgetBox):
    def __init__(self, config: WidgetBoxConfig):
        name = config.name or f"lxa_widgetbox_{uuid.uuid4().hex[:8]}"

        super().__init__(
            name=name,
            widgets=config.widgets,
            close_button_location=config.close_button_location,
            text_closed=config.text_closed,
            text_open=config.text_open,
            mouse_callbacks={
                "Button1": lambda: toggle_and_auto_close_widgetbox(
                    name,
                    close_after=config.timeout,
                )
            },
        )
