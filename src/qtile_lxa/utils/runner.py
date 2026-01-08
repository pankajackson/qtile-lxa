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

        # remaining kwargs are pure subprocess kwargs
        self.kwargs = kwargs

    def run(self, command: str):
        try:
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

        except Exception as e:
            logger.error(f"Error running command '{command}': {e}")
            return None

    def run_in_thread(self, target, *args):
        Thread(target=target, args=args, daemon=True).start()

    def run_in_terminal(self, cmd, wait: bool = True):
        if wait:
            cmd = (
                f'{terminal} -e bash -c "{cmd}; '
                "echo; echo Press any key to close...; "
                'read -n 1 -s -r"'
            )
        else:
            cmd = f'{terminal} -e bash -c "{cmd}"'

        subprocess.Popen(
            cmd,
            cwd=self.workdir,
            shell=True,
            env=self.env,
        )
