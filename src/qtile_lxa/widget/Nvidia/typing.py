from dataclasses import dataclass


@dataclass
class NvidiaConfig:
    fgcolor_crit: str = "ff0000"
    fgcolor_high: str = "ffaa00"
    high: int = 50
    crit: int = 70
