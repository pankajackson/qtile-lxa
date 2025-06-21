from dataclasses import dataclass
from pathlib import Path


@dataclass
class KubernetesConfig:
    label: str | None = None
    kubeconfig_path: Path = Path.home() / ".kube" / "config"
    show_all_status: bool = False
    logger_enabled: bool = False
    ready_symbol: str = "🟢"
    not_ready_symbol: str = "⚠️"
    error_symbol: str = "❌"
