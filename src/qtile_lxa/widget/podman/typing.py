from pathlib import Path
from dataclasses import dataclass, field
import ipaddress
import podman
from podman.errors import NotFound
from podman.domain.networks import Network
from libqtile.log_utils import logger
from qtile_lxa import __DEFAULTS__


@dataclass
class PodmanNetwork:
    name: str = field(default_factory=lambda: __DEFAULTS__.podman.network)
    subnet: str | None = None
    gateway: str | None = None
    create_if_not_found: bool = True

    # Internal attributes
    _network: ipaddress._BaseNetwork | None = field(
        default=None, init=False, repr=False
    )
    _client: podman.PodmanClient = field(
        default_factory=lambda: podman.PodmanClient(
            # base_url="unix:/run/podman/podman.sock"
        ),
        init=False,
        repr=False,
    )

    def resolve_network(self):
        if self._network is None:
            self._get_or_create_network()

    def _get_or_create_network(self) -> None:
        try:
            # Try to get the network if it exists
            try:
                existing = self._client.networks.get(self.name)
                cfg = existing.attrs.get("subnets", [{}])[0]

                self.subnet = cfg.get("subnet", self.subnet)
                self.gateway = cfg.get("gateway", self.gateway)

                self._network = (
                    ipaddress.ip_network(self.subnet, strict=False)
                    if self.subnet
                    else None
                )

                logger.info(f"Podman network '{self.name}' already exists.")
                return

            except NotFound:
                if not self.create_if_not_found:
                    logger.warning(
                        f"Podman network '{self.name}' not found and creation disabled."
                    )
                    self._network = None
                    return

            # -----------------------
            #  CREATE NEW NETWORK
            # -----------------------
            if self.subnet is None:
                # Auto IPAM mode
                network = self._client.networks.create(
                    name=self.name,
                    driver="bridge",
                )

                cfg = network.attrs.get("subnets", [{}])[0]
                self.subnet = cfg.get("subnet")
                self.gateway = cfg.get("gateway")

                self._network = (
                    ipaddress.ip_network(self.subnet, strict=False)
                    if self.subnet
                    else None
                )

                logger.info(
                    f"Podman network '{self.name}' created with auto subnet {self.subnet}"
                )
                return

            # Manual IPAM mode
            self._network = ipaddress.ip_network(self.subnet, strict=False)
            self.gateway = self.gateway or str(list(self._network.hosts())[0])

            self._client.networks.create(
                name=self.name,
                driver="bridge",
                subnets=[{"subnet": self.subnet, "gateway": self.gateway}],
            )

            logger.info(f"Podman network '{self.name}' created successfully.")

        except Exception as e:
            logger.error(f"Error during podman network setup: {e}")
            self._network = None

    @property
    def network(self) -> ipaddress._BaseNetwork | None:
        return self._network


@dataclass
class PodmanComposeConfig:
    compose_file: Path
    service_name: str | None = None

    network: PodmanNetwork | None = field(
        default_factory=lambda: PodmanNetwork(
            name=__DEFAULTS__.podman.network,
            subnet=__DEFAULTS__.podman.subnet,
        )
    )

    ipaddress: str | None = None
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    partial_running_symbol: str = "⚠️"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    label: str | None = None
    enable_logger: bool = True

    def __post_init__(self):
        if self.label is None and self.service_name:
            self.label = self.service_name
