import os, subprocess
import threading
import json
from qtile_extras.widget import GenPollText, decorations
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal
from pathlib import Path
from typing import Any
from .typing import DockerComposeConfig
from .network import get_docker_network

terminal = guess_terminal()


class DockerCompose(GenPollText):
    def __init__(
        self,
        config: DockerComposeConfig,
        **kwargs: Any,
    ):
        self.config = config
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
        self.format = "{symbol} {label}"
        if config.network is not None:
            get_docker_network(config.network)
        super().__init__(func=self.check_service_status, **kwargs)

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

    def run_in_thread(self, target, *args):
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()

    def fetch_service_details(self):
        try:
            cmd = [
                "docker-compose",
                "ls",
                "-a",
                "--format",
                "json",
            ]
            output = self.run_command(cmd)

            service_list = json.loads(output or "[]")
            service_filtered = list(
                filter(
                    lambda x: Path(x["ConfigFiles"]) == self.config.compose_file,
                    service_list,
                )
            )
            if len(service_filtered) == 0:
                return {
                    "Name": None,
                    "Status": None,
                    "ConfigFiles": self.config.compose_file,
                }
            else:
                return service_filtered[0]
        except Exception as e:
            self.log_errors(str(e))
            return {
                "Name": None,
                "Status": None,
                "ConfigFiles": self.config.compose_file,
            }

    def check_service_status(self):
        service = self.fetch_service_details()
        if service["Status"] is None:
            status_symbol = self.config.unknown_symbol
        elif "running" in str(service["Status"]) and "exited" in str(service["Status"]):
            status_symbol = self.config.partial_running_symbol
        elif "running" in str(service["Status"]):
            status_symbol = self.config.running_symbol
        elif "exited" in str(service["Status"]):
            status_symbol = self.config.stopped_symbol
        else:
            status_symbol = self.config.unknown_symbol
        return self.format.format(
            symbol=status_symbol, label=self.config.label or service["Name"] or "Docker"
        )

    def button_press(self, x, y, button):
        if button == 1:  # Left-click: Start the service
            self.run_in_thread(self.handle_start_service)
        elif button == 3:  # Right-click: Stop the service
            self.run_in_thread(self.handle_stop_service)
        elif button == 2:  # Middle-click: Restart the service
            self.run_in_thread(self.handle_remove_service)

    def handle_start_service(self):
        service = self.fetch_service_details()
        if service["Status"] is not None:
            if "running" in str(service["Status"]):
                cmd_logs = f"{terminal} -e docker-compose -f {self.config.compose_file} logs --follow"
                if self.config.service_name:
                    cmd_logs = f"{cmd_logs} {self.config.service_name}"
                subprocess.Popen(cmd_logs, shell=True)
                return

        cmd = f"{terminal} -e docker-compose -f {self.config.compose_file} up -d"
        if self.config.service_name:
            cmd = f"{cmd} {self.config.service_name}"

        env_vars = {}
        if self.config.network:
            env_vars["CONTAINER_NETWORK"] = self.config.network.name
        if self.config.ipaddress:
            env_vars["IPADDRESS"] = self.config.ipaddress

        env = os.environ.copy()
        env.update(env_vars)
        self.log_errors("Starting docker")
        subprocess.Popen(cmd, shell=True, env=env)

    def handle_stop_service(self):
        cmd = f"{terminal} -e docker-compose -f {self.config.compose_file} stop"

        if self.config.service_name:
            cmd = f"{cmd} {self.config.service_name}"
        subprocess.Popen(cmd, shell=True)

    def handle_remove_service(self):
        cmd = f"{terminal} -e docker-compose -f {self.config.compose_file} rm -s -f"

        if self.config.service_name:
            cmd = f"{cmd} {self.config.service_name}"
        subprocess.Popen(cmd, shell=True)
