from dataclasses import dataclass
from pathlib import Path


@dataclass
class DockerComposeConfig:
    compose_file: Path
    service_name: str | None = None
    network: str | None = None
    ipaddress: str | None = None
    running_symbol: str = "✅"
    stopped_symbol: str = "❌"
    partial_running_symbol: str = "⚠️"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    label: str | None = None
    enable_logger: bool = True

    def __post_init__(self):
        if self.label is None and self.service_name:
            self.label = self.service_name
