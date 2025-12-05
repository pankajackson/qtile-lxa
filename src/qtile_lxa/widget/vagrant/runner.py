from io import StringIO
import csv
import json
from pathlib import Path
from typing import Any

# from qtile_lxa.utils.runner import Runner
from .typing import VagrantVMStatus


from .process_locker import ConcurrencyLocker
import subprocess, os
from threading import Thread
from pathlib import Path
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger
from typing import Any


terminal = guess_terminal()


class Runner:
    def __init__(self, workdir: Path, **kwargs: Any):
        self.workdir = workdir
        self.env = os.environ.copy()
        self.env.update(kwargs.pop("env", {}) or {})
        self.kwargs = kwargs

    def _with_lock(self, locker_id, concurrency, block, func):
        locker = None

        if locker_id:
            if concurrency < 1:
                raise ValueError("concurrency must be >= 1")
            locker = ConcurrencyLocker(locker_id, concurrency)
            if not locker.acquire(block=block):
                return None

        try:
            return func()
        finally:
            if locker:
                locker.release()

    def run(
        self,
        command: str,
        locker_id: str | None = None,
        concurrency: int = 1,
        block=True,
    ):

        def _execute():
            result = subprocess.run(
                command,
                cwd=self.workdir,
                shell=True,
                text=True,
                capture_output=True,
                env=self.env,
                **self.kwargs,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            logger.error(f"Command failed ({command}):\n{result.stderr.strip()}")
            return None

        return self._with_lock(locker_id, concurrency, block, _execute)

    def run_in_thread(self, target, *args, locker_id=None, concurrency=1, block=False):

        def _thread_wrapper():
            def _execute():
                return target(*args)

            self._with_lock(locker_id, concurrency, block, _execute)

        Thread(target=_thread_wrapper, daemon=True).start()

    def run_in_terminal(
        self, cmd, wait: bool = True, locker_id=None, concurrency=1, block=False
    ):

        def _execute():
            if wait:
                full = (
                    f'{terminal} -e bash -c "{cmd}; '
                    "echo; echo Press any key to close...; "
                    'read -n 1 -s -r"'
                )
            else:
                full = f'{terminal} -e bash -c "{cmd}"'

            subprocess.Popen(
                full,
                cwd=self.workdir,
                shell=True,
                env=self.env,
            )

        return self._with_lock(locker_id, concurrency, block, _execute)


class VagrantCLI(Runner):
    def __init__(self, workdir: Path, **kwargs: Any):
        super().__init__(workdir, **kwargs)
        self.status_path = self.workdir / ".vm_status.json"

    def _save_status(self, data: list[dict]) -> None:
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

    def get_vm_list(self) -> list[VagrantVMStatus]:
        """
        1. Try reading live status with lock
        2. If lock blocks or vagrant fails -> fallback to JSON file
        3. If live read succeeds, update JSON file
        """

        output = self.run(
            "vagrant status --machine-readable",
            locker_id=f"{str(self.workdir)}-status",
            concurrency=1,
            block=True,
        )

        # If command failed or returned None → fallback to stored file
        if not output:
            logger.warning("Falling back to stored VM status (lock busy or error).")
            return self._load_status()

        # Normal parsing
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

        # Convert to dataclasses
        result: list[VagrantVMStatus] = []
        json_list: list[dict] = []

        for vm in vms.values():
            obj = VagrantVMStatus(
                name=vm["name"] or "",
                provider=vm["provider"] or "",
                state=vm["state"] or "",
                state_short=vm["state_short"] or "",
                state_long=vm["state_long"] or "",
            )
            result.append(obj)

            json_list.append(
                {
                    "name": obj.name,
                    "provider": obj.provider,
                    "state": obj.state,
                    "state_short": obj.state_short,
                    "state_long": obj.state_long,
                }
            )

        # Save successful status
        self._save_status(json_list)

        return result

    def get_vm(self, vm_name: str | None = None) -> VagrantVMStatus | None:
        vms = self.get_vm_list()
        if not vms:
            return None
        if vm_name:
            for vm in vms:
                if vm.name == vm_name:
                    return vm
            return None
        return vms[0]

    def start_vm(self, vm: str) -> None:
        self.run_in_terminal(
            cmd=f"vagrant up {vm}",
            locker_id=str(self.workdir),
            concurrency=1,
            block=False,
        )

    def stop_vm(self, vm: str) -> None:
        self.run_in_terminal(
            cmd=f"vagrant halt {vm}",
            locker_id=str(self.workdir),
            concurrency=1,
            block=False,
        )

    def destroy_vm(self, vm: str) -> None:
        self.run_in_terminal(
            cmd=f"vagrant destroy -f {vm}",
            locker_id=str(self.workdir),
            concurrency=1,
            block=False,
        )

    def ssh_vm(self, vm: str) -> None:
        self.run_in_terminal(
            cmd=f"vagrant ssh {vm}",
            locker_id=str(self.workdir),
            concurrency=1,
            block=False,
        )
