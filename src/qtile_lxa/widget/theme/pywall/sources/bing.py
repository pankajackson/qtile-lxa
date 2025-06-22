import requests
from libqtile.log_utils import logger
from pathlib import Path
from .utils import (
    get_potd_directories,
    get_source_list,
    get_active_source_id,
    sync_config_for_source,
)
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.utils.process_lock import ProcessLocker


class Bing:
    def __init__(
        self,
        wallpaper_dir: Path,
        theme_config: ThemeConfig,
        process_locker: ProcessLocker = ProcessLocker("bing"),
    ):
        self.wallpaper_dir = wallpaper_dir
        self.theme_config = theme_config
        self.process_locker = process_locker

    def sync_bing(self):
        image_path, potd_path, date_dir, potd_dir = get_potd_directories(
            self.wallpaper_dir, "bing"
        )
        if image_path.exists():
            return
        self.download_bing_potd()
        source_list = get_source_list(theme_config=self.theme_config)
        active_source_id = get_active_source_id(theme_config=self.theme_config)
        # if active_source_id is not None:
        #     source = source_list[get_active_source_id(theme_config=self.theme_config)]
        #     if source["group"] == "bing" and source["collection"] == "PictureOfTheDay":
        #         self.set_wallpaper(screen_lock_background=True, notify=True)

    def download_bing_potd(self, resolution="WidescreenHD"):
        """Download the Bing Picture of the Day."""

        def _fetch_bing_metadata(bing_api_url):
            """Fetch metadata from the Bing API."""
            response = requests.get(bing_api_url)
            response.raise_for_status()
            return response.json()["images"][0]

        def _construct_bing_image_url(image_info, resolution, fallback_resolution):
            """Construct the image URL based on resolution."""
            image_url_base = "https://www.bing.com" + image_info["urlbase"]
            image_url = f"{image_url_base}_{resolution}.jpg"
            image_fallback_url = f"{image_url_base}_{fallback_resolution}.jpg"
            return image_url, image_fallback_url

        def _save_bing_image(
            image_url, image_fallback_url, image_path: Path, potd_path: Path
        ):
            """Download and save the image, create symlink for POTD."""
            try:
                image_response = requests.get(image_url)
                if image_response.status_code == 404:
                    logger.warning(
                        f"Image not available at resolution, falling back to standard resolution."
                    )
                    image_response = requests.get(image_fallback_url)

                image_response.raise_for_status()

                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                logger.info(f"Image saved as {image_path}")

                # Create/update symlink
                if potd_path.exists():
                    # os.remove(potd_path) # Update
                    potd_path.unlink()
                # os.symlink(image_path, potd_path) # Update
                potd_path.symlink_to(image_path)
                logger.info(f"Symlink updated: {potd_path}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download image: {e}")
                return None

        lock_fd = self.process_locker.acquire_lock()
        if not lock_fd:
            return

        try:
            BING_API_URL = (
                "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
            )
            available_resolutions = {
                "UHD": "UHD",
                "4K": "UHD",
                "FullHD": "1920x1080",
                "HD": "1280x720",
                "WidescreenHD": "1366x768",
                "MobileHD": "720x1280",
                "MobileFHD": "1080x1920",
            }

            # Validate resolution
            if resolution not in available_resolutions:
                logger.error(
                    f"Resolution label '{resolution}' is not valid. "
                    f"Available options are: {list(available_resolutions.keys())}"
                )
                return None

            # Directories and paths
            image_path, potd_path, date_dir, potd_dir = get_potd_directories(
                self.wallpaper_dir, "bing"
            )

            # Check if the image already exists
            if image_path.exists():
                logger.info("Bing POTD already exists.")
                return image_path

            try:
                # Fetch metadata and construct URLs
                image_info = _fetch_bing_metadata(BING_API_URL)
                resolution = available_resolutions[resolution]
                image_url, image_fallback_url = _construct_bing_image_url(
                    image_info, resolution, "1920x1080"
                )

                # Save the image and update symlink
                _save_bing_image(image_url, image_fallback_url, image_path, potd_path)
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
                logger.error(f"Failed to download Bing POTD: {e}")
                return None
        finally:
            self.process_locker.release_lock(lock_fd)
