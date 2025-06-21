import subprocess
from kubernetes import client, config
from libqtile.log_utils import logger
from qtile_extras.widget import GenPollText
from urllib3.exceptions import HTTPError
from libqtile.utils import guess_terminal
from pathlib import Path
from typing import Any
from .typing import KubernetesConfig

terminal = guess_terminal()


class Kubernetes(GenPollText):
    def __init__(
        self,
        config: KubernetesConfig = KubernetesConfig(),
        **kwargs: Any,
    ):
        self.config = config
        self.format = "{symbol} {label} : {status}"
        super().__init__(func=self.check_cluster_status, **kwargs)

    def _initialize_k8s_client(self, kubeconfig_path: Path):
        try:
            (
                config.load_kube_config(config_file=str(kubeconfig_path))
                if kubeconfig_path
                else config.load_kube_config()
            )
            return client.CoreV1Api()
        except Exception as e:
            self._log_error(f"Error loading kube config: {e}")
            return None

    def _log_error(self, msg):
        if self.config.logger_enabled:
            logger.error(msg)

    def _get_default_label(self, kubeconfig_path: Path):
        try:
            contexts = config.list_kube_config_contexts(
                config_file=str(kubeconfig_path)
            )
            context = contexts[1].get("context", {}).get("cluster")
            return context if context else self.config.label
        except Exception as e:
            self._log_error(f"Error fetching default Kubernetes context: {e}")
            return self.config.label

    def _get_status(self):
        try:
            k8s_api = self._initialize_k8s_client(self.config.kubeconfig_path)
            if not k8s_api:
                return "No API", self.config.error_symbol
            nodes = k8s_api.list_node(timeout_seconds=2)
            if not nodes.items:
                return "No Nodes", self.config.error_symbol

            ready_node_count = sum(
                1
                for node in nodes.items
                if any(
                    cond.type == "Ready" and cond.status == "True"
                    for cond in node.status.conditions
                )
            )
            not_ready_node_count = len(nodes.items) - ready_node_count

            if not_ready_node_count > 0:
                return (
                    f"{not_ready_node_count}/{len(nodes.items)} Node(s) Not Ready",
                    self.config.not_ready_symbol,
                )
            return "Ready", self.config.ready_symbol
        except HTTPError as e:
            self._log_error(f"Failed to connect to Kubernetes API server: {e}")
            return "Unreachable", self.config.error_symbol
        except Exception as e:
            self._log_error(f"Error fetching cluster status: {e}")
            return "Error", self.config.error_symbol

    def _get_format(self, kube_status):
        if self.config.show_all_status or kube_status not in [
            "Ready",
            "Unreachable",
            "Error",
            "No API",
            "No Nodes",
        ]:
            return self.format
        return self.format.removesuffix(" : {status}")

    def check_cluster_status(self):
        status, symbol = self._get_status()
        kube_context = self._get_default_label(self.config.kubeconfig_path)
        label = self.config.label or kube_context or "K8S"
        format_str = self._get_format(status)

        return format_str.format(label=label, status=status, symbol=symbol)

    def button_press(self, x, y, button):
        if button == 1:  # Left-click: Start the cluster
            self.open_k9s()

    def open_k9s(self):
        try:
            command = (
                [terminal, "-e", "k9s", "--kubeconfig", self.config.kubeconfig_path]
                if self.config.kubeconfig_path
                else [terminal, "-e", "k9s"]
            )
            subprocess.Popen(command)
        except Exception as e:
            self._log_error(f"Failed to open k9s: {e}")
