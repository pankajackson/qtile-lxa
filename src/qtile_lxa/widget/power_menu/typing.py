from enum import Enum
from qtile_lxa import __DEFAULTS__


class SleepMode(Enum):
    sleep = "systemctl suspend"
    hibernate = "systemctl hibernate"
    hybrid_sleep = "systemctl hybrid-sleep"


class PowerMenuConfig:
    sleep_mode: SleepMode = SleepMode.sleep
    screenlock_effect: str = __DEFAULTS__.theme_manager.pywall.screenlock_effect
