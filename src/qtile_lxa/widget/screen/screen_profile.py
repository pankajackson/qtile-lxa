import subprocess
from qtile_extras.widget import GenPollText
from libqtile.log_utils import logger
from typing import Any
from .typing import ScreenProfileConfig


class ScreenProfile(GenPollText):
    def __init__(
        self,
        config: ScreenProfileConfig = ScreenProfileConfig(),
        **kwargs: Any,
    ):
        self.config = config
        self.format = " {icon}"
        super().__init__(func=self.check_screen_profile, update_interval=2, **kwargs)

    def run_command(self, cmd: list[str]):
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.SubprocessError as e:
            logger.error(f"Error running command: {cmd} - {str(e)}")
            return None

    def check_screen_profile(self):
        current_profile = self.run_command(self.config.current_cmd)
        if current_profile == self.config.default_profile:
            return self.format.format(icon=self.config.icon_default)
        elif current_profile:
            return self.format.format(icon=self.config.icon_other)
        else:
            return self.format.format(icon=self.config.error_icon)

    def button_press(self, x, y, button):
        if button == 1:
            self.run_command(self.config.load_cmd())
        elif button == 2:
            self.run_command(self.config.save_cmd())
        elif button == 3:
            subprocess.Popen(self.config.arandr_cmd, shell=True)
