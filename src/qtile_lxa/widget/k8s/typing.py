from dataclasses import dataclass, field
import ipaddress
from pathlib import Path
import secrets
from typing import Literal
from libqtile.log_utils import logger
from qtile_lxa.widget.multipass import MultipassNetwork
from qtile_lxa.widget.vagrant import VagrantNetwork


# TODO: Deprecated: Please remove K8sNetwork class. Use Platform specific Network instead.
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
    adapter: str = "ens4"  # Adapter name inside the VM, e.g., "eth0"

    def get_ip(self, index: int) -> str:
        """Return an IP address incremented by index from the start_ip with CIDR suffix."""
        net = ipaddress.ip_network(self.subnet, strict=False)
        base_ip = list(net.hosts())[self.start_ip - 1]
        return f"{ipaddress.ip_address(base_ip) + index}/{net.prefixlen}"

    def master_ip(self) -> str:
        """Return the master node IP (first IP in the range)."""
        return self.get_ip(0)

    def agent_ips(self, count: int) -> list[str]:
        """Return a list of agent node IPs starting after the master IP."""
        return [self.get_ip(i + 1) for i in range(count)]


@dataclass
class K8SConfig:
    cluster_name: str
    platform: Literal["multipass", "virtualbox", "libvirt"]
    master_cpus: int | None = None  # default 1
    master_memory: str | None = None  # default "1G"
    master_disk: str | None = None  # default "5G"
    master_image: str | None = None  # virtualbox: bento/ubuntu-22.04, multipass: 22.04
    master_network: MultipassNetwork | VagrantNetwork | None = None
    agent_cpus: int | None = None  # default 1
    agent_memory: str | None = None  # default "1G"
    agent_disk: str | None = None  # default "5G"
    agent_count: int = 1  # Number of agent nodes
    agent_image: str | None = None  # virtualbox: bento/ubuntu-22.04, multipass: 22.04
    agent_network: MultipassNetwork | VagrantNetwork | None = None
    data_dir: Path | None = None
    extra_packages: list[str] = field(default_factory=list)
    tls_san: list[str] = field(
        default_factory=list
    )  # e.g., ["kube.linuxastra.in", "kube.lxa.com, kube.linuxastra.in:443"]

    # K3s install options
    # check available version using `curl -sL https://api.github.com/repos/k3s-io/k3s/releases | jq -r '.[].tag_name'`
    k3s_version: str | None = None  # "v1.28.4+k3s1"
    k3s_token: str | None = None  # Shared secret between master and agents

    # Feature toggles
    disable_traefik_ingress: bool = False
    disable_local_storage: bool = False
    disable_metrics_server: bool = False

    # Labels & Taints
    labels: list[str] = field(default_factory=list)
    taints: list[str] = field(
        default_factory=list
    )  # e.g., ["node-role.kubernetes.io/master=true:NoSchedule"]

    # Logs & Debug
    enable_logger: bool = True

    # Worker only configs
    worker_only: bool = False
    master_address: str | None = None  # eg "192.168.1.10"
    kubeconfig_path: Path | None = None

    update_interval: int = 10

    # WidgetBoxConfig
    widgetbox_close_button_location: Literal["left", "right"] = "left"
    widgetbox_text_closed: str = " 󱃾 "
    widgetbox_text_open: str = "󱃾  "
    widgetbox_timeout: int = 5

    def __post_init__(self):
        if self.worker_only:
            if not self.master_address:
                raise ValueError("Must specify master address when worker_only is True")
            if not self.k3s_token:
                raise ValueError("Must specify k3s token when worker_only is True")
            if not self.kubeconfig_path:
                logger.warning(
                    "⚠️  WARNING: worker_only=True but kubeconfig_path is not provided.\n"
                    "    → Worker will run normally, but cluster actions requiring kubectl will NOT work on this node.\n"
                    "    Affected features:\n"
                    "      - Applying labels to this worker\n"
                    "      - 'delete node' operation before deleting VM",
                )
        if not self.k3s_token:
            self.k3s_token = secrets.token_hex(16)

        if self.master_network:
            if self.platform == "multipass" and not isinstance(
                self.master_network, MultipassNetwork
            ):
                raise ValueError("master_network must be a MultipassNetwork instance")
            elif self.platform == "libvirt" and not isinstance(
                self.master_network, VagrantNetwork
            ):
                raise ValueError("master_network must be a VagrantNetwork instance")
            elif self.platform == "virtualbox" and not isinstance(
                self.master_network, VagrantNetwork
            ):
                raise ValueError("master_network must be a VagrantNetwork instance")

        if self.agent_network:
            if self.platform == "multipass" and not isinstance(
                self.agent_network, MultipassNetwork
            ):
                raise ValueError("agent_network must be a MultipassNetwork instance")
            elif self.platform == "libvirt" and not isinstance(
                self.agent_network, VagrantNetwork
            ):
                raise ValueError("agent_network must be a VagrantNetwork instance")
            elif self.platform == "virtualbox" and not isinstance(
                self.agent_network, VagrantNetwork
            ):
                raise ValueError("agent_network must be a VagrantNetwork instance")

        # Validate size
        def validate_size(size: str):
            s = size.lower().strip()
            if not s.endswith(("gb", "g", "mb", "m", "tb", "t")):
                raise ValueError(
                    "Disk size must be like '10GB', '10G', '500MB','500M',  '1TB',  '1T'."
                )
            return s

        if self.master_disk:
            self.master_disk_size_mb = validate_size(self.master_disk)
        if self.agent_disk:
            self.agent_disk_size_mb = validate_size(self.agent_disk)
        if self.master_memory:
            self.master_memory_mb = validate_size(self.master_memory)
        if self.agent_memory:
            self.agent_memory_mb = validate_size(self.agent_memory)
