import ipaddress
import podman
from libqtile.log_utils import logger
from qtile_lxa import __DEFAULTS__


def get_podman_network(name=None, subnet=None, gateway=None):

    name = __DEFAULTS__.podman.network if name is None else name
    subnet = __DEFAULTS__.podman.subnet if subnet is None else subnet

    try:
        with podman.PodmanClient() as client:
            if not client.ping():
                logger.error("Unable to connect to Podman.")
                return None, None

            # Check if network already exists
            existing_networks = [
                net for net in client.networks.list() if net.name == name
            ]
            if existing_networks:
                network = existing_networks[0]
                network_subnet = network.attrs.get("subnets", [{}])[0].get(
                    "subnet", "Unknown"
                )
                logger.info(
                    f"Podman network '{name}' already exists with subnet {network_subnet}."
                )
                return network.name, ipaddress.ip_network(network_subnet, strict=False)

            # Convert subnet to ip_network object
            network = ipaddress.ip_network(subnet, strict=False)
            gateway = str(list(network.hosts())[0]) if gateway is None else gateway

            # Create Podman network
            network_config = {
                "name": name,
                "driver": "bridge",
                "subnets": [
                    {
                        "subnet": subnet,
                        "gateway": gateway,
                    }
                ],
            }

            created_network = client.networks.create(**network_config)
            logger.error(
                f"Podman network '{created_network.name}' created successfully."
            )
            return created_network.name, network

    except Exception as e:
        logger.error(f"An error occurred during Podman network creation: {e}")
        return None, None
