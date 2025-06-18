"""
from settings.bars.screen_one_widgets import widget_list as s1wl
from settings.bars.screen_two_widgets import widget_list as s2wl

from qtile_lxa.widget import DecoratedBar


def get_decorated_bars(widget_list, height=30):

    bar_top = DecoratedBar(
        left_widgets=widget_list["top"]["left"],
        right_widgets=widget_list["top"]["right"],
        height=height,
    ).get_bar()
    bar_bottom = DecoratedBar(
        left_widgets=widget_list["bottom"]["left"],
        right_widgets=widget_list["bottom"]["right"],
        height=height,
    ).get_bar()
    bar_right = DecoratedBar(
        left_widgets=widget_list["right"]["left"],
        right_widgets=widget_list["right"]["right"],
        transparent=False,
    ).get_bar()
    bars = {
        "top": bar_top,
        "bottom": bar_bottom,
        "right": bar_right,
    }
    return bars


def get_all_bars():

    return [
        get_decorated_bars(widget_list=s1wl, height=40),
        get_decorated_bars(widget_list=s2wl),
    ]

"""
