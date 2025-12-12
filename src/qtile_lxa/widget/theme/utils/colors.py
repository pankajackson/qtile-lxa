from typing import Any


def invert_hex_color_of(hex_color: str):
    hex_color = hex_color.lstrip("#")  # Remove '#' if present
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # Convert hex to RGB
    inverted_rgb = tuple(255 - value for value in rgb)  # Invert RGB
    inverted_hex = "#%02x%02x%02x" % inverted_rgb  # Convert RGB to hex
    return inverted_hex


def rgba(hex_color: Any, alpha: float):
    hex_color = hex_color.lstrip("#")
    return f"#{hex_color}{int(alpha * 255):02x}"
