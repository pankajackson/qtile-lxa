from dataclasses import dataclass, field
from typing import List


@dataclass
class ScreenProfileConfig:
    default_profile: str = "my_desktop_screen"
    icon_default: str = "✅"
    icon_other: str = "❓"
    error_icon: str = "❌"
    format: str = " {icon}"
    arandr_cmd: str = "arandr"
    current_cmd: List[str] = field(default_factory=lambda: ["autorandr", "--current"])

    def load_cmd(self) -> List[str]:
        return ["autorandr", "--load", self.default_profile]

    def save_cmd(self) -> List[str]:
        return ["autorandr", "--force", "--save", self.default_profile]
