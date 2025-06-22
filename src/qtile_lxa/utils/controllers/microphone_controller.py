import os
import re
import shlex
import subprocess
from libqtile.lazy import lazy
from libqtile.log_utils import logger
from qtile_lxa import __DEFAULTS__, __ASSETS_DIR__
from qtile_lxa.utils.notification import send_notification


log_enabled = True


def _log_error(msg):
    if log_enabled:
        logger.error(msg)
        print(msg)


def get_current_source_volume():
    return (
        subprocess.check_output(
            ["pactl -- get-source-volume 0 | awk -F'/' '{print $2}'"], shell=True
        )
        .decode("utf-8")
        .strip()
        .replace("%", "")
    )


# Use the existing process_name function to clean the source name
def process_name(name):
    parts = re.split(r"[_\- ]", name)
    processed_name = [part for part in parts if not part.isdigit()]
    return " ".join(processed_name)


# Get the currently active source (microphone input device)
def get_current_source():
    result = subprocess.run(["pactl", "info"], capture_output=True, text=True)
    match = re.search(r"Default Source: (\S+)", result.stdout)
    return match.group(1) if match else None


# List all available sources
def get_sources():
    result = subprocess.run(
        ["pactl", "list", "short", "sources"], capture_output=True, text=True
    )
    sources = [
        line.split()[1]
        for line in result.stdout.splitlines()
        if line.split()[1].startswith("alsa_input")
    ]
    return sources


# Extract descriptions and process them to get cleaner names
def get_source_names():
    result = subprocess.run(
        ["pactl", "list", "sources"], capture_output=True, text=True
    )
    source_names = []
    for line in result.stdout.splitlines():
        if line.strip().startswith("Description:"):
            description = re.sub(r"^\s*Description:\s*", "", line).strip()
            processed = process_name(description)
            source_names.append(processed)
    return source_names


# Find the index of the current source
def find_current_index(sources, current_source):
    try:
        return sources.index(current_source)
    except ValueError:
        _log_error("Source index not found")
        return None


# Get the human-readable name of the current source
def get_current_source_name():
    current_source = get_current_source()
    if not current_source:
        _log_error("Unknown Source")
        return "Unknown Source"

    sources = get_sources()
    source_names = get_source_names()

    try:
        current_index = find_current_index(sources, current_source)
        return (
            source_names[current_index]
            if current_index is not None
            else "Unknown Source"
        )
    except ValueError:
        _log_error("Unknown Source")
        return "Unknown Source"


# Switch to the next source
def set_next_source(sources, current_index):
    next_index = (current_index + 1) % len(sources)
    subprocess.run(["pactl", "set-default-source", sources[next_index]])
    return next_index


def send_source_notification(is_mute=False):

    theme = "light"  # dark or light theme
    mic_icon_normal = __ASSETS_DIR__ / f"icons/mic-normal-{theme}.png"
    mic_icon_mute = __ASSETS_DIR__ / f"icons/mic-mute-{theme}.png"

    def get_int_of(input_value):
        out_val = re.search(r"\d+", input_value)
        if out_val:
            return int(out_val.group())
        return 0

    volume = "0" if is_mute else get_current_source_volume()
    text = "Mute" if is_mute else "Microphone"
    icon = mic_icon_mute if is_mute or get_int_of(volume) <= 0 else mic_icon_normal
    sound_file = __ASSETS_DIR__ / "sounds/microphone-notification.wav"
    source_name = get_current_source_name()

    send_notification(
        title=text,
        msg=source_name,
        app_name="Microphone",
        progress=int(volume),
        icon=icon,
        app_id=9992,
        timeout=2000,
    )
    subprocess.Popen(["aplay", sound_file])


@lazy.function
def volume_up(qtile):
    if (
        int(get_current_source_volume().replace("%", "").strip())
        < __DEFAULTS__.media.max_volume
    ):
        subprocess.run("pactl set-source-volume 0 +5%", shell=True)
    send_source_notification()


@lazy.function
def volume_down(qtile):
    subprocess.run("pactl set-source-volume 0 -5%", shell=True)
    send_source_notification()


@lazy.function
def toggle_mute(qtile):
    subprocess.run("pactl set-source-mute 0 toggle", shell=True)
    is_mute = "yes" in (
        subprocess.check_output(["pactl get-source-mute 0"], shell=True)
        .decode("utf-8")
        .strip()
    )
    send_source_notification(is_mute=is_mute)


@lazy.function
def switch(qtile):
    current_source = get_current_source()
    if not current_source:
        _log_error("Could not find the current source.")
        return

    sources = get_sources()

    current_index = find_current_index(sources, current_source)
    if current_index is None:
        _log_error("Could not find the current source in the list.")
        return

    next_index = set_next_source(sources, current_index)

    # Notify the user
    send_source_notification()
