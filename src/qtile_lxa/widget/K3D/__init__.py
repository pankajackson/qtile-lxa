import subprocess
import threading
import json
import yaml
import tempfile
from pathlib import Path
from qtile_extras.widget import GenPollText, decorations
from libqtile.log_utils import logger
from libqtile.utils import guess_terminal
from typing import Any, Literal
from .typing import K3DConfig

terminal = guess_terminal()


class K3D(GenPollText):
    def __init__(self, config: K3DConfig, **kwargs: Any) -> None:
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
        super().__init__(func=self.get_text, **kwargs)

    def log_errors(self, msg):
        if self.config.enable_logger:
            logger.error(msg)

    def get_config(self):
        k3d_config = {
            "apiVersion": "k3d.io/v1alpha5",
            "kind": "Simple",
            "metadata": {"name": self.config.cluster_name},
        }

        if self.config.servers is not None:
            k3d_config["servers"] = self.config.servers
        if self.config.agents is not None:
            k3d_config["agents"] = self.config.agents
        if (
            self.config.kube_api_host
            or self.config.kube_api_host_ip
            or self.config.kube_api_host_port
        ):
            k3d_config["kubeAPI"] = {}
        if self.config.kube_api_host:
            k3d_config["kubeAPI"]["host"] = self.config.kube_api_host
        if self.config.kube_api_host_ip:
            k3d_config["kubeAPI"]["hostIP"] = self.config.kube_api_host_ip
        if self.config.kube_api_host_port:
            k3d_config["kubeAPI"]["hostPort"] = self.config.kube_api_host_port
        if self.config.network:
            k3d_config["network"] = self.config.network
        if self.config.volumes:
            k3d_config["volumes"] = [
                {"volume": f"{volume}:{self.config.volumes[volume]}"}
                for volume in self.config.volumes.keys()
            ]
        k3d_config["options"] = {}

        if (
            self.config.disable_traefik_ingress
            or self.config.disable_service_lb
            or self.config.disable_local_storage
        ):
            k3s_extra_args = []
            if self.config.disable_traefik_ingress:
                k3s_extra_args.append(
                    {"arg": "--disable=traefik", "nodeFilters": ["server:*"]}
                )
            if self.config.disable_service_lb:
                k3s_extra_args.append(
                    {"arg": "--disable=servicelb", "nodeFilters": ["server:*"]}
                )
            if self.config.disable_local_storage:
                k3s_extra_args.append(
                    {"arg": "--disable=local-storage", "nodeFilters": ["server:*"]}
                )
            k3d_config["options"]["k3s"] = {"extraArgs": k3s_extra_args}

        ulimits = [
            {
                "name": "nofile",
                "soft": 65535,
                "hard": 65535,
            },
        ]
        k3d_config["options"]["runtime"] = {}
        k3d_config["options"]["runtime"]["ulimits"] = ulimits
        if self.config.server_memory:
            k3d_config["options"]["runtime"][
                "serversMemory"
            ] = self.config.server_memory
        if self.config.agent_memory:
            k3d_config["options"]["runtime"]["agentsMemory"] = self.config.agent_memory
        if self.config.gpu_request is not None:
            k3d_config["options"]["runtime"]["gpuRequest"] = self.config.gpu_request

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        with open(temp_file.name, "w") as file:
            yaml.dump(k3d_config, file)
        self.log_errors(f"k3d config generated at: {temp_file.name}")
        return temp_file.name

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

    def fetch_cluster_details(self) -> dict[Any, Any] | None:
        try:
            cmd = ["k3d", "cluster", "list", "-o", "json"]
            output = self.run_command(cmd)
            cluster_list = json.loads(output or "[]")
            cluster_filtered = list(
                filter(lambda x: x["name"] == self.config.cluster_name, cluster_list)
            )
            if len(cluster_filtered) == 0:
                return {
                    "name": self.config.cluster_name,
                    "serversRunning": 0,
                    "serversCount": 0,
                    "agentsRunning": 0,
                    "agentsCount": 0,
                }
            else:
                return cluster_filtered[0]
        except Exception as e:
            self.log_errors(str(e))
            return None

    def check_cluster_status(
        self,
    ) -> Literal["running", "stopped", "warning", "unknown", "error"]:
        cluster = self.fetch_cluster_details()
        if cluster is not None:
            if cluster["serversCount"] == 0:
                return "unknown"
            else:
                if cluster["serversRunning"] == 0:
                    return "stopped"
                else:
                    if (cluster["serversCount"] > cluster["serversRunning"]) or (
                        cluster["agentsCount"] > cluster["agentsRunning"]
                    ):
                        return "warning"
                    else:
                        return "running"
        else:
            return "error"

    def get_text(self):
        symbol_map = {
            "stopped": self.config.stopped_symbol,
            "running": self.config.running_symbol,
            "warning": self.config.warning_symbol,
            "unknown": self.config.unknown_symbol,
            "error": self.config.error_symbol,
        }
        status = self.check_cluster_status()
        return self.format.format(
            symbol=symbol_map[status],
            label=self.config.label or self.config.cluster_name or "K3D Cluster",
        )

    def button_press(self, x, y, button):
        if button == 1:  # Left-click: Start the cluster
            self.run_in_thread(self.handle_start_cluster)
        elif button == 3:  # Right-click: Stop the cluster
            self.run_in_thread(self.handle_stop_cluster)
        elif button == 2:  # Middle-click: Restart the cluster
            self.run_in_thread(self.handle_remove_cluster)

    def handle_create_cluster(self):
        config_file = self.get_config()
        cmd = f"{terminal} -e k3d cluster create --config {config_file}"
        subprocess.Popen(cmd, shell=True)

    def handle_start_cluster(self):
        status = self.check_cluster_status()
        if status == "unknown":
            self.handle_create_cluster()
        elif status == "stopped":
            cmd = f"{terminal} -e k3d cluster start {self.config.cluster_name}"
            subprocess.Popen(cmd, shell=True)
        else:
            self.open_k9s()

    def handle_stop_cluster(self):
        cmd = f"{terminal} -e k3d cluster stop {self.config.cluster_name}"
        subprocess.Popen(cmd, shell=True)

    def handle_remove_cluster(self):
        cmd = f"{terminal} -e k3d cluster delete {self.config.cluster_name}"
        subprocess.Popen(cmd, shell=True)

    def open_k9s(self):
        try:
            command = [terminal, "-e", "k9s"]
            subprocess.Popen(command)
        except Exception as e:
            self._log_error(f"Failed to open k9s: {e}")
