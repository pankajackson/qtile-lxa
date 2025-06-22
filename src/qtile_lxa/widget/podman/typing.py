from dataclasses import dataclass, field
from pathlib import Path
from qtile_lxa import __DEFAULTS__


@dataclass
class PodmanNetworkConfig:
    name: str = __DEFAULTS__.podman.network
    subnet: str = __DEFAULTS__.podman.subnet
    gateway: str | None = None


@dataclass
class PodmanComposeConfig:
    compose_file: Path
    service_name: str | None = None
    network: PodmanNetworkConfig | None = field(default_factory=PodmanNetworkConfig)
    ipaddress: str | None = None
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    partial_running_symbol: str = "⚠️"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    label: str | None = None
    enable_logger: bool = True

    def __post_init__(self):
        if self.label is None and self.service_name:
            self.label = self.service_name
