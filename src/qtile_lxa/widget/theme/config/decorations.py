from qtile_extras.widget.decorations import PowerLineDecoration


decorations = {
    "arrows": {
        "left_decoration": [PowerLineDecoration(path="arrow_left")],
        "right_decoration": [PowerLineDecoration(path="arrow_right")],
    },
    "rounded": {
        "left_decoration": [PowerLineDecoration(path="rounded_left")],
        "right_decoration": [PowerLineDecoration(path="rounded_right")],
    },
    "slash": {
        "left_decoration": [PowerLineDecoration(path="back_slash")],
        "right_decoration": [PowerLineDecoration(path="forward_slash")],
    },
    "zig_zag": {
        "left_decoration": [PowerLineDecoration(path="zig_zag")],
        "right_decoration": [PowerLineDecoration(path="zig_zag")],
    },
}
