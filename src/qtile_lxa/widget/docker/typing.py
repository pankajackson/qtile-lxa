from dataclasses import dataclass, field
from pathlib import Path
from qtile_lxa import __DEFAULTS__


@dataclass
class DockerNetworkConfig:
    name: str = __DEFAULTS__.docker.network
    subnet: str = __DEFAULTS__.docker.subnet
    gateway: str | None = None


@dataclass
class DockerComposeConfig:
    compose_file: Path
    service_name: str | None = None
    network: DockerNetworkConfig | None = field(default_factory=DockerNetworkConfig)
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
