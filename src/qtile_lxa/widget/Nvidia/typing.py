from dataclasses import dataclass
from typing import Optional


@dataclass
class NvidiaConfig:
    fgcolor_crit: str = "ff0000"
    fgcolor_high: str = "ffaa00"
    high: int = 50
    crit: int = 70
