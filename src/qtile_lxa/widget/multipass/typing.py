from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MultipassNetwork:
    multipass_network: str  # Network name from `multipass networks`
    adapter: str = "ens4"  # Interface name inside the VM
    dhcp4: bool = True  # Enable DHCP for IPv4 by default
    addresses: list[str] = field(
        default_factory=list
    )  # Static IPs, e.g., ["192.168.100.31/24"]
    gateway4: str | None = None  # Default gateway
    nameservers: list[str] = field(
        default_factory=lambda: ["8.8.8.8", "8.8.4.4"]
    )  # DNS servers
    mtu: int | None = 1500  # Optional MTU
    routes: list[dict] = field(default_factory=list)  # Optional static routes

    def to_netplan_dict(self) -> dict:
        """Convert this network config into netplan YAML dict format."""
        dhcp_enabled = self.dhcp4 and not (
            self.addresses or self.routes or self.gateway4
        )

        net = {
            "network": {
                "version": 2,
                "ethernets": {
                    self.adapter: {
                        "dhcp4": dhcp_enabled,
                    }
                },
            }
        }

        eth = net["network"]["ethernets"][self.adapter]

        if self.addresses:
            eth["addresses"] = self.addresses

        if self.nameservers:
            eth["nameservers"] = {"addresses": self.nameservers}

        if self.mtu:
            eth["mtu"] = self.mtu

        if self.routes:
            eth["routes"] = self.routes
        elif self.gateway4:
            eth["routes"] = [{"to": "0.0.0.0/0", "via": self.gateway4}]

        return net


@dataclass
class MultipassSharedVolume:
    source_path: Path
    target_path: Path


@dataclass
class MultipassScript:
    path: Path
    args: list[str] = field(default_factory=list)
    inside_vm: bool = False
    ignore_errors: bool = False

    def __post_init__(self):
        if not isinstance(self.path, Path):
            raise TypeError(f"path must be a Path, got {type(self.path).__name__}")


class MultipassVMOnlyScript(MultipassScript):
    def __init__(
        self, path: Path, args: list[str] | None = None, ignore_errors: bool = False
    ):
        super().__init__(
            path=path, args=args or [], inside_vm=True, ignore_errors=ignore_errors
        )


@dataclass(frozen=True)
class MultipassConfig:
    instance_name: str
    cloud_init_path: Path | None = None
    image: str | None = None
    cpus: int | None = None  # default 1
    memory: str | None = None  # default "1G"
    disk: str | None = None  # default "5G"
    network: MultipassNetwork | None = None
    shared_volumes: list[MultipassSharedVolume] = field(default_factory=list)
    userdata_script: MultipassVMOnlyScript | None = None
    pre_launch_script: MultipassScript | None = None
    post_launch_script: MultipassScript | None = None
    pre_start_script: MultipassScript | None = None
    post_start_script: MultipassScript | None = None
    pre_stop_script: MultipassScript | None = None
    post_stop_script: MultipassScript | None = None
    pre_delete_script: MultipassScript | None = None
    post_delete_script: MultipassScript | None = None
    label: str | None = None
    not_created_symbol: str = "⚪"
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    deleted_symbol: str = "🗑️"
    starting_symbol: str = "🟡"
    restarting_symbol: str = "🔄"
    delayed_shutdown_symbol: str = "🛑"
    suspending_symbol: str = "⏱️"
    suspended_symbol: str = "❄️"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    enable_logger: bool = False
