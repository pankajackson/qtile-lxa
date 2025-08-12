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
    network: str | None = None
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
