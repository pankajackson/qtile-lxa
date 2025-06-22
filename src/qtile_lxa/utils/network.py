import subprocess
from libqtile.log_utils import logger


def check_interface_exists(interface_name):
    try:
        result = subprocess.run(
            ["ip", "link", "show", interface_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"An error occurred while checking interface: {e}")
        return False


def get_default_interface():
    try:
        result = subprocess.run(
            ["ip", "route"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.returncode != 0:
            raise Exception(f"Error executing ip route: {result.stderr}")

        for line in result.stdout.splitlines():
            if line.startswith("default"):
                interface = line.split()[4]
                return interface

        raise Exception("Default interface not found.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None


def get_interface(interface_name=None):
    if interface_name:
        if check_interface_exists(interface_name):
            return interface_name
        else:
            logger.error(
                f"Interface {interface_name} not found, using default interface."
            )

    return get_default_interface()
