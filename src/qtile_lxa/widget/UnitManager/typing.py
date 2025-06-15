from dataclasses import dataclass


@dataclass
class UnitManagerConfig:
    unit_name: str
    label: str | None = None
    active_symbol: str = "🟢"
    inactive_symbol: str = "🔴"
    failed_symbol: str = "❌"
    activating_symbol: str = "⏳"
    deactivating_symbol: str = "🔄"
    unknown_symbol: str = "❓"
    status_symbol_first: bool = True
