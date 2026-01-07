from typing import Any
from enum import Enum, auto
from libqtile import qtile, hook, bar
from libqtile.widget.base import _Widget
from libqtile.log_utils import logger
from qtile_extras import widget
from qtile_lxa import __DEFAULTS__
from ..config import ThemeAware, ColorSchemeConfig
from ..manager import ThemeManager, DecorationChanger
from ..utils.colors import rgba, invert_hex_color_of


class WidgetPos(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


class CenterLayout(Enum):
    CENTERED = auto()  # current behavior
    NO_SPACERS = auto()  # no spacers at all
    LEFT_SPACER = auto()  # spacer only on left
    RIGHT_SPACER = auto()  # spacer only on right


class CenterTransparency(Enum):
    NEVER = auto()
    ON_SPLIT = auto()
    ALWAYS = auto()


class DecoratedBar:
    def __init__(
        self,
        manager: ThemeManager,
        left_widgets: list[_Widget] | None = None,
        center_widgets: list[_Widget] | None = None,
        right_widgets: list[_Widget] | None = None,
        *,
        center_layout: CenterLayout = CenterLayout.CENTERED,
        center_transparency: CenterTransparency = CenterTransparency.NEVER,
        size: int = 30,
        **bar_kwargs,
    ):
        self.manager = manager
        self.theme = self.manager.theme
        self._bar_kwargs = bar_kwargs
        self.active_decoration = self.theme.decoration
        self._raw_left_widgets = left_widgets or []
        self._raw_center_widgets = center_widgets or []
        self._raw_right_widgets = right_widgets or []
        self.center_layout = center_layout
        self.center_transparency = center_transparency
        self.left_widgets = self._decorated_widgets(
            self._raw_left_widgets, WidgetPos.LEFT
        )
        self.center_widgets = self._decorate_center_widgets(self._raw_center_widgets)
        self.right_widgets = self._decorated_widgets(
            self._raw_right_widgets, WidgetPos.RIGHT
        )
        self.bar: bar.Bar = bar.Bar(
            widgets=[*self.left_widgets, *self.center_widgets, *self.right_widgets],
            background=rgba(self.theme.color.scheme.palette.background, 0),
            size=size,
            **bar_kwargs,
        )
        self._subscribe_controllers()

        # TODO: Find permanent fix of this
        hook.subscribe.screen_change(self.apply_theme)
        # qtile.call_later(3, self.apply_theme)

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

    def _decorate(self, w: _Widget, d):
        if d:
            setattr(w, "decorations", d)

    def _decorated_widgets(
        self,
        wid_list: list[_Widget],
        pos: WidgetPos,
    ):
        dec = {
            WidgetPos.LEFT: self.theme.decoration.value.left_decoration,
            WidgetPos.CENTER: None,
            WidgetPos.RIGHT: self.theme.decoration.value.right_decoration,
        }[pos]

        decorated: list[_Widget] = []
        for wid in wid_list:
            is_last_right = (
                pos is WidgetPos.RIGHT
                and self._raw_right_widgets
                and wid is self._raw_right_widgets[-1]
            )
            if not is_last_right:
                self._decorate(wid, dec)
            decorated.append(wid)
        return decorated

    def _decorate_center_widgets(self, wid_list: list[_Widget]) -> list[_Widget]:
        def _spacer(length: int | None = None):
            if length is not None:
                return self._decorated_widgets(
                    [widget.Spacer(length=length)], WidgetPos.RIGHT
                )
            return self._decorated_widgets([widget.Spacer()], WidgetPos.RIGHT)

        left_spacer = (
            _spacer()
            if self.center_layout
            in {
                CenterLayout.CENTERED,
                CenterLayout.LEFT_SPACER,
            }
            else _spacer(length=1)
        )

        right_spacer = (
            _spacer()
            if self.center_layout
            in {
                CenterLayout.CENTERED,
                CenterLayout.RIGHT_SPACER,
            }
            else _spacer(length=1)
        )

        n = len(wid_list)

        # No widgets → just spacers
        if n == 0:
            return [*left_spacer, *right_spacer]

        # One widget → centered, no decoration
        if n == 1:
            return [
                *left_spacer,
                *self._decorated_widgets([wid_list[0]], WidgetPos.LEFT),
                *right_spacer,
            ]

        # Two widgets → split decorations
        if n == 2:
            return [
                *left_spacer,
                *self._decorated_widgets([wid_list[0]], WidgetPos.RIGHT),
                *self._decorated_widgets([wid_list[1]], WidgetPos.LEFT),
                *right_spacer,
            ]

        # Three or more
        mid = n // 2

        if n % 2 == 1:
            left = wid_list[:mid]
            center = wid_list[mid]
            right = wid_list[mid + 1 :]
        else:
            left = wid_list[:mid]
            center = None
            right = wid_list[mid:]

        result: list[_Widget] = []
        result.extend(left_spacer)
        result.extend(self._decorated_widgets(left, WidgetPos.RIGHT))

        if center:
            result.extend(self._decorated_widgets([center], WidgetPos.RIGHT))

        result.extend(self._decorated_widgets(right, WidgetPos.LEFT))
        result.extend(right_spacer)

        return result

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

        self.left_widgets = self._decorated_widgets(
            self._raw_left_widgets, WidgetPos.LEFT
        )
        self.center_widgets = self._decorate_center_widgets(self._raw_center_widgets)
        self.right_widgets = self._decorated_widgets(
            self._raw_right_widgets, WidgetPos.RIGHT
        )

        new_bar = bar.Bar(
            widgets=[*self.left_widgets, *self.center_widgets, *self.right_widgets],
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
        # qtile.call_soon(qtile.reconfigure_screens)
        qtile.call_later(1, qtile.reconfigure_screens)
        qtile.call_later(1, self.apply_theme)

    def _resolve_colors(
        self,
        pos: WidgetPos,
        index: int,
        color_palette: ColorSchemeConfig,
        rainbow: bool,
    ):
        if rainbow:
            if pos is WidgetPos.LEFT:
                bg = color_palette.color_sequence[
                    -index % len(color_palette.color_sequence)
                ]
            elif pos is WidgetPos.RIGHT:
                bg = color_palette.color_sequence[
                    index % len(color_palette.color_sequence)
                ]
            else:  # CENTER
                bg = color_palette.background or color_palette.color_sequence[0]

            return bg, invert_hex_color_of(bg)

        # non-rainbow
        if pos is WidgetPos.LEFT:
            bg = color_palette.highlight
        elif pos is WidgetPos.CENTER:
            bg = color_palette.highlight
        else:  # RIGHT
            bg = color_palette.inactive

        fg = (
            color_palette.active
            if color_palette.active != bg
            else invert_hex_color_of(bg) if bg else None
        )
        return bg, fg

    def _apply_widget_group(
        self,
        widgets: list[_Widget],
        pos: WidgetPos,
    ):
        color_palette = self.theme.color.scheme.palette
        rainbow = self.theme.color.rainbow
        split = self.theme.bar.split
        transparent = self.theme.bar.transparent

        for i, wid in enumerate(widgets):
            bg, fg = self._resolve_colors(pos, i, color_palette, rainbow)

            attrs: dict[str, Any] = {
                "background": bg,
                "foreground": fg,
                "inactive": color_palette.inactive,
                "active": color_palette.active,
                "highlight_color": color_palette.highlight,
                "this_current_screen_border": color_palette.inactive,
                "block_highlight_text_color": color_palette.highlight,
            }

            for attr, value in attrs.items():
                if attr == "background":
                    if transparent:
                        value = rgba(value, 0)

                    elif pos is WidgetPos.CENTER:
                        is_spacer = (
                            isinstance(wid, widget.Spacer)
                            and wid not in self._raw_center_widgets
                        )
                        if self.center_transparency is CenterTransparency.ALWAYS:
                            value = rgba(value, 0)
                        elif split:
                            if is_spacer:
                                value = rgba(value, 0)
                            elif (
                                self.center_transparency is CenterTransparency.ON_SPLIT
                            ):
                                value = rgba(value, 0)

                setattr(wid, attr, value)

    def apply_theme(self, *_args):
        color_palette = self.theme.color.scheme.palette
        transparent = self.theme.bar.transparent

        setattr(
            self.bar,
            "background",
            rgba(color_palette.background, int(not transparent)),
        )

        self._apply_widget_group(self.left_widgets, WidgetPos.LEFT)
        self._apply_widget_group(self.center_widgets, WidgetPos.CENTER)
        self._apply_widget_group(self.right_widgets, WidgetPos.RIGHT)

        if self.bar.screen:
            self.bar.draw()
            self.bar.screen.group.layout_all()
