from dataclasses import dataclass
from pathlib import Path

@dataclass
class MultipassConfig:
    instance_name: str
    cloud_init_path: Path | None = None
    image: str = "22.04"
    cpus: int = 1
    memory: str = "1G"
    disk: str = "5G"
    label: str | None = None
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    enable_logger: bool = True
