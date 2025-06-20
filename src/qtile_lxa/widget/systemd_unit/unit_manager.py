import subprocess
from libqtile.widget import base
from qtile_extras.widget import GenPollText
from libqtile.log_utils import logger
from typing import Any
from .typing import UnitManagerConfig


class UnitManager(GenPollText):
    orientations = base.ORIENTATION_BOTH

    def __init__(
        self,
        config: UnitManagerConfig,
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
        super().__init__(func=self.check_status, **kwargs)
        self.add_callbacks({"Button1": self.toggle_unit})

    def check_status(self):
        try:
            result = subprocess.run(
                ["systemctl", "is-active", self.config.unit_name],
                capture_output=True,
                text=True,
            )
            status = result.stdout.strip()
            symbol = self.status_symbols_map.get(
                status, self.status_symbols_map["unknown"]
            )
            return (
                f"{symbol} {self.config.label}"
                if self.config.status_symbol_first
                else f"{self.config.label} {symbol}"
            )
        except Exception as e:
            logger.error(f"Error checking status of {self.config.unit_name}: {e}")
            return f"{self.config.label}: Error"

    def toggle_unit(self):
        current_status = (
            self.check_status().split(" ")[0]
            if self.config.status_symbol_first
            else self.check_status().split(" ")[1]
        )

        if current_status == self.status_symbols_map["active"]:
            action = "stop"
        else:
            action = "start"

        try:
            subprocess.run(
                ["sudo", "systemctl", action, self.config.unit_name],
                capture_output=True,
                text=True,
            )

            # Update the status immediately after toggling
            self.update(self.poll())
        except Exception as e:
            logger.error(f"Error toggling {self.config.unit_name}: {e}")
            self.update(f"{self.config.label}: Error")
