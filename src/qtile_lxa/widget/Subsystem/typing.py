from dataclasses import dataclass, field
from pathlib import Path
from libqtile.utils import guess_terminal


@dataclass
class Volume:
    src: Path
    dest: Path
    mode: str = "rw"


@dataclass
class SubsystemConfig:
    system_name: str
    image: str | None = None
    backend: str = "podman"
    success_symbol: str = "🟢"
    failure_symbol: str = "🔴"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    format: str = "{symbol} {label}"
    terminal: str = field(default_factory=guess_terminal) or "xterm"
    volume_mount: str = "/opt/arch-provisioner:/opt/arch-provisioner:ro"
    packages: str = "git"
    label: str | None = None
    enable_logger: bool = True
