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

    def _append_script(self, shell_cmd: list, path, label: str, inside_vm=False):
        if not path:
            return
        if path.exists():
            cmd = (
                f"multipass exec {self.config.instance_name} -- bash -s < {path}"
                if inside_vm
                else f"bash {path}"
            )
            shell_cmd.append(cmd)
        else:
            self.log(f"{label} script not found: {path}")

    def handle_launch_vm(self):
        shell_cmd = []

        # 0: Pre-launch script (host side)
        self._append_script(shell_cmd, self.config.pre_launch_script, "Pre-launch")

        # 1: Build launch command
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
        shell_cmd.append(" ".join(launch_cmd))

        # 2: Mount shared volumes
        if self.config.shared_volumes:
            for shared_volume in self.config.shared_volumes:
                try:
                    shared_volume.source_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.log(
                        f"Failed to create shared volume {shared_volume.source_path}: {e}"
                    )
                shell_cmd.append(
                    f"multipass mount {shared_volume.source_path} {self.config.instance_name}:{shared_volume.target_path}"
                )

        # 3: Userdata script (inside VM)
        self._append_script(
            shell_cmd, self.config.userdata_script, "Userdata", inside_vm=True
        )

        # 4: Post-launch script (inside VM)
        self._append_script(
            shell_cmd, self.config.post_launch_script, "Post-launch", inside_vm=False
        )

        # Run all chained
        full_shell_command = (
            " && ".join(shell_cmd)
            + "; echo Press any key to close..."
            + "; stty -echo -icanon time 0 min 1; dd bs=1 count=1 >/dev/null 2>&1; stty sane"
        )

        terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
        subprocess.Popen(terminal_cmd, shell=True)

    def handle_start_vm(self):
        status = self.check_vm_status()
        if status == "unknown":
            self.handle_launch_vm()
        elif status == "stopped":

            # 1: Pre-start script
            shell_cmd = []
            self._append_script(
                shell_cmd, self.config.pre_start_script, "Pre-start", inside_vm=False
            )

            # 2: Start VM
            shell_cmd.append(f"multipass start {self.config.instance_name}")

            # 3: Post-start script
            self._append_script(
                shell_cmd, self.config.post_start_script, "Post-start", inside_vm=False
            )

            full_shell_command = (
                " && ".join(shell_cmd)
                + "; echo Press any key to close..."
                + "; stty -echo -icanon time 0 min 1; dd bs=1 count=1 >/dev/null 2>&1; stty sane"
            )
            terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
            subprocess.Popen(terminal_cmd, shell=True)
        else:
            self.open_shell()

    def handle_stop_vm(self):
        # 1: Pre-stop script
        shell_cmd = []
        self._append_script(
            shell_cmd, self.config.pre_stop_script, "Pre-stop", inside_vm=False
        )

        # 2: stop VM
        shell_cmd.append(f"multipass stop {self.config.instance_name}")

        # 3: Post-stop script
        self._append_script(
            shell_cmd, self.config.post_stop_script, "Post-stop", inside_vm=False
        )

        full_shell_command = (
            " && ".join(shell_cmd)
            + "; echo Press any key to close..."
            + "; stty -echo -icanon time 0 min 1; dd bs=1 count=1 >/dev/null 2>&1; stty sane"
        )
        terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
        subprocess.Popen(terminal_cmd, shell=True)

    def handle_delete_vm(self):
        # 1: Pre-delete script
        shell_cmd = []
        self._append_script(
            shell_cmd, self.config.pre_delete_script, "Pre-delete", inside_vm=False
        )

        # 2: delete VM
        shell_cmd.append(
            f"multipass delete {self.config.instance_name} && multipass purge"
        )

        # 3: Post-delete script
        self._append_script(
            shell_cmd, self.config.post_delete_script, "Post-delete", inside_vm=False
        )

        full_shell_command = (
            " && ".join(shell_cmd)
            + "; echo Press any key to close..."
            + "; stty -echo -icanon time 0 min 1; dd bs=1 count=1 >/dev/null 2>&1; stty sane"
        )
        terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
        subprocess.Popen(terminal_cmd, shell=True)

    def open_shell(self):
        subprocess.Popen(
            f"{terminal} -e multipass shell {self.config.instance_name}", shell=True
        )
