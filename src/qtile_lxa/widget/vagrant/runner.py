from io import StringIO
import csv
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

    def get_vm_list(self) -> list[VagrantVMStatus]:
        output = self.run(
            "vagrant status --machine-readable",
            locker_id=f"{str(self.workdir)}-status",
            concurrency=1,
            block=True,
        )
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
