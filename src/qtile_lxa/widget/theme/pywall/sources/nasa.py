import requests
from pathlib import Path
from libqtile.log_utils import logger
from .utils import (
    get_potd_directories,
    get_source_list,
    get_active_source_id,
    sync_config_for_source,
)
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.utils.process_lock import ProcessLocker


class Nasa:
    def __init__(
        self,
        wallpaper_dir: Path,
        theme_config: ThemeConfig,
        process_locker: ProcessLocker = ProcessLocker("nasa"),
        nasa_api_key="hETQq0FPsZJnUP9C3sUEFtwmJH3edb4I5bghfWDM",
    ):
        self.wallpaper_dir = wallpaper_dir
        self.theme_config = theme_config
        self.process_locker = process_locker
        self.nasa_api_key = nasa_api_key

    def sync_nasa(self):
        image_path, potd_path, date_dir, potd_dir = get_potd_directories(
            self.wallpaper_dir, "nasa"
        )
        if image_path.exists():
            return
        self.download_nasa_apod()
        source_list = get_source_list(self.theme_config)
        active_source_id = get_active_source_id(self.theme_config)
        # if active_source_id is not None:
        #     source = source_list[self.get_active_source_id()]
        #     if source["group"] == "nasa" and source["collection"] == "PictureOfTheDay":
        #         self.set_wallpaper(screen_lock_background=True, notify=True)

    def download_nasa_apod(self):
        """Download NASA's Astronomy Picture of the Day (APOD)."""
        NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

        def _fetch_apod_metadata(api_url, api_key=None):
            """Fetch metadata from NASA APOD API."""
            params = {}
            if api_key:  # Include API key only if provided
                params["api_key"] = api_key
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            return response.json()

        def _save_apod_image(image_url, image_path, potd_path):
            """Download and save the image, create symlink for POTD."""
            try:
                image_response = requests.get(image_url)
                image_response.raise_for_status()

                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                logger.info(f"Image saved as {image_path}")

                # Create/update symlink
                if potd_path.exists():
                    potd_path.unlink()
                potd_path.symlink_to(image_path)
                logger.info(f"Symlink updated: {potd_path}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download image: {e}")
                return None

        lock_fd = self.process_locker.acquire_lock()
        if not lock_fd:
            return

        try:

            # Directories and paths
            image_path, potd_path, date_dir, potd_dir = get_potd_directories(
                self.wallpaper_dir, "nasa"
            )

            # Check if the image already exists
            if image_path.exists():
                logger.info("NASA APOD already exists.")
                return image_path

            try:
                # Fetch metadata
                apod_metadata = _fetch_apod_metadata(NASA_APOD_URL, self.nasa_api_key)

                # Check if today's APOD is an image (not a video)
                if "hdurl" not in apod_metadata:
                    logger.warning("Today's APOD is not an image.")
                    return None

                # Save the image and update symlink
                _save_apod_image(apod_metadata["hdurl"], image_path, potd_path)
                sync_config_for_source(
                    theme_config=self.theme_config,
                    wallpaper_dir=self.wallpaper_dir,
                    data_dir=date_dir,
                )
                sync_config_for_source(
                    theme_config=self.theme_config,
                    wallpaper_dir=self.wallpaper_dir,
                    data_dir=potd_dir,
                )

                return image_path

            except Exception as e:
                logger.error(f"Failed to download NASA APOD: {e}")
                return None
        finally:
            self.process_locker.release_lock(lock_fd)
