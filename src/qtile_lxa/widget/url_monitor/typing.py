from dataclasses import dataclass


@dataclass
class URLMonitorConfig:
    url: str
    schema: str = "https"
    cert_verify: bool = True
    timeout: int = 5
    success_symbol: str = "🟢"
    failure_symbol: str = "🔴"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    label: str | None = None
    enable_logger: bool = False
