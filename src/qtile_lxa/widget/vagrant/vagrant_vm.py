import threading
import subprocess
from pathlib import Path
import csv
from io import StringIO
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal
from qtile_extras.widget import GenPollText, decorations
from typing import Any
from .typing_vm import VagrantVMConfig
from .resources import VagrantVMConfigResources

terminal = guess_terminal()


class VagrantVM(GenPollText):
    def __init__(self, config: VagrantVMConfig, **kwargs: Any):
        self.config = config
        self.base_dir = Path.home() / f".lxa_vagrant/{self.config.name}"
        self.data_dir = self.config.data_dir or self.base_dir
        self.resources = VagrantVMConfigResources(
            config=config, output_dir=self.data_dir
        )
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

    def get_vm_list(self):
        output = self.run_command("vagrant status --machine-readable")
        if not output:
            return []

        vms = {}

        reader = csv.reader(StringIO(output))
        for row in reader:
            # Machine-readable must have 4+ columns
            if len(row) < 4:
                continue

            _, machine, field, value = row[:4]

            # Skip the final UI summary line where machine = ""
            if machine == "":
                continue

            # Ensure entry exists
            if machine not in vms:
                vms[machine] = {
                    "name": machine,
                    "provider": None,
                    "state": None,
                    "state_short": None,
                    "state_long": None,
                }

            # Map fields to our structure
            if field == "provider-name":
                vms[machine]["provider"] = value

            elif field == "state":
                vms[machine]["state"] = value

            elif field == "state-human-short":
                vms[machine]["state_short"] = value

            elif field == "state-human-long":
                # Make multiline text cleaner
                vms[machine]["state_long"] = value.replace("\\n", "\n")

        # Convert dict → list
        return list(vms.values())

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
