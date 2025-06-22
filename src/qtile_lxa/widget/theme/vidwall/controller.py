import subprocess
from qtile_extras import widget
from libqtile import qtile
import GPUtil
from pathlib import Path
from typing import Any, Literal
from qtile_lxa.utils.notification import send_notification
from qtile_lxa.utils import is_gpu_present
from qtile_lxa import __DEFAULTS__
from qtile_lxa.widget.theme.config import ThemeConfig
from .ui import VidWallUi


theme_config = ThemeConfig()


class VidWallController(widget.GenPollText):
    def __init__(
        self,
        hwdec: Literal["auto", "no"] | None = None,
        playlist_file: Path = __DEFAULTS__.theme_manager.vidwall.playlist_path,
        symbol_playing_video="",
        symbol_playing_playlist="󰕲",
        symbol_pause="",
        symbol_stop="󰓛",
        symbol_unknown="󰋖",
        **kwargs: Any,
    ):
        super().__init__(update_interval=1, **kwargs)

        # Decorations for the widget
        self.decorations = [
            widget.decorations.RectDecoration(
                colour="#004040",
                radius=10,
                filled=True,
                padding_y=4,
                group=True,
                extrawidth=5,
            )
        ]

        # Video wallpaper-specific attributes
        self.hwdec: Literal["auto", "no"] | None = (
            hwdec or "auto" if is_gpu_present else "no"
        )
        self.playlist_file = playlist_file
        self.widget = self.load_vid_wall_widget()

        # Status symbols
        self.symbol_playing_video = symbol_playing_video
        self.symbol_playing_playlist = symbol_playing_playlist
        self.symbol_pause = symbol_pause
        self.symbol_stop = symbol_stop
        self.symbol_unknown = symbol_unknown

        # Text format for the widget
        self.format = "󰃽 {status}"

        # Callbacks for user interaction
        self.add_callbacks(
            {
                "Button1": self.toggle_play_pause,
                "Button2": self.save_current_config,
                "Button3": self.toggle_show_hide,
            }
        )
        self.autostart()

    def poll(self):
        """Update the widget display with the current status."""
        return self.check_status()

    def autostart(self):
        config = self.get_current_config()
        if config.get("enabled", False):
            self.widget.is_muted = config.get("mute", True)
            self.widget.loop = config.get("loop", True)
            if config.get("playlist"):
                self.widget.play_playlist(config["playlist"])
            elif config.get("song"):
                self.widget.play_video(config["song"])
            self.widget.save_state()

    def check_status(self):
        """Fetch the current state of the video wallpaper."""
        if self.widget and self.widget.widget_instance:
            if self.widget.is_playing:
                if self.widget.current_video:
                    return self.format.format(status=self.symbol_playing_video)
                elif self.widget.current_playlist:
                    return self.format.format(status=self.symbol_playing_playlist)
                else:
                    return self.format.format(status=self.symbol_unknown)
            else:
                if self.widget.current_video or self.widget.current_playlist:
                    return self.format.format(status=self.symbol_pause)
                else:
                    return self.format.format(status=self.symbol_stop)
        return self.format.format(status=self.symbol_unknown)

    def load_vid_wall_widget(self):
        """Initialize the video wallpaper widget."""
        return VidWallUi(qtile, hwdec=self.hwdec, playlist_file=self.playlist_file)

    def toggle_show_hide(self):
        """Toggle visibility of the Video Wallpaper Widget."""
        if not self.widget.widget_instance:
            self.widget = self.load_vid_wall_widget()
        else:
            self.widget.hide()
        self.widget.show()

    def toggle_play_pause(self):
        """Toggle play/pause for the video wallpaper."""
        if self.widget.widget_instance:
            self.widget.widget_instance.toggle_play_pause()
        else:
            send_notification(
                title=f"App not Running at this moment",
                msg="Video Wallpaper",
                app_name="ThemeManager",
                app_id=2003,
                timeout=5000,
            )

    def get_current_config(self):
        """Get the current configuration for the video wallpaper."""
        return theme_config.load_config().get("video_wallpaper", {})

    def save_current_config(self):
        """Save the current state of the video wallpaper to the theme configuration."""
        config = theme_config.load_config()
        if self.widget.widget_instance:
            config["video_wallpaper"] = {
                "playlist": self.widget.current_playlist,
                "song": self.widget.current_video,
                "mute": self.widget.is_muted,
                "loop": self.widget.loop,
                "enabled": self.widget.is_playing,
            }
            theme_config.save_config(config)
            send_notification(
                title=f"State Saved",
                msg="Video Wallpaper",
                app_name="ThemeManager",
                app_id=2003,
                timeout=5000,
            )
        else:
            send_notification(
                title=f"App not Running at this moment",
                msg="Video Wallpaper",
                app_name="ThemeManager",
                app_id=2003,
                timeout=5000,
            )
