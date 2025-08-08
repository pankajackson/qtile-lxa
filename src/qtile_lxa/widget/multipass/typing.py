from dataclasses import dataclass
from pathlib import Path


@dataclass
class MultipassSharedVolume:
    source_path: Path
    target_path: Path


@dataclass
class MultipassConfig:
    instance_name: str
    cloud_init_path: Path | None = None
    image: str | None = None
    cpus: int | None = None  # default 1
    memory: str | None = None  # default "1G"
    disk: str | None = None  # default "5G"
    shared_volumes: list[MultipassSharedVolume] | None = None
    label: str | None = None
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    enable_logger: bool = True
