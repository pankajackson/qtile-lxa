from pathlib import Path
from dataclasses import dataclass, field
import ipaddress
import docker
from docker.types import IPAMConfig, IPAMPool
from docker.models.networks import Network
from libqtile.log_utils import logger
from qtile_lxa import __DEFAULTS__


@dataclass
class DockerNetwork:
    name: str = field(default_factory=lambda: __DEFAULTS__.docker.network)
    subnet: str | None = None
    gateway: str | None = None
    create_if_not_found: bool = True

    # Internal attributes
    _network: ipaddress._BaseNetwork | None = field(
        default=None, init=False, repr=False
    )

    def _get_client(self):
        return docker.from_env()

    def resolve_network(self):
        if self._network is None:
            self._get_or_create_network()

    def _get_or_create_network(self) -> None:
        """Internal logic to get or create the network."""
        try:
            client = self._get_client()

            existing_networks: list[Network] = client.networks.list(names=[self.name])

            if existing_networks:
                cfg = existing_networks[0].attrs["IPAM"]["Config"][0]
                self.subnet = cfg.get("Subnet")
                self.gateway = cfg.get("Gateway")
                self._network = (
                    ipaddress.ip_network(self.subnet, strict=False)
                    if self.subnet
                    else None
                )
                logger.info(f"Docker network '{self.name}' already exists.")
                return

            if not self.create_if_not_found:
                logger.warning(
                    f"Docker network '{self.name}' not found and creation disabled."
                )
                self._network = None
                return

            if self.subnet is None:
                network = client.networks.create(
                    name=self.name,
                    driver="bridge",
                    ipam=None,  # DO NOT pass IPAM → Docker auto-assigns subnet
                )
                cfg = network.attrs["IPAM"]["Config"][0]
                self.subnet = cfg.get("Subnet")
                self.gateway = cfg.get("Gateway")
                if self.subnet is not None:
                    self._network = ipaddress.ip_network(self.subnet, strict=False)
                else:
                    self._network = None
                logger.info(
                    f"Docker network '{self.name}' created with auto subnet {self.subnet}"
                )
                return

            # NORMAL MODE (manual subnet)
            self._network = ipaddress.ip_network(self.subnet, strict=False)
            self.gateway = self.gateway or str(list(self._network.hosts())[0])

            ipam_pool = IPAMPool(subnet=self.subnet, gateway=self.gateway)
            ipam_config = IPAMConfig(pool_configs=[ipam_pool])

            client.networks.create(
                name=self.name,
                driver="bridge",
                ipam=ipam_config,
                options={"com.docker.network.bridge.enable_ip_masquerade": "true"},
            )

            logger.info(f"Docker network '{self.name}' created successfully.")

        except Exception as e:
            logger.error(f"Error during docker network setup: {e}")
            self._network = None

    @property
    def network(self) -> ipaddress._BaseNetwork | None:
        """Returns the IP network object for this Docker network."""
        return self._network


@dataclass
class DockerComposeConfig:
    compose_file: Path
    service_name: str | None = None
    network: DockerNetwork | None = field(
        default_factory=lambda: DockerNetwork(
            name=__DEFAULTS__.docker.network,
            subnet=__DEFAULTS__.docker.subnet,
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
