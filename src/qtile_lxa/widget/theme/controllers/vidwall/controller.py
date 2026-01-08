import threading
from enum import Enum, auto
from pathlib import Path
from typing import Any, Literal

from libqtile import qtile, hook
from libqtile.log_utils import logger
from qtile_extras import widget

from qtile_lxa.utils.notification import send_notification
from qtile_lxa.utils import is_gpu_present
from qtile_lxa import __DEFAULTS__
from ...config import Theme, ThemeAware, VideoWallpaper
from .ui import VidWallUi


class _VidWallAction(Enum):
    START = auto()
    RESTART = auto()


class VidWallController(ThemeAware, widget.GenPollText):
    def __init__(
        self,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        hwdec: Literal["auto", "no"] | None = None,
        playlist_file: Path = __DEFAULTS__.theme_manager.vidwall.playlist_path,
        symbol_playing_video="",
        symbol_playing_playlist="󰕲",
        symbol_pause="",
        symbol_stop="󰓛",
        symbol_unknown="󰋖",
        **kwargs: Any,
    ):
        ThemeAware.__init__(self, theme=theme, config_file=config_file)
        widget.GenPollText.__init__(self, update_interval=1, **kwargs)

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

        # Video config
        self.hwdec: Literal["auto", "no"] = hwdec or (
            "auto" if is_gpu_present else "no"
        )
        self.playlist_file = playlist_file

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

        # Debounce timer
        self._vidwall_timer: threading.Timer | None = None

        # Hooks
        hook.subscribe.startup_complete(self._on_startup)
        hook.subscribe.screen_change(self._on_screen_change)

    def _on_startup(self, *args):
        self._schedule(_VidWallAction.START)

    def _on_screen_change(self, *args):
        self._schedule(_VidWallAction.RESTART)

    def _schedule(self, action: _VidWallAction, delay: float = 2):
        if self._vidwall_timer and self._vidwall_timer.is_alive():
            self._vidwall_timer.cancel()

        self._vidwall_timer = threading.Timer(delay, self._dispatch_action, [action])
        self._vidwall_timer.daemon = True
        self._vidwall_timer.start()

    def _dispatch_action(self, action: _VidWallAction):
        qtile.call_later(0, self._apply_action, action)

    def _apply_action(self, action: _VidWallAction):
        try:
            config = self.get_current_config()
            if action is _VidWallAction.START:
                if not config.enabled:
                    return
                ui = self._ui()
                if ui and ui.is_playing:
                    return

                self._start_from_config(config)

            elif action is _VidWallAction.RESTART:
                # Screen change → force restart for resize
                ui = self._ui() or self._new_ui()
                ui.load_cache()
                if ui.is_playing:
                    ui.toggle_play_pause()
                    ui.toggle_play_pause()

        except Exception as e:
            logger.error(f"VidWall action failed ({action}): {e}")

    def _start_from_config(self, config: VideoWallpaper):
        ui = self._new_ui()
        ui.is_muted = config.mute
        ui.loop = config.loop

        if config.playlist:
            ui.play_playlist(config.playlist)
        elif config.song:
            ui.play_video(config.song)

        ui.save_state()

    def _new_ui(self) -> VidWallUi:
        return VidWallUi(
            qtile,
            hwdec=self.hwdec,
            playlist_file=self.playlist_file,
            theme=self.theme,
        )

    def _ui(self) -> VidWallUi | None:
        return VidWallUi.widget_instance

    def poll(self):
        """Update the widget display with the current status."""
        return self.check_status()

    def check_status(self):
        """Fetch the current state of the video wallpaper."""
        ui = self._ui()
        if not ui:
            return self.format.format(status=self.symbol_unknown)

        ui.load_cache()
        if ui.is_playing:
            if ui.current_video:
                return self.format.format(status=self.symbol_playing_video)
            if ui.current_playlist:
                return self.format.format(status=self.symbol_playing_playlist)
            return self.format.format(status=self.symbol_unknown)

        if ui.current_video or ui.current_playlist:
            return self.format.format(status=self.symbol_pause)

        return self.format.format(status=self.symbol_stop)

    def toggle_show_hide(self, qtile=qtile):
        """Toggle visibility of the Video Wallpaper Widget."""

        VidWallUi(qtile).toggle_ui(qtile)

    def toggle_play_pause(self):
        """Toggle play/pause for the video wallpaper."""
        ui = self._ui()
        if not ui:
            send_notification(
                title="App not running",
                msg="Video Wallpaper",
                app_name="ThemeManager",
                app_id=2003,
                timeout=3000,
            )
            return
        ui.toggle_play_pause()

    def save_current_config(self):
        """Save the current state of the video wallpaper to the theme configuration."""
        ui = self._ui()
        if not ui:
            send_notification(
                title="App not running",
                msg="Video Wallpaper",
                app_name="ThemeManager",
                app_id=2003,
                timeout=3000,
            )
            return

        config = self.theme.video_wallpaper
        config.playlist = ui.current_playlist
        config.song = ui.current_video
        config.mute = ui.is_muted
        config.loop = ui.loop
        config.enabled = ui.is_playing
        self.theme.save()

        send_notification(
            title="State Saved",
            msg="Video Wallpaper",
            app_name="ThemeManager",
            app_id=2003,
            timeout=3000,
        )

    def get_current_config(self):
        return self.theme.video_wallpaper
