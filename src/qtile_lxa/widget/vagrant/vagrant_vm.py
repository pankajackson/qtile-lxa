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
from .runner import VagrantCLI

terminal = guess_terminal()


class VagrantVM(GenPollText):
    def __init__(self, config: VagrantVMConfig, **kwargs: Any):
        self.config = config
        self.vm_name = "unknown"

        # Root directory where VM-specific folders live
        self.base_dir = Path.home() / ".lxa_vagrant"

        if not self.config.skip_vagrantfile:
            if not self.config.name or not self.config.box:
                raise ValueError("VM `name` and `box` is required")

            # Folder for this specific VM
            self.vagrant_dir = (
                self.config.vagrant_dir or self.base_dir / self.config.name
            )
            self.vagrant_dir.mkdir(parents=True, exist_ok=True)

            # Load + render template resources
            self.resources = VagrantVMConfigResources(
                config=config, output_dir=self.vagrant_dir
            )

        # Vagrant → symbol mapping
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
        super().__init__(func=self.check_vm_status, **kwargs)

    def log_errors(self, msg):
        if self.config.enable_logger:
            logger.error(msg)

    def run_in_thread(self, target, *args):
        t = threading.Thread(target=target, args=args, daemon=True)
        t.start()

    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                cwd=self.vagrant_dir,
                shell=True,
                text=True,
                capture_output=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()

            self.log_errors(f"Command failed ({command}):\n{result.stderr.strip()}")
            return None

        except Exception as e:
            self.log_errors(f"Error running command '{command}': {e}")
            return None

    def check_vm_status(self):
        if self.config.vagrant_dir is None:
            return self.format.format(
                symbol=self.state_symbols_map["unknown"],
                label=self.config.label or self.config.name or "unknown",
            )
        vg_cli = VagrantCLI(self.config.vagrant_dir)
        vm = vg_cli.get_vm(self.config.name)
        if not vm:
            return self.format.format(
                symbol=self.state_symbols_map["unknown"],
                label=self.config.label or self.config.name or "unknown",
            )
        self.vm_name = vm.name
        state = vm.state
        symbol = self.state_symbols_map.get(state, self.config.unknown_symbol)
        return self.format.format(symbol=symbol, label=self.config.label or vm.name)

    def button_press(self, x, y, button):
        if button == 1:  # Left-click: Start all machines
            self.run_in_thread(self.handle_start_vagrant)
        elif button == 3:  # Right-click: Stop all machines
            self.run_in_thread(self.handle_stop_vagrant)
        elif button == 2:  # Middle-click: Destroy all machines
            self.run_in_thread(self.handle_destroy_vagrant)

    def handle_start_vagrant(self):
        if self.config.vagrant_dir:
            vg_cli = VagrantCLI(self.config.vagrant_dir)
            vg_cli.start_vm(self.vm_name)

    def handle_stop_vagrant(self):
        if self.config.vagrant_dir:
            vg_cli = VagrantCLI(self.config.vagrant_dir)
            vg_cli.stop_vm(self.vm_name)

    def handle_destroy_vagrant(self):
        if self.config.vagrant_dir:
            vg_cli = VagrantCLI(self.config.vagrant_dir)
            vg_cli.destroy_vm(self.vm_name)
