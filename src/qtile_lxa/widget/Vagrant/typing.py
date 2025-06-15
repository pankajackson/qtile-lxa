from dataclasses import dataclass


@dataclass
class VagrantConfig:
    vagrant_dir: str
    running_symbol: str = "🟢"
    partial_running_symbol: str = "🟡"
    poweroff_symbol: str = "🔴"
    stopped_symbol: str = "🛑"
    not_created_symbol: str = "⚪"
    aborted_symbol: str = "⚡"
    saved_symbol: str = "💤"
    frozen_symbol: str = "❄️"
    shutoff_symbol: str = "🔌"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    label: str | None = None
    detailed_status: bool = True
    enable_logger: bool = True
