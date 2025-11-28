from dataclasses import dataclass
import subprocess
from io import StringIO
import threading
import csv
from pathlib import Path
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger
from typing import Any


terminal = guess_terminal()


class Runner:
    def __init__(self, workdir: Path, **kwargs: Any):
        self.workdir = workdir
        self.kwargs = kwargs

    def run(self, command: str):
        try:
            result = subprocess.run(
                command,
                cwd=self.workdir,
                shell=True,
                text=True,
                capture_output=True,
                **self.kwargs,
            )
            if result.returncode == 0:
                return result.stdout.strip()

            logger.error(f"Command failed ({command}):\n{result.stderr.strip()}")
            return None

        except Exception as e:
            logger.error(f"Error running command '{command}': {e}")
            return None

    def run_in_thread(self, target, *args):
        t = threading.Thread(target=target, args=args, daemon=True)
        t.start()

    def run_in_terminal(self, cmd, wait: bool = True):
        if wait:
            cmd = (
                f'{terminal} -e bash -c "{cmd}; '
                "echo; echo Press any key to close...; "
                'read -n 1 -s -r"'
            )
        else:
            cmd = f'{terminal} -e bash -c "{cmd};'
        subprocess.Popen(
            cmd,
            cwd=self.workdir,
            shell=True,
        )


@dataclass
class VagrantVMStatus:
    name: str
    provider: str
    state: str
    state_short: str
    state_long: str


class VagrantCLI(Runner):
    def __init__(self, workdir: Path, **kwargs: Any):
        super().__init__(workdir, **kwargs)

    def get_vm_list(self) -> list[VagrantVMStatus]:
        output = self.run("vagrant status --machine-readable")
        if not output:
            return []

        vms: dict[str, dict[str, str | None]] = {}
        reader = csv.reader(StringIO(output))

        for row in reader:
            if len(row) < 4:
                continue

            _, machine, field, value = row[:4]

            # Skip summary lines
            if not machine:
                continue

            # Initialize vm entry if not exists
            vm = vms.setdefault(
                machine,
                {
                    "name": machine,
                    "provider": None,
                    "state": None,
                    "state_short": None,
                    "state_long": None,
                },
            )

            # Populate fields
            if field == "provider-name":
                vm["provider"] = value
            elif field == "state":
                vm["state"] = value
            elif field == "state-human-short":
                vm["state_short"] = value
            elif field == "state-human-long":
                vm["state_long"] = value.replace("\\n", "\n")

        # Convert dictionary → dataclass objects
        result: list[VagrantVMStatus] = []
        for vm in vms.values():
            result.append(
                VagrantVMStatus(
                    name=vm["name"] or "",
                    provider=vm["provider"] or "",
                    state=vm["state"] or "",
                    state_short=vm["state_short"] or "",
                    state_long=vm["state_long"] or "",
                )
            )

        return result

    def get_vm(self, vm_name: str | None = None) -> VagrantVMStatus | None:
        vms = self.get_vm_list()
        if not vms:
            return None
        if vm_name:
            filtered_list = [vm for vm in vms if vm.name == vm_name]
            if len(filtered_list) == 0:
                return None
            return filtered_list[0]
        return vms[0]

    def start_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant up {vm}")

    def stop_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant halt {vm}")

    def destroy_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant destroy -f {vm}")
