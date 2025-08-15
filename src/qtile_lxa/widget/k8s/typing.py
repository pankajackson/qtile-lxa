from dataclasses import dataclass, field
import ipaddress
from pathlib import Path
import secrets
from qtile_lxa.widget.multipass import MultipassConfig
from typing import Literal


@dataclass
class K8sNetwork:
    """
    Configuration for a Kubernetes network inside Multipass.

    Attributes:
        network: Name of the Multipass network (from `multipass networks`).
        adapter: Network adapter name inside the VM, e.g., "br0".
        subnet: Subnet in CIDR notation, e.g., "192.168.0.0/24".
        start_ip: Starting IP offset (1-based) to allocate addresses within the subnet.

    Example:
        k8s_net = K8sNetwork(
            network="lxa-net",
            adapter="br0",
            subnet="192.168.0.0/24",
            start_ip=30
        )
        k8s_net.master_ip()  # returns "192.168.0.30"
        k8s_net.agent_ips(3)  # returns ["192.168.0.31", "192.168.0.32", "192.168.0.33"]
    """

    network: str  # Network name from `multipass networks`
    subnet: str  # e.g., "192.168.0.0/24"
    start_ip: int  # e.g., 30
    adapter: str | None = None  # e.g., "br0"

    def get_ip(self, index: int) -> str:
        """Return an IP address incremented by index from the start_ip."""
        net = ipaddress.ip_network(self.subnet, strict=False)
        base_ip = list(net.hosts())[self.start_ip - 1]  # start_ip is 1-based
        return str(ipaddress.ip_address(base_ip) + index)

    def master_ip(self) -> str:
        """Return the master node IP (first IP in the range)."""
        return self.get_ip(0)

    def agent_ips(self, count: int) -> list[str]:
        """Return a list of agent node IPs starting after the master IP."""
        return [self.get_ip(i + 1) for i in range(count)]


@dataclass
class K8SConfig:
    cluster_name: str
    master_cpus: int | None = None  # default 1
    master_memory: str | None = None  # default "1G"
    master_disk: str | None = None  # default "5G"
    agent_cpus: int | None = None  # default 1
    agent_memory: str | None = None  # default "1G"
    agent_disk: str | None = None  # default "5G"
    agent_count: int = 1  # Number of agent nodes
    data_dir: Path | None = None
    network: K8sNetwork | None = None
    extra_packages: list[str] = field(default_factory=list)

    # K3s install options
    k3s_version: str | None = None  # "v1.28.4+k3s1"
    token: str | None = None  # Shared secret between master and agents

    # Feature toggles
    disable_traefik_ingress: bool = False
    disable_local_storage: bool = False
    disable_metrics_server: bool = False

    # Labels & Taints
    label: str | None = None
    taints: list[str] = field(
        default_factory=list
    )  # e.g., ["node-role.kubernetes.io/master=true:NoSchedule"]

    # Logs & Debug
    enable_logger: bool = True

    # WidgetBoxConfig
    widgetbox_close_button_location: Literal["left", "right"] = "left"
    widgetbox_text_closed: str = " 󱃾 "
    widgetbox_text_open: str = "󱃾  "
    widgetbox_timeout: int = 5

    def __post_init__(self):
        if not self.token:
            self.token = secrets.token_hex(16)
