import subprocess
import threading
import json
from pathlib import Path
from qtile_extras.widget import GenPollText, decorations
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal
from typing import Any, Literal
from .typing import MultipassConfig

terminal = guess_terminal()


class MultipassVM(GenPollText):
    def __init__(self, config: MultipassConfig, **kwargs: Any) -> None:
        self.config = config
        self.decorations = [
            decorations.RectDecoration(
                colour="#333366",
                radius=10,
                filled=True,
                padding_y=4,
                group=True,
                extrawidth=5,
            )
        ]
        self.format = "{symbol} {label}"
        super().__init__(func=self.get_text, **kwargs)

    def log(self, msg: str):
        if self.config.enable_logger:
            logger.error(msg)

    def run_command(self, cmd):
        try:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.stderr:
                self.log(f"stderr: {result.stderr.strip()}")
            return result.stdout.strip()
        except FileNotFoundError:
            self.log(
                "Error: 'multipass' command not found. Is Multipass installed and in PATH?"
            )
            return None
        except subprocess.SubprocessError as e:
            self.log(f"Error running command: {' '.join(cmd)} - {str(e)}")
            return None

    def run_in_thread(self, target, *args):
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()

    def get_instance_info(self):
        cmd = ["multipass", "list", "--format", "json"]
        output = self.run_command(cmd)
        if not output:
            return None
        try:
            instances = json.loads(output).get("list", [])
            for inst in instances:
                if inst["name"] == self.config.instance_name:
                    return inst
            return None
        except json.JSONDecodeError as e:
            self.log(f"JSON decode error: {e}")
            return None

    def check_vm_status(self) -> Literal["running", "stopped", "unknown", "error"]:
        info = self.get_instance_info()
        if not info:
            return "unknown"
        state = info.get("state", "").lower()
        if "running" in state:
            return "running"
        elif "stopped" in state:
            return "stopped"
        else:
            return "error"

    def get_text(self):
        symbol_map = {
            "stopped": self.config.stopped_symbol,
            "running": self.config.running_symbol,
            "unknown": self.config.unknown_symbol,
            "error": self.config.error_symbol,
        }
        try:
            status = self.check_vm_status()
        except Exception as e:
            self.log(f"Exception in get_text: {e}")
            status = "error"
        return self.format.format(
            symbol=symbol_map.get(status, self.config.unknown_symbol),
            label=self.config.label or self.config.instance_name,
        )

    def button_press(self, x, y, button):
        if button == 1:
            self.run_in_thread(self.handle_start_vm)
        elif button == 3:
            self.run_in_thread(self.handle_stop_vm)
        elif button == 2:
            self.run_in_thread(self.handle_delete_vm)

    def handle_launch_vm(self):
        launch_cmd = [
            "multipass",
            "launch",
            "--name",
            self.config.instance_name,
        ]

        if self.config.cpus:
            launch_cmd += ["--cpus", str(self.config.cpus)]
        if self.config.memory:
            launch_cmd += ["--memory", str(self.config.memory)]
        if self.config.disk:
            launch_cmd += ["--disk", str(self.config.disk)]
        if self.config.cloud_init_path and Path(self.config.cloud_init_path).exists():
            launch_cmd += ["--cloud-init", str(self.config.cloud_init_path)]
        if self.config.image:
            launch_cmd += [str(self.config.image)]

        # Base shell command
        shell_cmd = [" ".join(launch_cmd)]

        # Append mount commands as a chain
        if self.config.shared_volumes:
            for shared_volume in self.config.shared_volumes:
                shell_cmd.append(
                    f"multipass mount {shared_volume.source_path} {self.config.instance_name}:{shared_volume.target_path}"
                )

        full_shell_command = " && ".join(shell_cmd)

        terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
        subprocess.Popen(terminal_cmd, shell=True)

    def handle_start_vm(self):
        status = self.check_vm_status()
        if status == "unknown":
            self.handle_launch_vm()
        elif status == "stopped":
            subprocess.Popen(
                f"{terminal} -e multipass start {self.config.instance_name}", shell=True
            )
        else:
            self.open_shell()

    def handle_stop_vm(self):
        subprocess.Popen(
            f"{terminal} -e multipass stop {self.config.instance_name}", shell=True
        )

    def handle_delete_vm(self):
        subprocess.Popen(
            f"{terminal} -e multipass delete {self.config.instance_name} && multipass purge",
            shell=True,
        )

    def open_shell(self):
        subprocess.Popen(
            f"{terminal} -e multipass shell {self.config.instance_name}", shell=True
        )
