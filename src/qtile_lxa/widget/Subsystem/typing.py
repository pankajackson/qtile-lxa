from dataclasses import dataclass, field
from libqtile.utils import guess_terminal


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
    volumes: list[str] | None = None
    packages: list[str] = field(default_factory=lambda: ["git"])
    label: str | None = None
    enable_logger: bool = True
