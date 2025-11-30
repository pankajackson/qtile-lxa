from io import StringIO
import csv
from pathlib import Path
from typing import Any
from qtile_lxa.utils.runner import Runner
from .typing import VagrantVMStatus


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

    def ssh_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant ssh {vm}")
