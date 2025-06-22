import subprocess
from threading import Timer
from libqtile import qtile
from libqtile.log_utils import logger
import psutil
from typing import Literal
import GPUtil


def toggle_and_auto_close_widgetbox(widget_name, close_after=5):
    widget = qtile.widgets_map[widget_name]
    widget.toggle()
    if widget.box_is_open:
        Timer(
            close_after, lambda: widget.toggle() if widget.box_is_open else None
        ).start()


def check_battery():
    battery = psutil.sensors_battery()
    if battery is not None:
        return True
    else:
        return False


def get_hostname():
    hostname = (
        subprocess.check_output(["hostnamectl hostname"], shell=True)
        .decode("utf-8")
        .strip()
    )
    return hostname


def toggle_systemd_unit(service_name: str, level: Literal["user", "system"] = "system"):
    cmds = {
        "check": ["systemctl", "is-active", "--quiet", service_name],
        "start": ["systemctl", "start", service_name],
        "stop": ["systemctl", "stop", service_name],
    }

    # Modify commands based on the level
    for action, command in cmds.items():
        if (level == "system") or (level is None):
            cmds[action].insert(0, "sudo")
        else:
            cmds[action].insert(1, "--user")

    try:
        # Check if the service is active
        subprocess.run(cmds["check"], check=True)

        # Service is active, stop it
        subprocess.run(cmds["stop"], check=True)
        logger.info(f"Service {service_name} stopped.")
    except subprocess.CalledProcessError:
        # Service is not active, start it
        subprocess.run(cmds["start"], check=True)
        logger.info(f"Service {service_name} started.")


def is_gpu_present() -> bool:
    try:
        gpus = GPUtil.getGPUs()
        return len(gpus) > 0
    except Exception:
        return False
