from dataclasses import dataclass, field
from typing import Literal


@dataclass
class SystemdUnitConfig:
    unit_name: str
    label: str | None = None
    bus_name: Literal["system", "user"] = "system"
    active_symbol: str = "🟢"
    inactive_symbol: str = "🔴"
    failed_symbol: str = "❌"
    activating_symbol: str = "⏳"
    deactivating_symbol: str = "🔄"
    unknown_symbol: str = "❓"
    status_symbol_first: bool = True
    markup: bool = False
