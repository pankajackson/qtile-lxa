import os
import subprocess
from libqtile.lazy import lazy
from qtile_lxa import __ASSETS_DIR__
from qtile_lxa.utils.notification import send_notification


def get_current_brightness():
    return (
        subprocess.check_output(
            ["brightnessctl -m | awk -F, '{print substr($4, 0, length($4)-1)}'"],
            shell=True,
        )
        .decode("utf-8")
        .strip()
    )


def send_brightness_notification():
    theme = "light"  # dark or light ref https://icons8.com/icon/set/brightness/sf-black--static--white
    icon = __ASSETS_DIR__ / f"icons/brightness-{theme}.png"
    brightness = get_current_brightness()
    send_notification(
        title=f"Brightness",
        msg="Brightness",
        app_name="Brightness",
        progress=int(brightness),
        icon=icon,
        app_id=9994,
        timeout=1000,
    )


@lazy.function
def brightness_up(qtile):
    subprocess.run("brightnessctl set +10%", shell=True)
    send_brightness_notification()


@lazy.function
def brightness_down(qtile):
    subprocess.run("brightnessctl set 10%-", shell=True)
    send_brightness_notification()
