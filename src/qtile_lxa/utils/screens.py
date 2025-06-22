import subprocess
import re
from libqtile.log_utils import logger


def get_screens():
    xrandr_output = subprocess.check_output(["xrandr"]).decode()  # Get xrandr output
    lines = xrandr_output.splitlines()[1:]
    screens = []

    for line in lines:
        if not line.startswith(" "):
            parts = line.split()

            name = parts[0]
            connected = "connected" in parts
            active = False
            resolution = None
            refresh_rate = None
            position = None
            rotation = "normal"  # Default rotation
            modes = {}
            recommended = {}

            if connected:

                # Get Rotation
                try:
                    rotation_data = line.split("(")[0].split()
                    if "primary" in rotation_data:
                        rotation_data.remove("primary")
                    if len(rotation_data) == 4:
                        rotation = rotation_data[-1]
                except:
                    logger.error(f"Error Fetching Rotation for {name}")

                # Use regular expression to extract resolution and position
                resolution_cords = None
                position_cords = None
                try:
                    match = re.search(r"(\d+x\d+)\+(\d+)\+(\d+)", line)
                    if match:
                        resolution_cords = match.group(1)
                        position_cords = {
                            "x": int(match.group(2)),
                            "y": int(match.group(3)),
                        }

                    if position_cords:  # Ensure position_cords are not None
                        position = f"{position_cords['x']}x{position_cords['y']}"
                    if resolution_cords:  # Ensure resolution_cords are not None
                        width, height = resolution_cords.split("x")
                        if rotation in ["left", "right"]:
                            resolution = f"{height}x{width}"
                        else:
                            resolution = f"{width}x{height}"
                except:
                    logger.error(f"Error Fetching resolution and position for {name}")

                # Get mode
                try:
                    current_line_id = lines.index(line)
                    init_mode_id = 0
                    available_rates = []
                    while True:
                        init_mode_id += 1
                        mode_line = lines[current_line_id + init_mode_id]
                        if not mode_line.startswith(" "):
                            break
                        mode_parts = mode_line.split()
                        res = mode_parts[0]
                        all_refresh_rates = mode_parts[1:]
                        all_refresh_rates_cleaned = []
                        for rate in all_refresh_rates:
                            is_active = False
                            is_recommended = False
                            if rate.endswith("*"):
                                is_active = True
                            elif rate.endswith("*+"):
                                is_active = True
                                is_recommended = True
                            elif (
                                rate != all_refresh_rates[-1]
                                and all_refresh_rates[all_refresh_rates.index(rate) + 1]
                                == "+"
                            ):
                                is_recommended = True

                            try:
                                rate = re.sub(r"[+*]", "", rate)
                                float(rate)  # check if refresh rate is valid
                                all_refresh_rates_cleaned.append(rate)
                                if is_active:
                                    refresh_rate = rate
                                if is_recommended:
                                    recommended = {
                                        "resolution": res,
                                        "refresh_rate": rate,
                                    }
                            except:
                                continue
                        modes[res] = all_refresh_rates_cleaned

                except:
                    logger.error(f"Error fetching mode for {name}")

            if resolution and refresh_rate and position:
                active = True

            screens.append(
                {
                    "name": name,
                    "connected": connected,
                    "active": active,
                    "resolution": resolution,
                    "refresh_rate": refresh_rate,
                    "position": position,
                    "rotation": rotation,
                    "modes": modes,
                    "recommended": recommended,
                }
            )

    return screens


def get_active_monitor_count(screens=get_screens()):
    active_screens = list(filter(lambda s: s["active"] and s["connected"], screens))
    return len(active_screens)
