import threading
from typing import Any
from libqtile import qtile
from libqtile.bar import Bar
from libqtile.widget.base import _Widget
from qtile_extras import widget
from qtile_lxa import __DEFAULTS__
from .config import ThemeAware
from .utils.colors import rgba, invert_hex_color_of
from .manager import ThemeManager, DecorationChanger
from libqtile.log_utils import logger


class DecoratedBar:
    def __init__(
        self,
        manager: ThemeManager,
        left_widgets: list[_Widget] | None = None,
        right_widgets: list[_Widget] | None = None,
        size: int = 30,
        **bar_kwargs,
    ):
        self.manager = manager
        self.theme = self.manager.theme
        self._bar_kwargs = bar_kwargs
        self.active_decoration = self.theme.decoration
        self._raw_left_widgets = left_widgets or []
        self._raw_right_widgets = right_widgets or []
        self.left_widgets = self._decorated_widget(
            self._raw_left_widgets, self.active_decoration.value.left_decoration
        )
        self.right_widgets = self._decorated_widget(
            self._raw_right_widgets, self.active_decoration.value.right_decoration
        )

        self.bar: Bar = Bar(
            widgets=[*self.left_widgets, *self.right_widgets],
            background=rgba(self.theme.color.scheme.palette.background, 0),
            size=size,
            **bar_kwargs,
        )
        self._subscribe_controllers()
        qtile.call_later(1, self.apply_theme)

    def _subscribe_controllers(self):
        for ctrl in (
            self.manager.bar_split,
            self.manager.bar_transparency,
            self.manager.color_rainbow,
            self.manager.color_scheme,
            self.manager.pywall,
        ):
            if isinstance(ctrl, ThemeAware):
                ctrl.subscribe(self.apply_theme)
        if isinstance(self.manager.decoration, DecorationChanger):
            self.manager.decoration.subscribe(self.rebuild_bar)

    def _decorated_widget(self, wid_list: list[_Widget], decorations) -> list[_Widget]:
        decorated_wids: list[_Widget] = []
        for wid in wid_list:
            decorated_wid = wid
            setattr(decorated_wid, "decorations", decorations)
            decorated_wids.append(decorated_wid)
        return decorated_wids

    def rebuild_bar(self, *_args):
        def _get_bar_position():
            screen = self.bar.screen
            if not screen:
                return None

            if screen.top is self.bar:
                return "top"
            if screen.bottom is self.bar:
                return "bottom"
            if screen.left is self.bar:
                return "left"
            if screen.right is self.bar:
                return "right"

            return None

        screen = self.bar.screen
        if not screen:
            return

        position = _get_bar_position()
        if position is None:
            logger.warning("Bar is not attached to any screen edge")
            return

        old_bar = self.bar

        self.left_widgets = self._decorated_widget(
            self._raw_left_widgets,
            self.theme.decoration.value.left_decoration,
        )
        self.right_widgets = self._decorated_widget(
            self._raw_right_widgets,
            self.theme.decoration.value.right_decoration,
        )

        new_bar = Bar(
            widgets=[*self.left_widgets, *self.right_widgets],
            size=old_bar.size,
            background=rgba(self.theme.color.scheme.palette.background, 0),
            **self._bar_kwargs,
        )

        # Replace bar
        setattr(screen, position, new_bar)
        self.bar = new_bar

        # Finalize old bar AFTER replacement
        old_bar.finalize()

        # Ask Qtile to reconfigure screens properly
        qtile.call_soon(qtile.cmd_reconfigure_screens)
        qtile.call_later(1, self.apply_theme)

    def apply_theme(self, *_args):
        color_scheme = self.theme.color.scheme.palette
        colors_rainbow_mode = self.theme.color.rainbow
        bar_split_mode = self.theme.bar.split
        bar_transparent_mode = self.theme.bar.transparent

        setattr(
            self.bar,
            "background",
            rgba(color_scheme.background, int(not bar_transparent_mode)),
        )

        def set_properties(wid: _Widget, attributes: dict[str, Any]):
            for attr, value in attributes.items():
                if attr == "background":
                    if bar_transparent_mode:
                        value = rgba(value, 0)
                    elif bar_split_mode and isinstance(
                        wid, (widget.WindowName, widget.TaskList)
                    ):
                        value = rgba(value, 0)
                setattr(wid, attr, value)

        for i, wid in enumerate(self.left_widgets):
            if colors_rainbow_mode:
                bg = color_scheme.color_sequence[-i % len(color_scheme.color_sequence)]
                fg = invert_hex_color_of(bg)
            else:
                bg = color_scheme.highlight
                fg = (
                    color_scheme.active
                    if color_scheme.active != bg
                    else invert_hex_color_of(bg) if bg else None
                )

            attrs: dict[str, Any] = {
                "background": bg,
                "foreground": fg,
            }

            set_properties(wid, attrs)

        for i, wid in enumerate(self.right_widgets):
            if colors_rainbow_mode:
                bg = color_scheme.color_sequence[i % len(color_scheme.color_sequence)]
                fg = invert_hex_color_of(bg)
            else:
                bg = color_scheme.inactive
                fg = (
                    color_scheme.active
                    if color_scheme.active != bg
                    else invert_hex_color_of(bg) if bg else None
                )

            attrs: dict[str, Any] = {
                "background": bg,
                "foreground": fg,
            }

            set_properties(wid, attrs)

        if self.bar.screen:
            self.bar.draw()
            self.bar.screen.group.layout_all()
