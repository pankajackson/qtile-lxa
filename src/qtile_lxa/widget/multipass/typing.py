from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MultipassSharedVolume:
    source_path: Path
    target_path: Path


@dataclass
class MultipassScript:
    path: Path
    args: list[str] = field(default_factory=list)
    inside_vm: bool = False


class MultipassVMOnlyScript(MultipassScript):
    def __init__(self, path: Path, args: list[str] | None = None):
        super().__init__(path=path, args=args or [], inside_vm=True)


@dataclass
class MultipassConfig:
    instance_name: str
    cloud_init_path: Path | None = None
    image: str | None = None
    cpus: int | None = None  # default 1
    memory: str | None = None  # default "1G"
    disk: str | None = None  # default "5G"
    shared_volumes: list[MultipassSharedVolume] | None = None
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
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    enable_logger: bool = False
