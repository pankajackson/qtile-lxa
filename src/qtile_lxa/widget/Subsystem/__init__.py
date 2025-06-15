import subprocess
from qtile_extras.widget import GenPollText, decorations
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal
from typing import Any
from .typing import SubsystemConfig


terminal = guess_terminal()


def get_hostname():
    hostname = (
        subprocess.check_output(["hostnamectl hostname"], shell=True)
        .decode("utf-8")
        .strip()
    )
    return hostname


"""
Important Emoji
Kali Linux: 🐉 (Dragon emoji, since Kali's mascot is a dragon)
Fedora: 🎩 (Top hat emoji, representing Fedora's logo)
Arch Linux: 🔺 (Triangle emoji, resembles Arch's logo shape)
Linux Mint: 🍃 (Leaf emoji, symbolizing Mint's green logo)
Red Hat: 🎩 (Top hat emoji, as Red Hat's logo includes a hat)
CentOS: 🖥️ (Desktop computer emoji, general server OS representation)
Debian: 🌪️ (Whirlwind emoji, loosely resembling the swirl in Debian's logo)
Ubuntu: 🌍 (Globe emoji, representing global collaboration)
OpenSUSE: 🦎 (Lizard emoji, since OpenSUSE's logo features a chameleon)
Elementary OS: 💻 (Laptop emoji, representing its clean and user-friendly desktop environment)
Manjaro: 🟩 (Green square emoji, representing Manjaro's green branding)
Gentoo: 💎 (Gem emoji, symbolizing Gentoo's "geeky" reputation)
Alpine Linux: 🏔️ (Mountain emoji, relating to the name "Alpine")
"""


class Subsystem(GenPollText):
    def __init__(
        self,
        config: SubsystemConfig,
        **kwargs,
    ):
        self.config = config
        self.config.image = self.config.image or self.config.system_name
        self.config.label = self.config.label or self.config.system_name
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
        self.exists_cmd = [
            self.config.backend,
            "inspect",
            "--format",
            "{{.State.Status}}",
            self.config.system_name,
        ]
        self.status_cmd = [
            self.config.backend,
            "inspect",
            "--format",
            "{{.State.Running}}",
            self.config.system_name,
        ]
        self.enter_cmd = f"{terminal} -e distrobox enter {self.config.system_name}"
        self.stop_cmd = [
            "distrobox",
            "stop",
            "-Y",
            self.config.system_name,
        ]
        volume_args = " ".join(f"--volume {v}" for v in self.config.volumes or [])
        extra_packages_arg = " ".join(self.config.packages or [])
        self.create_cmd = (
            f"{terminal} -e distrobox create -Y -I "
            f"-n {self.config.system_name} "
            f"{volume_args} "
            f"-i {self.config.image} "
            f"-ap '{extra_packages_arg}' "
            f"--hostname {self.config.system_name}.{get_hostname()}"
        )
        self.destroy_cmd = [
            "distrobox",
            "rm",
            "-f",
            "-Y",
            self.config.system_name,
        ]
        self.format = "{symbol} {label}"
        super().__init__(func=self.check_container_status, **kwargs)

    def log_errors(self, msg):
        if self.config.enable_logger:
            logger.error(msg)

    def run_command(self, cmd):
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.SubprocessError as e:
            self.log_errors(f"Error running command: {cmd} - {str(e)}")
            return None

    def check_container_status(self):
        try:
            output = self.run_command(self.status_cmd)
            if output == "true":
                status_symbol = self.config.success_symbol
            elif output == "false":
                status_symbol = self.config.failure_symbol
            else:
                status_symbol = self.config.unknown_symbol
            return self.format.format(symbol=status_symbol, label=self.config.label)

        except Exception as e:
            self.log_errors(str(e))
            return self.format.format(
                symbol=self.config.error_symbol, label=self.config.system_name
            )

    def button_press(self, x, y, button):
        if button == 1:  # Left-click: Enter container if running, else create and enter
            self.handle_left_click()
        elif button == 3:  # Right-click: Stor container
            self.handle_right_click()
        elif button == 2:  # Middle-click: Destroy container
            self.handle_middle_click()

    def handle_left_click(self):
        exists = self.run_command(self.exists_cmd)
        self.log_errors(exists)
        if exists:
            self.log_errors("entering")
            subprocess.Popen(self.enter_cmd, shell=True)
        else:
            self.log_errors("creating and entering")
            subprocess.Popen(f"{self.create_cmd} && {self.enter_cmd}", shell=True)

    def handle_right_click(self):
        status = self.run_command(self.status_cmd)
        self.log_errors(status)
        if status == "true":
            self.log_errors("stoping")
            self.run_command(self.stop_cmd)

    def handle_middle_click(self):
        exists = self.run_command(self.exists_cmd)
        self.log_errors(exists)
        if exists:
            self.log_errors("deleting")
            self.run_command(self.destroy_cmd)
        else:
            self.log_errors("creating")
            subprocess.Popen(self.create_cmd, shell=True)
