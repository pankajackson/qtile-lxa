import subprocess
import threading
import json
import uuid
import yaml
from pathlib import Path
from qtile_extras.widget import GenPollText, decorations
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal
from typing import Any, Literal
from .typing import (
    MultipassVMConfig,
    MultipassScript,
    MultipassVMOnlyScript,
)
from qtile_lxa.utils.notification import send_notification

terminal = guess_terminal()


class MultipassVM(GenPollText):
    def __init__(
        self, config: MultipassVMConfig, vm_index: int | None = None, **kwargs: Any
    ) -> None:
        self.config = config
        self.vm_index = vm_index
        if self.vm_index is not None:
            self.config.instance_name = f"{self.config.instance_name}-{self.vm_index}"
            if self.config.label:
                self.config.label = f"{self.config.label}-{self.vm_index}"

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

    def check_vm_status(
        self,
    ) -> Literal[
        "not_created",
        "running",
        "stopped",
        "deleted",
        "starting",
        "restarting",
        "delayed_shutdown",
        "suspending",
        "suspended",
        "unknown",
        "error",
    ]:
        info = self.get_instance_info()
        if not info:
            return "not_created"
        state = info.get("state", "").lower()
        if state == "running":
            return "running"
        elif state == "stopped":
            return "stopped"
        elif state == "deleted":
            return "deleted"
        elif state == "starting":
            return "starting"
        elif state == "restarting":
            return "restarting"
        elif state == "delayed shutdown":
            return "delayed_shutdown"
        elif state == "suspending":
            return "suspending"
        elif state == "suspended":
            return "suspended"
        elif state == "unknown":
            return "unknown"
        else:
            return "error"

    def get_text(self):
        symbol_map = {
            "not_created": self.config.not_created_symbol,
            "running": self.config.running_symbol,
            "stopped": self.config.stopped_symbol,
            "deleted": self.config.deleted_symbol,
            "starting": self.config.starting_symbol,
            "restarting": self.config.restarting_symbol,
            "delayed_shutdown": self.config.delayed_shutdown_symbol,
            "suspending": self.config.suspending_symbol,
            "suspended": self.config.suspended_symbol,
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

    def _get_script_cmd(self, script: MultipassScript | MultipassVMOnlyScript):
        TMP_DIR = Path.home() / ".multipass_tmp"
        TMP_DIR.mkdir(exist_ok=True)
        if script.cmd:
            tmp_path = TMP_DIR / f"cmd_{uuid.uuid4().hex}.sh"
            tmp_path.write_text(f"#!/usr/bin/env bash\n{script.cmd}\n")
            tmp_path.chmod(0o755)
            if script.path:
                logger.warning(
                    f"`path` {script.path} will be ignored when `cmd` is specified"
                )
            script.path = tmp_path
        if not script.path:
            self.log(f"Script not found: {script.path}")
            return
        if not script.path.exists():
            self.log(f"Script not found: {script.path}")
            return

        if script.inside_vm:
            # Generate unique path inside VM
            remote_tmp_path = f"/tmp/{uuid.uuid4().hex}_{script.path.name}"

            # Transfer script into VM
            transfer_cmd = (
                f"multipass transfer {script.path} "
                f"{self.config.instance_name}:{remote_tmp_path}"
            )

            # Execute script in VM
            exec_cmd = (
                f"multipass exec {self.config.instance_name} -- "
                f"bash {remote_tmp_path} {' '.join(script.args)}"
            )

            # Optional cleanup command
            cleanup_cmd = (
                f"multipass exec {self.config.instance_name} -- rm {remote_tmp_path}"
            )

            # Return full chain of commands
            return f"{transfer_cmd} && {exec_cmd} && {cleanup_cmd}"

        else:
            # Run directly on host
            return f"bash {script.path} {' '.join(script.args)}"

    def _get_network_setup_cmd(self) -> str:
        if not self.config.network:
            self.log("No network config provided")
            return ""

        network = self.config.network
        adapter = network.adapter
        netplan_filename = f"99-lxa-{adapter}.yaml"
        netplan_path = f"/etc/netplan/{netplan_filename}"
        backup_path = f"{netplan_path}.bak"

        # Convert network dict to YAML
        netplan_dict = network.to_netplan_dict(self.vm_index)
        netplan_yaml = yaml.dump(netplan_dict, sort_keys=False)

        # Create temporary directory and files locally
        tmp_dir = Path.home() / ".cache/lxa_multipass_vm"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        netplan_tmp_file = tmp_dir / f"{uuid.uuid4().hex}_{netplan_filename}"
        script_file = tmp_dir / f"{uuid.uuid4().hex}_setup_netplan.sh"

        # Write netplan YAML to temporary file
        netplan_tmp_file.write_text(netplan_yaml, encoding="utf-8")

        # Generate shell script content
        script_content = (
            "#!/bin/bash\n"
            "set -e\n"
            f"echo 'Setting up network...'\n"
            f"# Backup existing netplan if exists\n"
            f"if [ -f {netplan_path} ]; then\n"
            f"    sudo cp {netplan_path} {backup_path}\n"
            f"    backup_exists=true\n"
            f"else\n"
            f"    backup_exists=false\n"
            f"fi\n"
            f"# Move temporary netplan into place\n"
            f"sudo mv /tmp/{netplan_tmp_file.name} {netplan_path}\n"
            f"# Ensure correct permissions\n"
            f"sudo chmod 600 {netplan_path}\n"
            f"# Apply netplan, restore backup if it fails and backup exists\n"
            f"if ! sudo netplan apply; then\n"
            f"    echo 'Netplan apply failed'\n"
            f'    if [ "$backup_exists" = true ]; then\n'
            f"        echo 'Restoring backup'\n"
            f"        sudo cp {backup_path} {netplan_path}\n"
            f"        sudo netplan apply\n"
            f"    else\n"
            f"        sudo mv {netplan_path} {netplan_path}.failed\n"
            f"        echo 'No backup exists, please fix `{netplan_path}.failed` manually'\n"
            f"        sudo netplan apply\n"
            f"    fi\n"
            f"fi\n"
        )

        # Write script to file and make executable
        script_file.write_text(script_content, encoding="utf-8")
        script_file.chmod(0o755)

        # Build command string: transfer netplan + transfer script + execute + cleanup
        cmd = (
            f"multipass transfer {netplan_tmp_file} {self.config.instance_name}:/tmp/{netplan_tmp_file.name} && "
            f"multipass transfer {script_file} {self.config.instance_name}:/tmp/{script_file.name} && "
            f"multipass exec {self.config.instance_name} -- bash /tmp/{script_file.name} && "
            f"multipass exec {self.config.instance_name} -- rm /tmp/{script_file.name}"
        )

        return cmd

    def _append_script(
        self, shell_cmd: list, script: MultipassScript | MultipassVMOnlyScript | None
    ):
        if script:
            cmd = self._get_script_cmd(script)
            if cmd:
                if script.ignore_errors:
                    cmd = f"({cmd}) || true"
                shell_cmd.append(cmd)
        return shell_cmd

    def _get_full_event_shell_cmd(
        self, event: Literal["launch", "start", "stop", "delete"]
    ):
        shell_cmd = []
        if event == "launch":
            # 0: Pre-launch script (host side)
            self._append_script(shell_cmd, self.config.pre_launch_script)

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
            if self.config.network:
                launch_cmd += ["--network", str(self.config.network.multipass_network)]
            if (
                self.config.cloud_init_path
                and Path(self.config.cloud_init_path).exists()
            ):
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

            # 3: Setup Network
            if self.config.network:
                shell_cmd.append(self._get_network_setup_cmd())

            # 4: Userdata script (inside VM)
            self._append_script(shell_cmd, self.config.userdata_script)

            # 5: Post-launch script (inside VM)
            self._append_script(shell_cmd, self.config.post_launch_script)

        elif event == "start":
            # 1: Pre-start script
            self._append_script(shell_cmd, self.config.pre_start_script)

            # 2: Start VM
            shell_cmd.append(f"multipass start {self.config.instance_name}")

            # 3: Post-start script
            self._append_script(shell_cmd, self.config.post_start_script)
        elif event == "stop":
            # 1: Pre-stop script
            self._append_script(shell_cmd, self.config.pre_stop_script)

            # 2: stop VM
            shell_cmd.append(f"multipass stop {self.config.instance_name} --force")

            # 3: Post-stop script
            self._append_script(shell_cmd, self.config.post_stop_script)

        elif event == "delete":
            # 1: Pre-delete script
            self._append_script(shell_cmd, self.config.pre_delete_script)

            # 2: delete VM
            shell_cmd.append(f"multipass delete --purge {self.config.instance_name}")

            # 3: Post-delete script
            self._append_script(shell_cmd, self.config.post_delete_script)

        # Run all chained
        full_shell_command = (
            " && ".join(shell_cmd)
            + "; echo Press any key to close..."
            + "; stty -echo -icanon time 0 min 1; dd bs=1 count=1 >/dev/null 2>&1; stty sane"
        )

        return full_shell_command

    def handle_launch_vm(self):
        full_shell_command = self._get_full_event_shell_cmd("launch")
        terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
        subprocess.Popen(terminal_cmd, shell=True)

    def handle_start_vm(self):
        status = self.check_vm_status()

        if status in ("not_created", "deleted"):
            self.handle_launch_vm()

        elif status in ["stopped", "suspended"]:
            # Start the VM normally
            full_shell_command = self._get_full_event_shell_cmd("start")
            terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
            subprocess.Popen(terminal_cmd, shell=True)

        elif status in ("running",):
            # Already running → just open shell
            self.open_shell()

        elif status in (
            "starting",
            "restarting",
            "delayed_shutdown",
            "suspending",
            "unknown",
        ):
            # VM is busy → maybe just log or notify user
            msg = f"VM is currently {status.replace('_', ' ')}. Please wait..."
            self.log(msg)
            send_notification(self.config.instance_name, msg)

        else:
            msg = f"Unhandled VM status: {status}"
            self.log(msg)
            send_notification(self.config.instance_name, msg)

    def handle_stop_vm(self):
        status = self.check_vm_status()

        if status in ("running", "delayed_shutdown", "suspended"):
            full_shell_command = self._get_full_event_shell_cmd("stop")
            terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
            subprocess.Popen(terminal_cmd, shell=True)

        elif status == "stopped":
            msg = "VM is already stopped."
            self.log(msg)
            send_notification(self.config.instance_name, msg)

        elif status in (
            "starting",
            "restarting",
            "suspending",
            "unknown",
        ):
            msg = f"VM is currently {status.replace('_', ' ')}. Please wait..."
            self.log(msg)
            send_notification(self.config.instance_name, msg)

        else:
            msg = f"Unhandled VM status: {status}"
            self.log(msg)
            send_notification(self.config.instance_name, msg)

    def handle_delete_vm(self):
        status = self.check_vm_status()

        if status in [
            "running",
            "starting",
            "restarting",
            "suspending",
            "stopped",
            "delayed_shutdown",
            "suspended",
            "deleted",
        ]:
            full_shell_command = self._get_full_event_shell_cmd("delete")
            terminal_cmd = f'{terminal} -e bash -c "{full_shell_command}"'
            subprocess.Popen(terminal_cmd, shell=True)
        elif status in ["not_created", "unknown"]:
            msg = f"VM is currently {status.replace('_', ' ')}. Cannot be deleted."
            self.log(msg)
            send_notification(self.config.instance_name, msg)
        else:
            msg = f"Unhandled VM status: {status}"
            self.log(msg)
            send_notification(self.config.instance_name, msg)

    def open_shell(self):
        subprocess.Popen(
            f"{terminal} -e multipass shell {self.config.instance_name}", shell=True
        )
