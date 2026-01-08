import subprocess
from libqtile.log_utils import logger


def check_interface_exists(interface_name: str) -> bool:
    try:
        result = subprocess.run(
            ["ip", "link", "show", interface_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking interface '{interface_name}': {e}")
        return False


def get_default_interface() -> str | None:
    try:
        output = subprocess.check_output(
            ["ip", "route"], text=True, stderr=subprocess.STDOUT
        )
    except Exception as e:
        logger.error(f"Error executing 'ip route': {e}")
        return None

    for line in output.splitlines():
        if line.startswith("default"):
            parts = line.split()
            # Look for the token "dev"
            if "dev" in parts:
                try:
                    return parts[parts.index("dev") + 1]
                except (IndexError, ValueError):
                    continue

    logger.error("Default interface not found.")
    return None


def get_interface(interface_name: str | None = None) -> str | None:
    if interface_name:
        if check_interface_exists(interface_name):
            return interface_name
        else:
            logger.error(
                f"Interface '{interface_name}' not found. Falling back to default."
            )

    return get_default_interface()
