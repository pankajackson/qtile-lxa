from dataclasses import dataclass, field
from pathlib import Path
import secrets
from qtile_lxa.widget.multipass import MultipassConfig
from typing import Literal


@dataclass
class K8SConfig:
    cluster_name: str
    master_cpus: int | None = None  # default 1
    master_memory: str | None = None  # default "1G"
    master_disk: str | None = None  # default "5G"
    agent_cpus: int | None = None  # default 1
    agent_memory: str | None = None  # default "1G"
    agent_disk: str | None = None  # default "5G"
    agent_count: int = 1  # Number of agent nodes
    data_dir: Path | None = None
    network: str | None = None

    # Server
    extra_packages: list[str] = field(default_factory=list)

    # K3s install options
    k3s_version: str | None = None  # "v1.28.4+k3s1"
    token: str | None = None  # Shared secret between master and agents

    # Feature toggles
    disable_traefik_ingress: bool = False
    disable_local_storage: bool = False
    disable_metrics_server: bool = False

    # Labels & Taints
    label: str | None = None
    taints: list[str] = field(
        default_factory=list
    )  # e.g., ["node-role.kubernetes.io/master=true:NoSchedule"]

    # Logs & Debug
    enable_logger: bool = True

    # WidgetBoxConfig
    widgetbox_close_button_location: Literal["left", "right"] = "left"
    widgetbox_text_closed: str = " 󱃾 "
    widgetbox_text_open: str = "󱃾  "
    widgetbox_timeout: int = 5

    def __post_init__(self):
        if not self.token:
            self.token = secrets.token_hex(16)
