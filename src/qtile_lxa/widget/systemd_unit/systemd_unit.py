import subprocess
import shutil
from libqtile.widget import base
from qtile_extras.widget import GenPollText, decorations
from libqtile.log_utils import logger
from typing import Any, Literal
from .typing import SystemdUnitConfig


class SystemdUnit(GenPollText):
    orientations = base.ORIENTATION_BOTH

    def __init__(
        self,
        config: SystemdUnitConfig,
        **kwargs: Any,
    ):
        self.config = config
        self.config.label = (
            self.config.label if self.config.label else self.config.unit_name
        )
        self.status_symbols_map = {
            "active": self.config.active_symbol,
            "inactive": self.config.inactive_symbol,
            "failed": self.config.failed_symbol,
            "activating": self.config.activating_symbol,
            "deactivating": self.config.deactivating_symbol,
            "unknown": self.config.unknown_symbol,
        }
        self.status_colors_map = {
            "active": "#00ff00",
            "inactive": "#ff0000",
            "failed": "#ff0000",
            "unknown": "#888888",
            "activating": "#ffaa00",
            "deactivating": "#aaaa00",
        }
        self.decorations = [
            decorations.RectDecoration(
                colour="#004040",
                radius=10,
                filled=True,
                padding_y=4,
                group=True,
                extrawidth=5,
            )
        ]

        super().__init__(func=self.get_text, markup=self.config.markup, **kwargs)
        self.add_callbacks(
            {
                "Button1": self.toggle_unit,
                "Button2": self.restart_unit,
            }
        )

    def get_cmd(self, action: Literal["check", "start", "stop", "restart"]):

        assert shutil.which("systemctl"), "'systemctl' not found"
        if self.config.bus_name == "system":
            assert shutil.which("sudo"), "'sudo' not found for system services"

        cmd = ["systemctl"]
        if self.config.bus_name == "system":
            cmd.insert(0, "sudo")
        else:
            cmd.append("--user")

        if action == "check":
            cmd.extend(["is-active", self.config.unit_name])
        elif action == "start":
            cmd.extend(["start", self.config.unit_name])
        elif action == "stop":
            cmd.extend(["stop", self.config.unit_name])
        elif action == "restart":
            cmd.extend(["restart", self.config.unit_name])
        return cmd

    def check_status(self):
        try:
            result = subprocess.run(
                self.get_cmd("check"),
                capture_output=True,
                text=True,
            )
            status = result.stdout.strip()

            if status in self.status_symbols_map.keys():
                return status
            return "unknown"
        except Exception as e:
            logger.error(f"Error checking status of {self.config.unit_name}: {e}")
            return "failed"

    def get_text(self):
        status = self.check_status()
        symbol = self.status_symbols_map.get(status, self.status_symbols_map["unknown"])
        color = self.status_colors_map.get(status, "#ffffff")
        text = (
            f"{symbol} {self.config.label}"
            if self.config.status_symbol_first
            else f"{self.config.label} {symbol}"
        )

        if self.config.markup:
            return f"<span color='{color}'>{text}</span>"
        return text

    def toggle_unit(self):
        current_status = self.check_status()

        if current_status == "active":
            action = "stop"
        else:
            action = "start"

        try:
            subprocess.run(
                self.get_cmd(action),
                capture_output=True,
                text=True,
            )

            # Update the status immediately after toggling
            self.update(self.poll())
        except Exception as e:
            logger.error(f"Error toggling {self.config.unit_name}: {e}")
            self.update(f"{self.config.label}: Error")

    def restart_unit(self):
        try:
            subprocess.run(
                self.get_cmd("restart"),
                capture_output=True,
                text=True,
            )
            self.update(self.poll())
        except Exception as e:
            logger.error(f"Error restarting {self.config.unit_name}: {e}")
