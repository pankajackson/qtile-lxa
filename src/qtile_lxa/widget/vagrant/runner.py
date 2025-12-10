from io import StringIO
import csv, json
from pathlib import Path
from typing import Any
from libqtile.log_utils import logger
from qtile_lxa.utils.runner import Runner
from qtile_lxa.utils.process_lock import ProcessLocker
from qtile_lxa.utils.safe_filename import safe_filename, safe_filename_hash
from .typing import VagrantVMStatus


class VagrantCLI(Runner):
    def __init__(self, workdir: Path, **kwargs: Any):
        super().__init__(workdir, **kwargs)
        self.status_path = self.workdir / ".vm_status.json"

    def _save_status(self, vm_status: list[VagrantVMStatus]) -> None:
        data: list[dict[str, str]] = []
        for vm in vm_status:
            data.append(
                {
                    "name": vm.name,
                    "provider": vm.provider,
                    "state": vm.state,
                    "state_short": vm.state_short,
                    "state_long": vm.state_long,
                }
            )

        try:
            self.status_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed writing {self.status_path}: {e}")

    def _load_status(self) -> list[VagrantVMStatus]:
        if not self.status_path.exists():
            return []
        try:
            data = json.loads(self.status_path.read_text())
        except Exception as e:
            logger.error(f"Failed reading {self.status_path}: {e}")
            return []

        result = []
        for vm in data:
            result.append(
                VagrantVMStatus(
                    name=vm.get("name", ""),
                    provider=vm.get("provider", ""),
                    state=vm.get("state", ""),
                    state_short=vm.get("state_short", ""),
                    state_long=vm.get("state_long", ""),
                )
            )
        return result

    def _fetch_status(self) -> list[VagrantVMStatus]:
        output = self.run("vagrant status --machine-readable")
        if not output:
            return []

        vms: dict[str, dict[str, str | None]] = {}
        reader = csv.reader(StringIO(output))

        for row in reader:
            if len(row) < 4:
                continue

            _, machine, field, value = row[:4]

            if not machine:
                continue

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

            if field == "provider-name":
                vm["provider"] = value
            elif field == "state":
                vm["state"] = value
            elif field == "state-human-short":
                vm["state_short"] = value
            elif field == "state-human-long":
                vm["state_long"] = value.replace("\\n", "\n")
        result: list[VagrantVMStatus] = []
        for vm in vms.values():
            obj = VagrantVMStatus(
                name=vm["name"] or "",
                provider=vm["provider"] or "",
                state=vm["state"] or "",
                state_short=vm["state_short"] or "",
                state_long=vm["state_long"] or "",
            )
            result.append(obj)
        self.run_in_thread(self._save_status, result)
        return result

    def get_async_status(self) -> list[VagrantVMStatus]:
        lock = ProcessLocker(
            f"{safe_filename_hash(str(self.workdir))}-{safe_filename(str(self.workdir))}-status"
        )
        fd = lock.acquire_lock()

        if fd:
            # run fetch in background while lock is held
            def _update():
                try:
                    self._fetch_status()
                finally:
                    lock.release_lock(fd)

            self.run_in_thread(_update)

        # return cached immediately
        return self._load_status()

    def get_sync_status(self) -> list[VagrantVMStatus]:
        vms_status = self._fetch_status()
        return vms_status

    def get_vm(self, vm_name: str | None = None, sync: bool = False):
        vms_status = self.get_sync_status() if sync else self.get_async_status()

        if not vms_status:
            logger.warning("VM list is empty. Maybe Vagrant is down?")
            return None

        if vm_name is None:
            return vms_status[0]

        vm = next((x for x in vms_status if x.name == vm_name), None)

        if vm is None:
            logger.warning(f"VM '{vm_name}' not found.")

        return vm

    def start_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant up {vm}")

    def stop_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant halt {vm}")

    def destroy_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant destroy -f {vm}")

    def ssh_vm(self, vm: str) -> None:
        self.run_in_terminal(cmd=f"vagrant ssh {vm}")
