import os
import subprocess
import threading
from pathlib import Path
from qtile_extras import widget
from libqtile import qtile
from libqtile.log_utils import logger
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.utils.notification import send_notification
from qtile_lxa.utils.process_lock import ProcessLocker
from qtile_lxa.utils.data_manager import sync_dirs
from .sources.git import Git
from .sources.bing import Bing
from .sources.nasa import Nasa
from .sources.utils import (
    get_source_list,
    get_active_source_id,
    sync_config_for_source,
    switch_next_source,
    switch_prev_source,
)
from qtile_lxa import __DEFAULTS__, __BASE_DIR__, __ASSETS_DIR__

theme_config = ThemeConfig()


class PyWallChanger(widget.GenPollText):
    def __init__(
        self,
        wallpaper_dir=__DEFAULTS__.theme_manager.pywall.wallpaper_dir,
        update_screenlock=False,
        screenlock_effect=__DEFAULTS__.theme_manager.pywall.screenlock_effect,
        wallpaper_repos=__DEFAULTS__.theme_manager.pywall.wallpaper_repos,
        bing_potd=True,
        nasa_potd=True,
        nasa_api_key="hETQq0FPsZJnUP9C3sUEFtwmJH3edb4I5bghfWDM",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.wallpaper_dir = wallpaper_dir
        self.update_screenlock = update_screenlock
        self.screenlock_effect = screenlock_effect
        self.wallpaper_repos = wallpaper_repos or []
        self.bing_potd = bing_potd
        self.nasa_potd = nasa_potd
        self.nasa_api_key = nasa_api_key
        self.text_template = f"󰸉: {{index}}"  # Icon and index
        self.update_wall_timer = None
        self.update_lock_timer = None
        self.update_interval = 900
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
        self.add_callbacks(
            {
                "Button1": self.next_source,  # Switch to next source
                "Button3": self.prev_source,  # Switch to previous source
                "Button2": self.apply_pywal,  # Apply current wallpaper
                "Button4": self.next_wallpaper,  # Next wallpaper
                "Button5": self.prev_wallpaper,  # Previous wallpaper
            }
        )
        self.sync_default_wallpapers()
        sync_config_for_source(
            theme_config=theme_config, wallpaper_dir=self.wallpaper_dir
        )
        self.set_wallpaper()
        self.update_text()

    def poll(self):
        return self.get_text()

    def sync_default_wallpapers(self):
        sync_dirs(
            __ASSETS_DIR__ / "wallpapers",
            __DEFAULTS__.theme_manager.pywall.wallpaper_dir / "defaults",
        )

    def sync_sources_background(self):
        def worker():
            try:
                self.sync_sources()
            except Exception as e:
                logger.error(f"sync_sources_background failed: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def sync_sources(self):
        process_locker = ProcessLocker("sync_sources")
        lock_fd = process_locker.acquire_lock()
        if not lock_fd:
            return
        try:
            active_source_id = get_active_source_id(theme_config=theme_config)

            source_git = Git(
                wallpaper_dir=self.wallpaper_dir,
                theme_config=theme_config,
                wallpaper_repos=self.wallpaper_repos,
            )
            source_git.sync_git()

            if self.bing_potd:
                source_bing = Bing(
                    wallpaper_dir=self.wallpaper_dir, theme_config=theme_config
                )
                source_bing.sync_bing()

            if self.nasa_potd:
                source_bing = Nasa(
                    wallpaper_dir=self.wallpaper_dir, theme_config=theme_config
                )
                source_bing.sync_nasa()
            source_list = get_source_list(theme_config)
            if source_list and active_source_id is None:
                self.set_wallpaper(screen_lock_background=True, notify=True)
        finally:
            process_locker.release_lock(lock_fd=lock_fd)

    def get_active_wall_id(self):
        """Get the current wallpaper index."""
        active_source_id = get_active_source_id(theme_config=theme_config)
        if active_source_id is not None:
            return theme_config.load_config()["wallpaper"]["sources"][active_source_id][
                "active_index"
            ]
        return None

    def set_active_wall_id(self, index):
        """Save the current wallpaper index."""
        active_source_id = get_active_source_id(theme_config=theme_config)
        if active_source_id is not None:
            config = theme_config.load_config()
            config["wallpaper"]["sources"][active_source_id]["active_index"] = index
            theme_config.save_config(config)

    def get_wallpaper(self, index=None):
        sources = get_source_list(theme_config)
        if not sources:
            return
        if index is None:
            index = self.get_active_wall_id()
        if index is not None:
            active_source_id = get_active_source_id(theme_config=theme_config)
            source = sources[active_source_id]
            wallpaper = self.wallpaper_dir
            if source["group"]:
                wallpaper = os.path.join(wallpaper, source["group"])
            if source["collection"]:
                wallpaper = os.path.join(wallpaper, source["collection"])
            wallpaper = os.path.join(wallpaper, source["wallpapers"][index])

            return wallpaper
        return

    def set_wallpaper(self, index=None, screen_lock_background=False, notify=False):
        """Set the wallpaper for the given index."""
        if index is None:
            index = self.get_active_wall_id()
        if index is not None:
            wallpaper = self.get_wallpaper(index=index)
            sources = get_source_list(theme_config)
            active_source_id = get_active_source_id(theme_config=theme_config)
            file_name = sources[active_source_id]["wallpapers"][index]
            if wallpaper:
                try:
                    if not os.path.isfile(wallpaper):
                        raise FileNotFoundError(f"Wallpaper not found: {wallpaper}")
                    subprocess.run(["feh", "--bg-scale", wallpaper], check=True)
                    if notify:
                        send_notification(
                            "Wallpaper Changed",
                            file_name,
                            app_name="Wallpaper",
                            app_id=9998,
                            timeout=5000,
                        )
                    if self.update_screenlock and screen_lock_background:
                        if self.update_lock_timer and self.update_lock_timer.is_alive():
                            self.update_lock_timer.cancel()
                        self.update_lock_timer = threading.Timer(
                            5, self._update_screenlock_image, [wallpaper, notify]
                        )
                        self.update_lock_timer.start()

                    self.set_active_wall_id(index)
                    self.update_text()
                except FileNotFoundError as e:
                    send_notification(
                        "Wallpaper Changed",
                        f"Error: {e}",
                        app_name="Wallpaper",
                        app_id=9998,
                        timeout=5000,
                    )
                    logger.error(f"Error: {e}")
                except subprocess.CalledProcessError as e:
                    send_notification(
                        "Wallpaper Changed",
                        f"Error: Failed to set wallpaper. Command exited with status {e.returncode}.",
                        app_name="Wallpaper",
                        app_id=9998,
                        timeout=5000,
                    )
                    logger.error(
                        f"Error: Failed to set wallpaper. Command exited with status {e.returncode}."
                    )
                    logger.error(f"Command: {e.cmd}")
                    logger.error(f"Output: {e.output}")
                    logger.error(f"Stderr: {e.stderr}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred: {e}")

    def _update_screenlock_image(self, wallpaper, notify=False):
        """Update the screen lock background."""
        screen_lock_update_cmd = ["betterlockscreen", "-u", wallpaper]
        if self.screenlock_effect:
            screen_lock_update_cmd += ["--fx", self.screenlock_effect]
        subprocess.run(screen_lock_update_cmd, check=True)
        if notify:
            send_notification(
                "ScreenLock",
                "ScreenLock Background has been updated!",
                app_name="ScreenLock",
                app_id=9995,
            )

    def get_text(self):
        """Build the text that displays the current wallpaper index."""
        sources = get_source_list(theme_config)  # Returns the dictionary of sources
        active_source_id = get_active_source_id(theme_config=theme_config)
        active_wall_id = self.get_active_wall_id()
        if active_source_id is None or not sources:
            active_source_id = "-"
        else:
            source_ids = list(sources.keys())  # Get a list of source IDs
            active_source_id = source_ids.index(active_source_id)
        if active_wall_id is None:
            active_wall_id = "-"
        return self.text_template.format(index=f"{active_source_id}:{active_wall_id}")

    def update_text(self):
        """Update the text that displays the current wallpaper index."""
        self.text = self.get_text()
        self.draw()

    def next_source(self):
        switch_next_source(theme_config=theme_config)
        self.update_text()

        # If a timer is running, cancel it and start a new one
        if self.update_wall_timer and self.update_wall_timer.is_alive():
            self.update_wall_timer.cancel()

        self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
        self.update_wall_timer.start()

    def prev_source(self):
        switch_prev_source(theme_config=theme_config)
        self.update_text()

        # If a timer is running, cancel it and start a new one
        if self.update_wall_timer and self.update_wall_timer.is_alive():
            self.update_wall_timer.cancel()

        self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
        self.update_wall_timer.start()

    def next_wallpaper(self):
        """Set the next wallpaper."""
        active_source_id = get_active_source_id(theme_config=theme_config)
        active_wall_id = self.get_active_wall_id()
        sources = get_source_list(theme_config)
        if active_wall_id is not None:
            next_index = (active_wall_id + 1) % len(
                sources[active_source_id]["wallpapers"]
            )
            self.set_active_wall_id(next_index)
            self.update_text()
            if self.update_wall_timer and self.update_wall_timer.is_alive():
                self.update_wall_timer.cancel()
            self.update_wall_timer = threading.Timer(
                0.2, self.set_wallpaper, [next_index, True, True]
            )
            self.update_wall_timer.start()

    def prev_wallpaper(self):
        """Set the previous wallpaper."""
        active_source_id = get_active_source_id(theme_config=theme_config)
        active_wall_id = self.get_active_wall_id()
        sources = get_source_list(theme_config)
        if active_wall_id is not None:
            prev_index = (active_wall_id - 1) % len(
                sources[active_source_id]["wallpapers"]
            )
            self.set_active_wall_id(prev_index)
            self.update_text()
            if self.update_wall_timer and self.update_wall_timer.is_alive():
                self.update_wall_timer.cancel()
            self.update_wall_timer = threading.Timer(
                0.2, self.set_wallpaper, [prev_index, True, True]
            )
            self.update_wall_timer.start()

    def apply_pywal(self):
        """Apply the current wallpaper using pywal."""
        wallpaper = self.get_wallpaper()
        if wallpaper:
            subprocess.run(["wal", "-i", wallpaper])
            qtile.reload_config()
