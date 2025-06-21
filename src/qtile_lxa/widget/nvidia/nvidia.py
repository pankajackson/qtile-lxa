import GPUtil
from libqtile.log_utils import logger
from libqtile.widget import base
from typing import Any
from .typing import NvidiaConfig
from qtile_lxa.utils import is_gpu_present


class Nvidia(base.InLoopPollText):
    """
    A simple widget to display NVIDIA GPU usage and memory.
    Widget requirements: GPUtil_ must be installed.
    .. _GPUtil: https://pypi.org/project/gputil/
    """

    def __init__(
        self,
        config: NvidiaConfig = NvidiaConfig(),
        update_interval: float = 2.0,
        **kwargs: Any,
    ):
        self.config = config
        self.update_interval = update_interval
        self.format = (
            "󱜕  {name} [ : {util}%   : {mem_used}/{mem_total} GB   󰔏 {temp}°C ]   "
        )
        base.InLoopPollText.__init__(self, **kwargs)

    def _configure(self, qtile, bar):
        base.InLoopPollText._configure(self, qtile, bar)
        self.foreground_normal = self.foreground

    def get_stats(self):
        try:
            if not is_gpu_present():
                return

            gpus = GPUtil.getGPUs()
            gpu = gpus[0]
            variables = {
                "name": gpu.name,
                "util": round(gpu.load * 100, 2),
                "mem_used": round(gpu.memoryUsed / 1024, 1),
                "mem_total": round(gpu.memoryTotal / 1024, 1),
                "temp": gpu.temperature,
            }
            return variables
        except Exception as e:
            logger.error(e)
            return

    def poll(self) -> str:  # type: ignore[override]
        stats = self.get_stats()

        # Temperature not available
        if stats is None:
            return "󱜕  N/A   "
        temp_value: int = stats.get("temp", 0)
        if self.layout:
            if int(temp_value) < self.config.high:
                self.layout.colour = self.foreground_normal
            elif int(temp_value) < self.config.crit:
                self.layout.colour = self.config.fgcolor_high
            elif int(temp_value) >= self.config.crit:
                self.layout.colour = self.config.fgcolor_crit

        return self.format.format(**stats)
