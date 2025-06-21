from dataclasses import dataclass


@dataclass
class ElasticsearchMonitorConfig:
    username: str = "elastic"
    password: str = "changeme"
    endpoint: str = "http://localhost:9200"
    kibana_url: str | None = None
    timeout: int = 300
    ssl_ca: str | None = None
    verify_certs: bool = True
    green_health_symbol: str = "🟢"
    yellow_health_symbol: str = "🟡"
    red_health_symbol: str = "🔴"
    unknown_health_symbol: str = "❓"
    error_symbol: str = "❌"
    label: str | None = None
    enable_logger: bool = False

    def get_label(self, fallback: str = "ES") -> str:
        return self.label or fallback
