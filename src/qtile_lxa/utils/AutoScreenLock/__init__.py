import subprocess
from qtile_lxa import __DEFAULTS__, __ASSETS_DIR__

# Settings for xidlehook
theme = "light"  # dark or light theme
DEFAULT_LOCK_TIME = 1  # Lock after 1 minute of inactivity
NOTIFY_BEFORE_LOCK = 30  # Notify 30 seconds before locking
DIM_DURATION = 5  # Dim screen after 5 seconds of Notification
LOCKER_CMD = (
    f"betterlockscreen -l {__DEFAULTS__.theme_manager.pywall.screenlock_effect or None}"
)
NOTIFY_CMD = f"dunstify -a 'ScreenLock' -r 9995 'ScreenLock' -i '{__ASSETS_DIR__}/icons/inactive-{theme}.png' 'Locking screen in {NOTIFY_BEFORE_LOCK} sec' -t 5000"


# Get the primary display dynamically
primary_display = subprocess.run(
    ["xrandr", "--listactivemonitors"], capture_output=True, text=True
)
primary_monitor = (
    primary_display.stdout.splitlines()[1].split()[-1]
    if primary_display.returncode == 0
    else "eDP-1"
)


def start_xidlehook(lock_time: int = DEFAULT_LOCK_TIME):
    idle_locker_hook = [
        "xidlehook",
        "--not-when-fullscreen",
        # "--not-when-audio",
        # Notification timer
        "--timer",
        str((lock_time * 60) - NOTIFY_BEFORE_LOCK),
        NOTIFY_CMD,
        "''",
        # Locking timer
        "--timer",
        str(NOTIFY_BEFORE_LOCK),
        LOCKER_CMD,
        "''",
    ]
    idle_brightness_hook = [
        "xidlehook",
        "--not-when-fullscreen",
        # "--not-when-audio",
        "--timer",
        str((lock_time * 60) - NOTIFY_BEFORE_LOCK + 5),
        f"xrandr --output {primary_monitor} --brightness 0.2",
        f"xrandr --output {primary_monitor} --brightness 1",
    ]

    subprocess.Popen(idle_locker_hook)
    subprocess.Popen(idle_brightness_hook)
