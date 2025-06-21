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


def get_current_volume():
    return (
        subprocess.check_output(
            ["pactl -- get-sink-volume 0 | awk -F'/' '{print $2}'"], shell=True
        )
        .decode("utf-8")
        .strip()
        .replace("%", "")
    )


# Function to process the sink (output device) names
def process_name(name):
    parts = re.split(r"[_\- ]", name)
    processed_name = [part for part in parts if not part.isdigit()]
    return " ".join(processed_name)


# Get the currently active sink (output device)
def get_current_sink():
    result = subprocess.run(["pactl", "info"], capture_output=True, text=True)
    match = re.search(r"Default Sink: (\S+)", result.stdout)
    return match.group(1) if match else None


# List all available sinks
def get_sinks():
    result = subprocess.run(
        ["pactl", "list", "short", "sinks"], capture_output=True, text=True
    )
    sinks = [line.split()[1] for line in result.stdout.splitlines()]
    return sinks


# Extract descriptions and process them to get cleaner names
def get_sink_names():
    result = subprocess.run(["pactl", "list", "sinks"], capture_output=True, text=True)
    sink_names = []
    for line in result.stdout.splitlines():
        if line.strip().startswith("Description:"):
            description = re.sub(r"^\s*Description:\s*", "", line).strip()
            processed = process_name(description)
            sink_names.append(processed)
    return sink_names


# Find the index of the current sink
def find_current_index(sinks, current_sink):
    try:
        return sinks.index(current_sink)
    except ValueError:
        _log_error("Sink index not found")
        return None


# Get the human-readable name of the current sink
def get_current_sink_name():
    current_sink = get_current_sink()
    if not current_sink:
        _log_error("Unknown Sink")
        return "Unknown Sink"

    sinks = get_sinks()
    sink_names = get_sink_names()

    try:
        current_index = find_current_index(sinks, current_sink)
        return (
            sink_names[current_index] if current_index is not None else "Unknown Sink"
        )
    except ValueError:
        _log_error("Unknown Sink")
        return "Unknown Sink"


# Switch to the next sink
def set_next_sink(sinks, current_index):
    next_index = (current_index + 1) % len(sinks)
    subprocess.run(["pactl", "set-default-sink", sinks[next_index]])
    return next_index


# Move all playing audio streams to the new sink
def move_audio_streams(sink):
    result = subprocess.run(
        ["pactl", "list", "short", "sink-inputs"], capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        stream_id = line.split()[0]
        subprocess.run(["pactl", "move-sink-input", stream_id, sink])


def send_volume_notification(is_mute=False):
    theme = "light"  # dark or light theme
    vol_icon_normal = __ASSETS_DIR__ / f"icons/volume-normal-{theme}.png"
    vol_icon_low = __ASSETS_DIR__ / f"icons/volume-low-{theme}.png"
    vol_icon_high = __ASSETS_DIR__ / f"icons/volume-high-{theme}.png"
    vol_icon_mute = __ASSETS_DIR__ / f"icons/volume-mute-{theme}.png"

    def get_int_of(input_value):
        out_val = re.search(r"\d+", input_value)
        if out_val:
            return int(out_val.group())
        return 0

    volume = "0" if is_mute else get_current_volume()
    text = "Mute" if is_mute else "Volume"
    icon = (
        vol_icon_mute
        if is_mute or get_int_of(volume) <= 0
        else (
            vol_icon_low
            if get_int_of(volume) < 50
            else (vol_icon_normal if get_int_of(volume) < 100 else vol_icon_high)
        )
    )
    sound_file = __ASSETS_DIR__ / "sounds/volume-notification.wav"
    sink_name = get_current_sink_name()

    # Escape the sink_name to prevent issues with special characters like apostrophes

    # Notification with the human-readable sink name
    send_notification(
        title=text,
        msg=sink_name,
        app_name="Volume",
        progress=int(volume),
        icon=icon,
        app_id=9993,
        timeout=2000,
    )
    subprocess.Popen(["aplay", sound_file])


@lazy.function
def volume_up(qtile):
    if (
        int(get_current_volume().replace("%", "").strip())
        < __DEFAULTS__.media.max_volume
    ):
        subprocess.run("pactl set-sink-volume 0 +5%", shell=True)
    send_volume_notification()


@lazy.function
def volume_down(qtile):
    subprocess.run("pactl set-sink-volume 0 -5%", shell=True)
    send_volume_notification()


@lazy.function
def toggle_mute(qtile):
    subprocess.run("pactl set-sink-mute 0 toggle", shell=True)
    is_mute = "yes" in (
        subprocess.check_output(["pactl get-sink-mute 0"], shell=True)
        .decode("utf-8")
        .strip()
    )
    send_volume_notification(is_mute=is_mute)


@lazy.function
def switch(qtile):
    current_sink = get_current_sink()
    if not current_sink:
        _log_error("Could not find the current sink.")
        return

    sinks = get_sinks()

    current_index = find_current_index(sinks, current_sink)
    if current_index is None:
        _log_error("Could not find the current sink in the list.")
        return

    next_index = set_next_sink(sinks, current_index)
    move_audio_streams(sinks[next_index])
    send_volume_notification()
