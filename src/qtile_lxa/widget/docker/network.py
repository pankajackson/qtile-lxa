import ipaddress
import docker
from libqtile.log_utils import logger
from docker.types import IPAMConfig, IPAMPool
from qtile_lxa import __DEFAULTS__
from .typing import DockerNetworkConfig


def get_docker_network(network_config: DockerNetworkConfig):
    name = network_config.name
    subnet = network_config.subnet
    gateway = network_config.gateway
    try:
        client = docker.from_env()
        existing_network = client.networks.list(names=[name])
        if existing_network:
            network = ipaddress.ip_network(
                existing_network[0].attrs["IPAM"]["Config"][0]["Subnet"],
                strict=False,
            )
            logger.info(f"Docker network '{name}' already exists.")
            return name, network
        else:
            network = ipaddress.ip_network(subnet, strict=False)
            gateway = str(list(network.hosts())[0]) if gateway is None else gateway
            ipam_pool = IPAMPool(subnet=subnet, gateway=gateway)
            ipam_config = IPAMConfig(pool_configs=[ipam_pool])
            client.networks.create(
                name=name,
                driver="bridge",
                ipam=ipam_config,
                options={"com.docker.network.bridge.enable_ip_masquerade": "true"},
            )
            logger.error(f"Docker network '{name}' created successfully.")
            return name, network
    except Exception as e:
        logger.error(f"An error occurred during docker network creation: {e}")
        return None, None
