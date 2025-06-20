import threading
import os
import subprocess
from qtile_extras.widget import GenPollText, decorations
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal
from typing import Any
from .typing import VagrantConfig

terminal = guess_terminal()


class Vagrant(GenPollText):
    def __init__(self, config: VagrantConfig, **kwargs: Any):
        self.config = config
        self.state_symbols_map = {
            "running": self.config.running_symbol,
            "not_created": self.config.not_created_symbol,
            "poweroff": self.config.poweroff_symbol,
            "aborted": self.config.aborted_symbol,
            "saved": self.config.saved_symbol,
            "stopped": self.config.stopped_symbol,
            "frozen": self.config.frozen_symbol,
            "shutoff": self.config.shutoff_symbol,
            "unknown": self.config.unknown_symbol,
            "error": self.config.error_symbol,
            "partial_running_symbol": self.config.partial_running_symbol,
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
        self.format = "{symbol} {label}"
        super().__init__(func=self.check_vagrant_status, **kwargs)

    def log_errors(self, msg):
        if self.config.enable_logger:
            logger.error(msg)

    def run_in_thread(self, target, *args):
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()

    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                cwd=self.config.vagrant_dir,
                shell=True,
                text=True,
                capture_output=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.log_errors(f"Command failed: {command}\n{result.stderr.strip()}")
                return None
        except Exception as e:
            self.log_errors(f"Error running command: {str(e)}")
            return None

    def check_vagrant_status(self):
        label = (
            self.config.label
            if self.config.label is not None
            else os.path.basename(os.path.normpath(self.config.vagrant_dir))
        )
        if not os.path.exists(self.config.vagrant_dir):
            return self.format.format(
                symbol=self.state_symbols_map["unknown"],
                label=label,
            )
        try:
            output = self.run_command("vagrant status --machine-readable")
            if not output:
                return self.format.format(
                    symbol=self.state_symbols_map["unknown"],
                    label=label,
                )

            statuses: dict[str, int] = {}
            for line in output.splitlines():
                parts = line.split(",")
                if len(parts) >= 4 and parts[2] == "state":
                    state = parts[3]
                    statuses[state] = statuses.get(state, 0) + 1

            total_machines = sum(statuses.values())
            running_count = statuses.get("running", 0)
            add_machine_status_str = False

            if len(statuses) == 1:
                state = next(iter(statuses))
                symbol = self.state_symbols_map.get(
                    state, self.state_symbols_map["unknown"]
                )
            elif running_count == 0:
                max_state = max(statuses, key=lambda k: statuses[k])
                symbol = self.state_symbols_map.get(
                    max_state, self.state_symbols_map["unknown"]
                )
                if statuses[max_state] != total_machines:
                    add_machine_status_str = True
            else:
                symbol = self.state_symbols_map["partial_running_symbol"]
                add_machine_status_str = True

            if add_machine_status_str:
                if self.config.detailed_status:
                    machine_status_str = (
                        "("
                        + " | ".join(
                            f"{self.state_symbols_map.get(state, self.state_symbols_map['unknown'])}: {count}"
                            for state, count in statuses.items()
                        )
                        + ")"
                    )
                else:
                    machine_status_str = f"({running_count}/{total_machines})"
            else:
                machine_status_str = ""

            return self.format.format(
                symbol=symbol, label=f"{label} {machine_status_str}"
            )
        except Exception as e:
            self.log_errors(f"Error checking Vagrant status: {str(e)}")
            return self.format.format(
                symbol=self.state_symbols_map["error"], label=label
            )

    def button_press(self, x, y, button):
        if button == 1:  # Left-click: Start all machines
            self.run_in_thread(self.handle_start_vagrant)
        elif button == 3:  # Right-click: Stop all machines
            self.run_in_thread(self.handle_stop_vagrant)
        elif button == 2:  # Middle-click: Destroy all machines
            self.run_in_thread(self.handle_destroy_vagrant)

    def handle_start_vagrant(self):
        cmd = f"{terminal} -e vagrant up"
        subprocess.Popen(
            cmd,
            cwd=self.config.vagrant_dir,
            shell=True,
        )

    def handle_stop_vagrant(self):
        cmd = f"{terminal} -e vagrant halt"
        subprocess.Popen(
            cmd,
            cwd=self.config.vagrant_dir,
            shell=True,
        )

    def handle_destroy_vagrant(self):
        cmd = f"{terminal} -e vagrant destroy -f"
        subprocess.Popen(
            cmd,
            cwd=self.config.vagrant_dir,
            shell=True,
        )
