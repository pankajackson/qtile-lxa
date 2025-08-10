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
    userdata_script: Path | None = None
    pre_launch_script: Path | None = None
    post_launch_script: Path | None = None
    pre_start_script: Path | None = None
    post_start_script: Path | None = None
    pre_stop_script: Path | None = None
    post_stop_script: Path | None = None
    pre_delete_script: Path | None = None
    post_delete_script: Path | None = None
    label: str | None = None
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    enable_logger: bool = False
