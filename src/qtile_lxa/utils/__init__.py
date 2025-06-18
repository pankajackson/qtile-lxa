from threading import Timer
from libqtile import qtile


def toggle_and_auto_close_widgetbox(widget_name, close_after=5):
    widget = qtile.widgets_map[widget_name]
    widget.toggle()
    if widget.box_is_open:
        Timer(
            close_after, lambda: widget.toggle() if widget.box_is_open else None
        ).start()
