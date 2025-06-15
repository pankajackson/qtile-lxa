import os
import subprocess
import threading
import fcntl
import requests
import hashlib
from pathlib import Path
from qtile_extras import widget
from libqtile import qtile
from libqtile.log_utils import logger
from datetime import datetime
from ..Config import ThemeConfig

theme_config = ThemeConfig(config_file=Path.home() / "theme_config.json")


class PyWallChanger(widget.GenPollText):
    def __init__(
        self,
        wallpaper_dir=Path.home() / "Pictures/desktop_backgrounds",
        update_screenlock=False,
        screenlock_effect="blur",
        wallpaper_repos=["https://github.com/pankajackson/wallpapers.git"],
        lock_dir="/tmp",
        bing_potd=True,
        nasa_potd=True,
        nasa_api_key="hETQq0FPsZJnUP9C3sUEFtwmJH3edb4I5bghfWDM",
        **config,
    ):
        super().__init__(**config)
        self.wallpaper_dir = wallpaper_dir
        self.update_screenlock = update_screenlock
        self.screenlock_effect = screenlock_effect
        self.wallpaper_repos = wallpaper_repos or []
        self.lock_dir = lock_dir
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
        self.sync_config_for_source()
        self.set_wallpaper()
        self.update_text()

    def poll(self):
        self.sync_sources()
        return self.get_text()

    def acquire_lock(self, provider):
        """Acquire a lock using a specific lock file."""
        lock_file = os.path.join(self.lock_dir, f"{provider}.lock")
        if not os.path.exists(lock_file):
            # Ensure the lock file exists
            open(lock_file, "a").close()

        lock_fd = open(lock_file, "r+")
        try:
            # Acquire an exclusive lock
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_fd
        except BlockingIOError:
            logger.error(
                f"Process Locked, Another instance is running for {lock_file}."
            )
            return None

    def release_lock(self, lock_fd):
        """Release the lock."""
        if lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    def sync_bing(self):
        image_path, potd_path, date_dir, potd_dir = self.get_potd_directories("bing")
        if os.path.exists(image_path):
            return
        self.download_bing_potd()
        source_list = self.get_source_list()
        active_source_id = self.get_active_source_id()
        if active_source_id is not None:
            source = source_list[self.get_active_source_id()]
            if source["group"] == "bing" and source["collection"] == "PictureOfTheDay":
                self.set_wallpaper(screen_lock_background=True, notify=True)

    def sync_nasa(self):
        image_path, potd_path, date_dir, potd_dir = self.get_potd_directories("nasa")
        if os.path.exists(image_path):
            return
        self.download_nasa_apod()
        source_list = self.get_source_list()
        active_source_id = self.get_active_source_id()
        if active_source_id is not None:
            source = source_list[self.get_active_source_id()]
            if source["group"] == "nasa" and source["collection"] == "PictureOfTheDay":
                self.set_wallpaper(screen_lock_background=True, notify=True)

    def sync_git(self):
        self.download_git_wallpaper_repos()

    def sync_sources(self):
        lock_fd = self.acquire_lock("sync_sources")
        if not lock_fd:
            return
        try:
            active_source_id = self.get_active_source_id()

            self.sync_git()

            if self.bing_potd:
                self.sync_bing()

            if self.nasa_potd:
                self.sync_nasa()
            source_list = self.get_source_list()
            if source_list and active_source_id is None:
                self.set_wallpaper(screen_lock_background=True, notify=True)
        finally:
            self.release_lock(lock_fd=lock_fd)

    def get_potd_directories(self, provider):
        potd_dir = os.path.join(self.wallpaper_dir, provider, "PictureOfTheDay")
        date_dir = os.path.join(
            self.wallpaper_dir,
            provider,
            datetime.now().strftime("%Y"),
            datetime.now().strftime("%m"),
        )
        os.makedirs(potd_dir, exist_ok=True)
        os.makedirs(date_dir, exist_ok=True)

        image_path = os.path.join(date_dir, f"{datetime.now().strftime('%d')}.jpg")
        potd_path = os.path.join(potd_dir, "current.jpg")
        return image_path, potd_path, date_dir, potd_dir

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

        def _save_bing_image(image_url, image_fallback_url, image_path, potd_path):
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
                if os.path.exists(potd_path):
                    os.remove(potd_path)
                os.symlink(image_path, potd_path)
                logger.info(f"Symlink updated: {potd_path}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download image: {e}")
                return None

        lock_fd = self.acquire_lock("bing")
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
            image_path, potd_path, date_dir, potd_dir = self.get_potd_directories(
                "bing"
            )

            # Check if the image already exists
            if os.path.exists(image_path):
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
                self.sync_config_for_source(date_dir)
                self.sync_config_for_source(potd_dir)

                return image_path

            except Exception as e:
                logger.error(f"Failed to download Bing POTD: {e}")
                return None
        finally:
            self.release_lock(lock_fd)

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
                if os.path.exists(potd_path):
                    os.remove(potd_path)
                os.symlink(image_path, potd_path)
                logger.info(f"Symlink updated: {potd_path}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download image: {e}")
                return None

        lock_fd = self.acquire_lock("nasa")
        if not lock_fd:
            return

        try:

            # Directories and paths
            image_path, potd_path, date_dir, potd_dir = self.get_potd_directories(
                "nasa"
            )

            # Check if the image already exists
            if os.path.exists(image_path):
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
                self.sync_config_for_source(date_dir)
                self.sync_config_for_source(potd_dir)

                return image_path

            except Exception as e:
                logger.error(f"Failed to download NASA APOD: {e}")
                return None
        finally:
            self.release_lock(lock_fd)

    def download_git_wallpaper_repos(self):
        """Download wallpapers using a thread-safe lock with fcntl."""

        def _is_git_repo_accessible(repo_url):
            """Check if the Git repository URL is accessible."""
            try:
                subprocess.run(
                    ["git", "ls-remote", repo_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,  # Capture stderr
                    check=True,
                )
                return True
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.decode("utf-8").strip()
                if (
                    "Could not resolve host" in error_message
                    or "Connection timed out" in error_message
                ):
                    self._send_notification(
                        "Wallpaper Download", "Internet connectivity issue detected."
                    )
                else:
                    self._send_notification(
                        "Wallpaper Download",
                        f"Repository URL not accessible: {repo_url}\nError: {error_message}",
                    )
                return False

        def _clone_repo(repo_url, git_clone_dir, progress_message):
            """Clone the repository with shallow depth and send progress notifications."""
            try:
                git_clone_process = subprocess.Popen(
                    [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        "--progress",
                        repo_url,
                        git_clone_dir,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                if git_clone_process.stdout is not None:
                    for line in git_clone_process.stdout:
                        if "Receiving objects:" in line:
                            percentage = int(line.split("%")[0].split()[-1])
                            self._send_progress_notification(
                                title="Downloading Wallpapers",
                                msg=progress_message,
                                progress=percentage,
                            )
                git_clone_process.wait()
                self._send_notification(
                    "Wallpaper Download",
                    f"Wallpapers downloaded successfully!\n{repo_url}",
                )
                return True
            except subprocess.CalledProcessError:
                self._send_notification(
                    "Wallpaper Download", f"Error cloning repo!\n{repo_url}"
                )
                return False

        def _detect_git_changes(git_clone_dir):
            """Detect if there are any updates in a shallow-cloned repository."""
            try:
                pull_output = subprocess.check_output(
                    ["git", "-C", git_clone_dir, "pull", "--depth", "1", "--rebase"],
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                if "Already up to date" in pull_output:
                    return False  # No updates
                return True  # Updates found and pulled
            except subprocess.CalledProcessError:
                # Assume changes if we cannot pull
                return True

        def _extract_github_info(repo_url):
            """
            Extract the GitHub username and repository name from the repository URL.
            Returns (username, repository).
            """
            try:
                parts = repo_url.rstrip("/").split("/")
                github_user = parts[-2]
                repo_name = parts[-1].replace(".git", "")
                if not github_user or not repo_name:
                    raise ValueError("Invalid GitHub URL")
                return github_user, repo_name
            except (IndexError, ValueError) as e:
                self._send_notification(
                    "Wallpaper Download", f"Invalid repo URL: {repo_url}"
                )
                return "unknown_user", "unknown_repo"

        lock_fd = self.acquire_lock("git")
        if not lock_fd:
            return

        try:

            if not self.wallpaper_repos:
                self._send_notification(
                    "Download Failed",
                    "Repo list empty, Wallpaper Download Failed...",
                )
                return

            os.makedirs(self.wallpaper_dir, exist_ok=True)
            any_repo_cloned_or_updated = False

            for repo_index, repo_url in enumerate(self.wallpaper_repos, start=1):
                if not _is_git_repo_accessible(repo_url):
                    continue

                github_user, repo_name = _extract_github_info(repo_url)
                progress_message = f"{github_user}/{repo_name}... ({repo_index}/{len(self.wallpaper_repos)})"
                git_clone_dir = os.path.join(
                    self.wallpaper_dir, f"{github_user}/{repo_name}"
                )

                if os.path.exists(git_clone_dir):
                    # Check if it's a Git repo
                    try:
                        subprocess.run(
                            ["git", "-C", git_clone_dir, "status"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True,
                        )
                        # Check for remote changes
                        if _detect_git_changes(git_clone_dir):
                            # Pull latest changes
                            subprocess.run(
                                ["git", "-C", git_clone_dir, "reset", "--hard"],
                                check=True,
                            )
                            subprocess.run(
                                ["git", "-C", git_clone_dir, "pull", "--rebase"],
                                check=True,
                            )
                            self.sync_config_for_source(git_clone_dir)
                            any_repo_cloned_or_updated = True
                    except subprocess.CalledProcessError:
                        # Not a valid Git repo, delete and clone
                        subprocess.run(["rm", "-rf", git_clone_dir])
                        if _clone_repo(repo_url, git_clone_dir, progress_message):
                            self.sync_config_for_source(git_clone_dir)
                            any_repo_cloned_or_updated = True
                else:
                    # Directory does not exist, clone the repo
                    if _clone_repo(repo_url, git_clone_dir, progress_message):
                        self.sync_config_for_source(git_clone_dir)
                        any_repo_cloned_or_updated = True

            if any_repo_cloned_or_updated:
                self._send_notification(
                    "Wallpaper Download", "Downloading Wallpapers Finished!"
                )
        finally:
            self.release_lock(lock_fd)

    def _send_notification(self, title, msg):
        """Send a notification."""
        subprocess.run(
            [
                "dunstify",
                "-a",
                "Wallpaper",
                "-r",
                "9998",
                title,
                msg,
                "-t",
                "5000",
            ],
            check=True,
        )

    def _send_progress_notification(self, title, msg, progress):
        """Send a progress notification with a progress bar."""
        subprocess.run(
            [
                "dunstify",
                "-a",
                "Wallpaper",
                "-r",
                "9999",
                "-h",
                f"int:value:{progress}",
                f"{title}: {progress}%",
                msg,
                "-t",
                "5000",
            ],
            check=True,
        )

    def sync_config_for_source(self, data_dir=None):
        """Get the list of wallpaper files and parse source information."""
        config = theme_config.load_config()
        sources = self.get_source_list()

        def get_uid(group=None, collection=None, none_marker="NONE"):
            """
            Generate a unique ID based on group and collection.
            """
            group = group if group else none_marker
            collection = collection if collection else none_marker

            # Generate ID using group and collection
            base_id_source = f"{group}:{collection}"
            unique_id = hashlib.md5(base_id_source.encode()).hexdigest()[:8]
            return unique_id

        def parse_source_info(relative_path):
            """
            Parse the source info (group, collection) from the relative path and generate a unique ID.
            The unique ID is based on the group and collection.
            """

            # Parse the relative path
            parts = relative_path.split(os.sep)
            if len(parts) == 1:  # Wallpaper directly in wallpaper_dir
                group, collection, filename = None, None, parts[-1]
            elif len(parts) == 2:  # Wallpaper in a group directory
                group, collection, filename = parts[0], None, parts[-1]
            else:  # Wallpaper in deeper directories
                group, collection, filename = parts[0], "/".join(parts[1:-1]), parts[-1]

            # Generate the unique ID
            unique_id = get_uid(group=group, collection=collection)
            return unique_id, group, collection, filename

        def scan_directory(directory):
            """Recursively scan directories for wallpaper files."""
            if not os.path.exists(directory):
                return
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.lower().endswith(
                        (".jpg", ".jpeg", ".png")
                    ):
                        relative_path = os.path.relpath(entry.path, self.wallpaper_dir)
                        id, group, collection, wallpaper_file_name = parse_source_info(
                            relative_path
                        )
                        src = sources.get(
                            id,
                            {
                                "group": group,
                                "collection": collection,
                                "active_index": 0,
                                "wallpapers": [],
                            },
                        )
                        if wallpaper_file_name not in src["wallpapers"]:
                            src["wallpapers"].append(wallpaper_file_name)
                        sources[id] = src

                    elif entry.is_dir():
                        scan_directory(entry.path)

        scan_directory(data_dir if data_dir else self.wallpaper_dir)

        config["wallpaper"]["sources"] = sources
        theme_config.save_config(config)
        return sources

    def get_source_list(self):
        config = theme_config.load_config()
        sources = config.get("wallpaper", {}).get("sources", {})
        return sources

    def get_active_source_id(self):
        """Get the current source ID."""
        config = theme_config.load_config()
        sources = self.get_source_list()
        if not sources:
            return
        active_source_id = config.get("wallpaper", {}).get("source_id", None)
        if active_source_id is None:
            source_ids = list(sources.keys())  # Get a list of source IDs
            first_src_id = source_ids[0]
            self.set_active_source_id(first_src_id)
            return first_src_id
        return active_source_id

    def set_active_source_id(self, source_id):
        """Save the current source ID."""
        if source_id is not None:
            config = theme_config.load_config()
            sources = self.get_source_list()
            if not sources:
                return
            config["wallpaper"]["source_id"] = source_id
            theme_config.save_config(config)
            source = sources[source_id]
            group = source["group"]
            collection = source["collection"]
            self._send_notification(f"Collection Changed: ", f"{collection}\n{group}")

    def get_active_wall_id(self):
        """Get the current wallpaper index."""
        active_source_id = self.get_active_source_id()
        if active_source_id is not None:
            return theme_config.load_config()["wallpaper"]["sources"][active_source_id][
                "active_index"
            ]
        return None

    def set_active_wall_id(self, index):
        """Save the current wallpaper index."""
        active_source_id = self.get_active_source_id()
        if active_source_id is not None:
            config = theme_config.load_config()
            config["wallpaper"]["sources"][active_source_id]["active_index"] = index
            theme_config.save_config(config)

    def get_wallpaper(self, index=None):
        sources = self.get_source_list()
        if not sources:
            return
        if index is None:
            index = self.get_active_wall_id()
        if index is not None:
            active_source_id = self.get_active_source_id()
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
            sources = self.get_source_list()
            active_source_id = self.get_active_source_id()
            file_name = sources[active_source_id]["wallpapers"][index]
            if wallpaper:
                try:
                    if not os.path.isfile(wallpaper):
                        raise FileNotFoundError(f"Wallpaper not found: {wallpaper}")
                    subprocess.run(["feh", "--bg-scale", wallpaper], check=True)
                    if notify:
                        self._send_notification("Wallpaper Changed", file_name)
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
                    self._send_notification("Wallpaper Changed", f"Error: {e}")
                    logger.error(f"Error: {e}")
                except subprocess.CalledProcessError as e:
                    self._send_notification(
                        "Wallpaper Changed",
                        f"Error: Failed to set wallpaper. Command exited with status {e.returncode}.",
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
            subprocess.run(
                [
                    "dunstify",
                    "-a",
                    "ScreenLock",
                    "-r",
                    "9995",
                    "ScreenLock",
                    "ScreenLock Background has been updated!",
                    "-t",
                    "5000",
                ],
                check=True,
            )

    def get_text(self):
        """Build the text that displays the current wallpaper index."""
        sources = self.get_source_list()  # Returns the dictionary of sources
        active_source_id = self.get_active_source_id()
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
        active_source_id = self.get_active_source_id()
        sources = self.get_source_list()  # Returns the dictionary of sources

        if not sources:
            return  # Exit if there are no sources available

        source_ids = list(sources.keys())  # Get a list of source IDs
        first_src_id = source_ids[0]  # First source ID in the list

        if active_source_id is None or active_source_id not in sources:
            # If no active source or the current source is invalid, set the first source
            next_src_id = first_src_id
        else:
            # Find the index of the current source and move to the next
            current_index = source_ids.index(active_source_id)
            next_index = (current_index + 1) % len(source_ids)  # Wrap around
            next_src_id = source_ids[next_index]

        # Update the current source
        self.set_active_source_id(next_src_id)
        self.update_text()

        # If a timer is running, cancel it and start a new one
        if self.update_wall_timer and self.update_wall_timer.is_alive():
            self.update_wall_timer.cancel()

        self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
        self.update_wall_timer.start()

    def prev_source(self):
        active_source_id = self.get_active_source_id()
        sources = self.get_source_list()  # Returns the dictionary of sources

        if not sources:
            return  # Exit if there are no sources available

        source_ids = list(sources.keys())  # Get a list of source IDs
        first_src_id = source_ids[0]  # First source ID in the list

        if active_source_id is None or active_source_id not in sources:
            # If no active source or the current source is invalid, set the first source
            next_src_id = first_src_id
        else:
            # Find the index of the current source and move to the next
            current_index = source_ids.index(active_source_id)
            next_index = (current_index - 1) % len(source_ids)  # Wrap around
            next_src_id = source_ids[next_index]

        # Update the current source
        self.set_active_source_id(next_src_id)
        self.update_text()

        # If a timer is running, cancel it and start a new one
        if self.update_wall_timer and self.update_wall_timer.is_alive():
            self.update_wall_timer.cancel()

        self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
        self.update_wall_timer.start()

    def next_wallpaper(self):
        """Set the next wallpaper."""
        active_source_id = self.get_active_source_id()
        active_wall_id = self.get_active_wall_id()
        sources = self.get_source_list()
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
        active_source_id = self.get_active_source_id()
        active_wall_id = self.get_active_wall_id()
        sources = self.get_source_list()
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
