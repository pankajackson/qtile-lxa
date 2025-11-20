from dataclasses import dataclass, field
from pathlib import Path
from qtile_lxa.widget.docker import DockerNetwork


@dataclass
class K3DConfig:
    cluster_name: str
    servers: int | None = None
    agents: int | None = None
    server_memory: str | None = None
    agent_memory: str | None = None
    gpu_request: str | None = None  # "all", "device=0", "1", etc.
    kube_api_host: str | None = None
    kube_api_host_ip: str | None = None
    kube_api_host_port: str | None = None
    network: DockerNetwork | None = field(default_factory=DockerNetwork)
    subnet: str | None = None
    volumes: dict[Path, Path] = field(
        default_factory=lambda: {Path.home() / "kube_storage": Path("/data/")}
    )
    disable_traefik_ingress: bool = False
    disable_service_lb: bool = False
    disable_local_storage: bool = False
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    warning_symbol: str = "⚠️"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    label: str | None = None
    enable_logger: bool = True
