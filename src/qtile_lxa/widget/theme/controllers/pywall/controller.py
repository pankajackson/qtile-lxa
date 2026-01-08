import os
import subprocess
import threading
from pathlib import Path
from libqtile import qtile, hook
from qtile_extras import widget
from libqtile.log_utils import logger
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
from ...config import Theme, ThemeAware
from qtile_lxa import __DEFAULTS__, __BASE_DIR__, __ASSETS_DIR__


class PyWallChanger(ThemeAware, widget.GenPollText):
    def __init__(
        self,
        config_file: Path = __DEFAULTS__.theme_manager.config_path,
        theme: Theme | None = None,
        wallpaper_dir=__DEFAULTS__.theme_manager.pywall.wallpaper_dir,
        update_screenlock=False,
        screenlock_effect=__DEFAULTS__.theme_manager.pywall.screenlock_effect,
        wallpaper_repos=__DEFAULTS__.theme_manager.pywall.wallpaper_repos,
        bing_potd=True,
        nasa_potd=True,
        nasa_api_key="hETQq0FPsZJnUP9C3sUEFtwmJH3edb4I5bghfWDM",
        **kwargs,
    ):
        ThemeAware.__init__(self, theme=theme, config_file=config_file)
        widget.GenPollText.__init__(self, **kwargs)
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
        self.conf_reload_timer = None
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
            theme_config=self.theme, wallpaper_dir=self.wallpaper_dir
        )
        self.update_text()
        self._wallpaper_timer: threading.Timer | None = None

        # Register hooks ONCE
        hook.subscribe.startup_complete(self._on_qtile_ready)
        hook.subscribe.screen_change(self._on_screen_change)

        # Optional: apply immediately if widget is created late
        qtile.call_later(0.1, self._schedule_wallpaper_apply)

    def _on_qtile_ready(self, *args):
        logger.info("PyWallChanger: startup_complete")
        self._schedule_wallpaper_apply()

    def _on_screen_change(self, *args):
        logger.info("PyWallChanger: screen_change")
        self._schedule_wallpaper_apply()

    def _schedule_wallpaper_apply(self, delay: float = 0.3):
        if self._wallpaper_timer and self._wallpaper_timer.is_alive():
            self._wallpaper_timer.cancel()

        self._wallpaper_timer = threading.Timer(delay, self._apply_wallpaper_safe)
        self._wallpaper_timer.daemon = True
        self._wallpaper_timer.start()

    def _apply_wallpaper_safe(self):
        try:
            qtile.call_later(0, self.set_wallpaper)
        except Exception as e:
            logger.error(f"PyWallChanger wallpaper apply failed: {e}")

    def poll(self):
        self.sync_potd_sources()
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
        send_notification(
            "Syncing wallpaper sources",
            "Wallpaper",
            app_name="Wallpaper",
            app_id=99980,
            timeout=5000,
        )
        process_locker = ProcessLocker("sync_sources")
        lock_fd = process_locker.acquire_lock()
        if not lock_fd:
            return
        try:
            active_source_id = get_active_source_id(self.theme)

            source_git = Git(
                wallpaper_dir=self.wallpaper_dir,
                wallpaper_repos=self.wallpaper_repos,
                theme_config=self.theme,
            )
            source_git.sync_git()
            self.sync_potd_sources()
            source_list = get_source_list(self.theme)
            if source_list and active_source_id is None:
                self.set_wallpaper(screen_lock_background=True, notify=True)
        finally:
            send_notification(
                "Synced wallpaper sources",
                "Wallpaper",
                app_name="Wallpaper",
                app_id=99980,
                timeout=5000,
            )
            process_locker.release_lock(lock_fd)

    def sync_potd_sources(self):
        if self.bing_potd:
            source_bing = Bing(
                wallpaper_dir=self.wallpaper_dir, theme_config=self.theme
            )
            is_synced = source_bing.sync_bing()
            if is_synced:
                source_list = get_source_list(self.theme)
                active_source_id = get_active_source_id(self.theme)
                if active_source_id is not None:
                    source = source_list[active_source_id]
                    if (
                        source.group == "bing"
                        and source.collection == "PictureOfTheDay"
                    ):
                        self.set_wallpaper(screen_lock_background=True, notify=True)

        if self.nasa_potd:
            source_bing = Nasa(
                wallpaper_dir=self.wallpaper_dir, theme_config=self.theme
            )
            is_synced = source_bing.sync_nasa()
            if is_synced:
                source_list = get_source_list(self.theme)
                active_source_id = get_active_source_id(self.theme)
                if active_source_id is not None:
                    source = source_list[active_source_id]
                    if (
                        source.group == "nasa"
                        and source.collection == "PictureOfTheDay"
                    ):
                        self.set_wallpaper(screen_lock_background=True, notify=True)

    def get_active_wall_id(self):
        """Get the current wallpaper index."""
        active_source_id = get_active_source_id(self.theme)
        if active_source_id is not None:
            return self.theme.wallpaper.sources[active_source_id].active_index
        return None

    def set_active_wall_id(self, index):
        """Save the current wallpaper index."""
        active_source_id = get_active_source_id(self.theme)
        if active_source_id is not None:
            config = self.theme.load()
            config.wallpaper.sources[active_source_id].active_index = index
            config.save()

    def get_wallpaper(self, index=None):
        sources = get_source_list(self.theme)
        if not sources:
            return
        if index is None:
            index = self.get_active_wall_id()
        if index is not None:
            active_source_id = get_active_source_id(self.theme)
            if active_source_id is not None:

                source = sources[active_source_id]
                wallpaper = self.wallpaper_dir
                if source.group:
                    wallpaper = os.path.join(wallpaper, source.group)
                if source.collection:
                    wallpaper = os.path.join(wallpaper, source.collection)
                wallpaper = os.path.join(wallpaper, source.wallpapers[index])

                return wallpaper
        return

    def set_wallpaper(self, index=None, screen_lock_background=False, notify=False):
        """Set the wallpaper for the given index."""
        if index is None:
            index = self.get_active_wall_id()
        if index is not None:
            wallpaper = self.get_wallpaper(index=index)
            sources = get_source_list(self.theme)
            active_source_id = get_active_source_id(self.theme)
            if active_source_id is None:
                logger.error(
                    f"Error: Failed to set wallpaper. active_source_id is None."
                )
                return
            file_name = sources[active_source_id].wallpapers[index]
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
        sources = get_source_list(self.theme)  # Returns the dictionary of sources
        active_source_id = get_active_source_id(self.theme)
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
        switch_next_source(self.theme)
        self.update_text()

        # If a timer is running, cancel it and start a new one
        if self.update_wall_timer and self.update_wall_timer.is_alive():
            self.update_wall_timer.cancel()

        self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
        self.update_wall_timer.start()

    def prev_source(self):
        switch_prev_source(self.theme)
        self.update_text()

        # If a timer is running, cancel it and start a new one
        if self.update_wall_timer and self.update_wall_timer.is_alive():
            self.update_wall_timer.cancel()

        self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
        self.update_wall_timer.start()

    def next_wallpaper(self):
        """Set the next wallpaper."""
        active_source_id = get_active_source_id(self.theme)
        if active_source_id is None:
            logger.error(f"Error: Failed to set wallpaper. active_source_id is None.")

            return
        active_wall_id = self.get_active_wall_id()
        sources = get_source_list(self.theme)
        if active_wall_id is not None:
            next_index = (active_wall_id + 1) % len(
                sources[active_source_id].wallpapers
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
        active_source_id = get_active_source_id(self.theme)
        if active_source_id is None:
            logger.error(f"Error: Failed to set wallpaper. active_source_id is None.")

            return
        active_wall_id = self.get_active_wall_id()
        sources = get_source_list(self.theme)
        if active_wall_id is not None:
            prev_index = (active_wall_id - 1) % len(
                sources[active_source_id].wallpapers
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
        send_notification(
            "Applying Pywal Theme",
            msg="Theme Manager",
            app_name="ThemeManager",
            app_id=2003,
            timeout=5000,
        )
        wallpaper = self.get_wallpaper()
        if wallpaper:
            subprocess.run(["wal", "-i", wallpaper])
            self.notify_theme("pywal_changer")
            send_notification(
                "Applied Pywal Theme",
                msg="Theme Manager",
                app_name="ThemeManager",
                app_id=2003,
                timeout=5000,
            )
