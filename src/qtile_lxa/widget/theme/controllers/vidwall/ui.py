import os
import json
import signal
from pathlib import Path
from subprocess import Popen
from typing import Any, Literal
from qtile_extras.popup.toolkit import PopupRelativeLayout, PopupText, PopupImage
from qtile_lxa.utils import is_gpu_present
from qtile_lxa import __DEFAULTS__, __ASSETS_DIR__
from ...utils.colors import rgba
from ...config import Theme, ThemeAware

VIDWALL_STATE_CACHE = __DEFAULTS__.theme_manager.vidwall.state_cache_path
VIDWALL_PLAYLIST_CACHE = __DEFAULTS__.theme_manager.vidwall.playlist_cache_path
VIDWALL_STATE_CACHE.parent.mkdir(parents=True, exist_ok=True)
VIDWALL_PLAYLIST_CACHE.parent.mkdir(parents=True, exist_ok=True)


class VidWallUi(ThemeAware):
    widget_instance = None

    DEFAULT_STATE = {
        "visible": False,
        "is_playing": False,
        "is_muted": True,
        "loop": True,
        "current_video": None,
        "current_playlist": None,
        "active_playlist_page_index": 0,
        "pid": None,
    }

    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @staticmethod
    def _pid_is_xwinwrap(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_text()
            return "xwinwrap" in cmdline
        except Exception:
            return False

    @classmethod
    def load_cache(cls) -> dict:
        if VIDWALL_STATE_CACHE.exists():
            try:
                data = json.loads(VIDWALL_STATE_CACHE.read_text())

                pid = data.get("pid")
                valid = cls._pid_alive(pid) and cls._pid_is_xwinwrap(pid)

                if not valid:
                    data["is_playing"] = False
                    data["pid"] = None

                return {**cls.DEFAULT_STATE, **data}
            except Exception:
                pass
        return cls.DEFAULT_STATE.copy()

    @classmethod
    def save_cache(cls, data: dict):
        VIDWALL_STATE_CACHE.write_text(json.dumps(data, indent=2))

    def __init__(
        self,
        qtile,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        hwdec: Literal["auto", "no"] | None = None,
        playlist_file=__DEFAULTS__.theme_manager.vidwall.playlist_path,
        **kwargs: Any,
    ):
        super().__init__(theme=theme, config_file=config_file)

        self.qtile = qtile
        self.playlist_file = playlist_file

        self.process = None
        self.pid = None
        self.controls = []
        self.active_playlist_page_index = 0
        self.layout = None
        self.hwdec = (
            hwdec if hwdec is not None else ("auto" if is_gpu_present else "no")
        )

        # Restore cache
        state = self.load_cache()
        for k, v in state.items():
            setattr(self, k, v)

        self.playlists = self.load_playlists()
        self.videos_per_page = 12
        self.playlist_pages = self.split_playlist()
        self.active_playlist_page = (
            self.playlist_pages[self.active_playlist_page_index]
            if self.playlist_pages
            else None
        )

        self.color_scheme = self.theme.color.scheme.palette
        self.active_color = rgba(self.color_scheme.active, 0.4)
        self.inactive_color = rgba(self.color_scheme.inactive, 0.4)
        self.create_controls()

    def load_playlists(self):
        """Load playlists from the JSON file."""
        if not os.path.exists(self.playlist_file):
            playlists = {
                "Fav Songs": [
                    {
                        "title": "SKYHARBOR - Blind Side (2016 Version)",
                        "url": "https://www.youtube.com/watch?v=xPhu-9UYlD4",
                    },
                    {
                        "title": "SBonnie Tyler - Holding Out For A Hero (Official HD Video)",
                        "url": "https://www.youtube.com/watch?v=bWcASV2sey0",
                    },
                    {
                        "title": "Laura Branigan - Self Control (Moreno J Remix)",
                        "url": "https://www.youtube.com/watch?v=D9p6FU9rJ7Q",
                    },
                    {
                        "title": "Selena Gomez - Love You Like A Love",
                        "url": "https://www.youtube.com/watch?v=EgT_us6AsDg",
                    },
                ]
            }
            with open(self.playlist_file, "w") as f:
                json.dump(playlists, f, indent=4)
        with open(self.playlist_file, "r") as f:
            playlists = json.load(f)
        return playlists

    def split_playlist(self):
        playlists_batches = []

        for playlist_name, videos in self.playlists.items():
            video_count = len(videos)

            if video_count <= self.videos_per_page:
                playlists_batches.append(
                    {
                        "name": playlist_name,
                        "videos": videos,
                        "page_count": 1,
                        "page_number": 1,
                    }
                )
            else:
                total_parts = (video_count // self.videos_per_page) + (
                    1 if video_count % self.videos_per_page != 0 else 0
                )

                for part in range(1, total_parts + 1):
                    start_index = (part - 1) * self.videos_per_page
                    end_index = min(part * self.videos_per_page, video_count)

                    new_playlist_name = f"{playlist_name} {part}/{total_parts}"
                    playlists_batches.append(
                        {
                            "name": playlist_name,
                            "videos": videos[start_index:end_index],
                            "page_count": total_parts,
                            "page_number": part,
                        }
                    )

        return playlists_batches

    def play_video(self, url):
        """Play video using xwinwrap and mpv."""
        if self.is_playing:
            self.stop_video()

        self.current_video = url
        self.current_playlist = None

        command = [
            "xwinwrap",
            "-ov",
            "-fs",
            # "-g",
            # "1920x1080+0+0",
            "--",
            "mpv",
            f"--hwdec={self.hwdec}",
            "-wid",
            "WID",
            url,
            "--no-osc",
            "--no-osd-bar",
            "--loop-file" if self.loop else "",
            "--player-operation-mode=cplayer",
            "--no-audio" if self.is_muted else "",
            "--panscan=1.0",
            "--no-input-default-bindings",
        ]
        self.process = Popen(command)
        self.pid = self.process.pid
        self.is_playing = True
        self.save_state()

    def stop_video(self):
        """Stop the video."""
        if self.is_playing and self.process:
            self.process.terminate()
            self.process.wait()  # Ensure proper cleanup
        else:
            if self.pid and self._pid_alive(self.pid):
                os.kill(self.pid, signal.SIGTERM)
            Popen(
                "kill $(ps -aux | grep xwinwrap | awk '{print $2}')", shell=True
            ).wait()
        self.process = None
        self.pid = None
        self.is_playing = False
        self.current_playlist = None
        self.current_video = None
        self.save_state()

    def play_playlist(self, playlist_name):
        """Play all videos in the specified playlist."""
        if playlist_name not in self.playlists:
            return  # No such playlist

        videos = self.playlists[playlist_name]
        if not videos:
            return  # Empty playlist

        if self.is_playing:
            self.stop_video()

        self.current_playlist = playlist_name
        self.current_video = None

        with open(VIDWALL_PLAYLIST_CACHE, "w", encoding="utf-8") as f:
            for video in videos:
                f.write(f"{video['url']}\n")

        # self.play_video("--playlist=current_playlists.plst")
        command = [
            "xwinwrap",
            "-ov",
            "-fs",
            # "-g",
            # "1920x1080+0+0",
            "--",
            "mpv",
            f"--hwdec={self.hwdec}",
            "-wid",
            "WID",
            f"--playlist={VIDWALL_PLAYLIST_CACHE}",
            "--no-osc",
            "--no-osd-bar",
            "--loop-playlist" if self.loop else "",
            "--player-operation-mode=cplayer",
            "--no-audio" if self.is_muted else "",
            "--panscan=1.0",
            "--no-input-default-bindings",
        ]
        self.process = Popen(command)
        self.pid = self.process.pid
        self.is_playing = True
        self.save_state()

    def toggle_loop(self):
        """Toggle playlist looping."""
        self.loop = not self.loop
        self.save_state()

    def toggle_play_pause(self):
        """Toggle play and pause."""
        if self.is_playing:
            if self.process:
                self.process.terminate()
                self.process.wait()  # Ensure proper cleanup
            else:
                if self.pid and self._pid_alive(self.pid):
                    os.kill(self.pid, signal.SIGTERM)
            self.is_playing = False
            self.process = None
            self.pid = None
            self.save_state()
        else:
            if self.current_video:
                self.play_video(self.current_video)
            elif self.current_playlist:
                self.play_playlist(self.current_playlist)
            self.is_playing = True
            self.save_state()

    def toggle_mute(self):
        """Toggle mute and unmute."""
        self.is_muted = not self.is_muted
        if self.is_playing:
            if self.current_video:
                self.play_video(self.current_video)
            elif self.current_playlist:
                self.play_playlist(self.current_playlist)
        self.save_state()

    def header_items(self):
        common_props = {
            "pos_y": 0.01,
            "height": 0.05,
            "width": 0.1,
            "highlight": self.active_color,
            "highlight_radius": 13,
            "highlight_method": "border",
        }
        center_adjust = common_props["width"] / 2
        if self.active_playlist_page is not None:
            playlist_name = self.active_playlist_page["name"]
            playlist_page_count = self.active_playlist_page["page_count"]
            playlist_page_number = self.active_playlist_page["page_number"]
            if len(self.playlist_pages) > 1:
                playlist_title_prefix = f"{self.active_playlist_page_index + 1}/{len(self.playlist_pages )}. "
            else:
                playlist_title_prefix = ""
            if playlist_page_count > 1:
                playlist_title_suffix = (
                    f" ({playlist_page_number}/{playlist_page_count})"
                )
            else:
                playlist_title_suffix = ""
            playlist_title = (
                f"{playlist_title_prefix}{playlist_name}{playlist_title_suffix}"
            )
        else:
            playlist_title = playlist_name = "No Playlist"
        items = []
        branding = PopupText(
            **common_props,
            text="LXA VIDWALL",
            pos_x=0,
            h_align="left",
        )
        btn_close = PopupImage(
            filename=str(__ASSETS_DIR__ / "icons/close.png"),
            pos_x=0.95,
            pos_y=0.01,
            width=0.035,
            height=0.05,
            highlight="D91656",
            highlight_radius=15,
            h_align="right",
            mouse_callbacks={"Button1": self.hide},
        )

        btn_playlist_first = PopupText(
            **common_props,
            text="❮❮ First",
            pos_x=0.2 - center_adjust,
            h_align="center",
            mouse_callbacks={"Button1": self.switch_playlist_first},
        )

        btn_playlist_prev = PopupText(
            **common_props,
            text="❮ Previous",
            pos_x=0.3 - center_adjust,
            h_align="center",
            mouse_callbacks={"Button1": self.switch_playlist_previous},
        )

        btn_playlist = PopupText(
            text=f"{playlist_title}",
            pos_x=0.4,
            pos_y=0.01,
            height=0.05,
            width=0.2,
            highlight=self.active_color,
            highlight_radius=13,
            highlight_method="border",
            h_align="center",
            mouse_callbacks={
                "Button1": lambda playlist=playlist_name: self.play_playlist(playlist)
            },
        )

        btn_playlist_next = PopupText(
            **common_props,
            text="Next ❯",
            pos_x=0.7 - center_adjust,
            h_align="center",
            mouse_callbacks={"Button1": self.switch_playlist_next},
        )

        btn_playlist_last = PopupText(
            **common_props,
            text="Last ❯❯",
            pos_x=0.8 - center_adjust,
            h_align="center",
            mouse_callbacks={"Button1": self.switch_playlist_last},
        )

        items = [
            branding,
            btn_playlist_prev,
            btn_playlist_first,
            btn_playlist,
            btn_playlist_next,
            btn_playlist_last,
            btn_close,
        ]
        return items

    def footer_items(self):
        """Create the footer layout items."""

        common_props = {
            "pos_y": 0.9,
            "width": 0.1,
            "height": 0.07,
            "h_align": "center",
            "highlight": self.active_color,
            "highlight_radius": 13,
            "highlight_method": "border",
        }
        items = []

        # Play/Pause Button
        btn_play_pause = PopupText(
            **common_props,
            text="Play/Pause",
            pos_x=0.3,
            mouse_callbacks={"Button1": lambda: self.toggle_play_pause()},
        )

        # Stop Button
        btn_stop = PopupText(
            **common_props,
            text="Stop",
            pos_x=0.4,
            mouse_callbacks={"Button1": lambda: self.stop_video()},
        )

        # Mute/Unmute Button
        btn_mute = PopupText(
            **common_props,
            text="Mute/Unmute",
            pos_x=0.5,
            mouse_callbacks={"Button1": lambda: self.toggle_mute()},
        )

        # Loop Button
        btn_loop = PopupText(
            **common_props,
            text="Loop",
            pos_x=0.6,
            mouse_callbacks={"Button1": lambda: self.toggle_loop()},
        )
        items = [
            btn_play_pause,
            btn_stop,
            btn_mute,
            btn_loop,
        ]
        return items

    def body_items(self):
        """Create the popup layout body items."""

        playlist_items = []
        y_position = 0.1
        if self.active_playlist_page:
            if self.active_playlist_page["videos"]:
                for video in self.active_playlist_page["videos"]:
                    playlist_items.append(
                        PopupText(
                            text=f"{video['title']}",
                            pos_x=0.2,
                            pos_y=y_position,
                            width=0.6,
                            height=0.05,
                            h_align="center",
                            highlight=self.active_color,
                            highlight_radius=13,
                            highlight_method="border",
                            mouse_callbacks={
                                "Button1": lambda video_url=video[
                                    "url"
                                ]: self.play_video(video_url)
                            },
                        )
                    )
                    y_position += 0.05

        return playlist_items

    def create_controls(self):
        """Create the popup layout controls."""
        self.controls = self.header_items() + self.body_items() + self.footer_items()

    def switch_playlist_first(self):
        """Switch to the first page."""
        self.switch_playlist_page(0)

    def switch_playlist_previous(self):
        """Switch to the previous page."""
        self.switch_playlist_page(self.active_playlist_page_index - 1)

    def switch_playlist_next(self):
        """Switch to the next page."""
        self.switch_playlist_page(self.active_playlist_page_index + 1)

    def switch_playlist_last(self):
        """Switch to the last page."""
        self.switch_playlist_page(len(self.playlist_pages) - 1)

    def switch_playlist_page(self, page):
        """Switch to the specified page."""
        if page < 0:
            page = 0
        if page >= len(self.playlist_pages):
            page = len(self.playlist_pages) - 1
        if self.active_playlist_page_index != page:
            self.active_playlist_page_index = page
            if self.playlist_pages:
                self.active_playlist_page = self.playlist_pages[
                    self.active_playlist_page_index
                ]
            else:
                self.active_playlist_page = None
            self.hide()
            self.create_controls()
            self.show()

    def show(self):
        """Show the widget."""
        if VidWallUi.widget_instance:
            return
        self.layout = PopupRelativeLayout(
            self.qtile,
            width=800,
            height=600,
            controls=self.controls,
            background=self.inactive_color,
            border=self.active_color,
            border_width=2,
            close_on_click=False,
            hide_on_mouse_leave=True,
        )
        self.layout.show(centered=True)
        VidWallUi.widget_instance = self
        self.visible = True
        self.save_state()

    def hide(self):
        """Hide the widget."""
        if self.layout:
            self.layout.hide()
            self.layout = None

        VidWallUi.widget_instance = None
        self.visible = False
        self.save_state()

    def save_state(self):
        self.save_cache(
            {
                "visible": self.visible,
                "is_playing": self.is_playing,
                "is_muted": self.is_muted,
                "loop": self.loop,
                "current_video": self.current_video,
                "current_playlist": self.current_playlist,
                "active_playlist_page_index": self.active_playlist_page_index,
                "pid": self.pid,
            }
        )

    @classmethod
    def toggle_ui(cls, qtile):

        if cls.widget_instance:
            cls.widget_instance.hide()
            # return

        ui = cls(qtile)
        ui.show()
