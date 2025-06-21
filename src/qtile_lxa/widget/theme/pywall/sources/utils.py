import os
from datetime import datetime
from pathlib import Path
import hashlib
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.utils.notification import send_notification


def get_potd_directories(wallpaper_dir: Path, provider: str):
    potd_dir = wallpaper_dir / provider / "PictureOfTheDay"
    date_dir = (
        wallpaper_dir
        / provider
        / datetime.now().strftime("%Y")
        / datetime.now().strftime("%m")
    )

    os.makedirs(potd_dir, exist_ok=True)
    os.makedirs(date_dir, exist_ok=True)

    image_path = date_dir / f"{datetime.now().strftime('%d')}.jpg"
    potd_path = potd_dir / "current.jpg"
    return image_path, potd_path, date_dir, potd_dir


def get_source_list(theme_config: ThemeConfig):
    config = theme_config.load_config()
    sources = config.get("wallpaper", {}).get("sources", {})
    return sources


def set_active_source_id(theme_config: ThemeConfig, source_id):
    """Save the current source ID."""
    if source_id is not None:
        config = theme_config.load_config()
        sources = get_source_list(theme_config)
        if not sources:
            return
        config["wallpaper"]["source_id"] = source_id
        theme_config.save_config(config)
        source = sources[source_id]
        group = source["group"]
        collection = source["collection"]
        send_notification(
            f"Collection Changed: ",
            f"{collection}\n{group}",
            app_name="Wallpaper",
            app_id=9998,
            timeout=5000,
        )


def get_active_source_id(theme_config: ThemeConfig):
    """Get the current source ID."""
    config = theme_config.load_config()
    sources = get_source_list(theme_config)
    if not sources:
        return
    active_source_id = config.get("wallpaper", {}).get("source_id", None)
    if active_source_id is None:
        source_ids = list(sources.keys())  # Get a list of source IDs
        first_src_id = source_ids[0]
        set_active_source_id(theme_config, first_src_id)
        return first_src_id
    return active_source_id


def sync_config_for_source(
    theme_config: ThemeConfig, wallpaper_dir: Path, data_dir=None
):
    """Get the list of wallpaper files and parse source information."""
    config = theme_config.load_config()
    sources = get_source_list(theme_config)

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
                    relative_path = os.path.relpath(entry.path, wallpaper_dir)
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

    scan_directory(data_dir if data_dir else wallpaper_dir)

    config["wallpaper"]["sources"] = sources
    theme_config.save_config(config)
    return sources


def switch_next_source(theme_config: ThemeConfig):
    active_source_id = get_active_source_id(theme_config)
    sources = get_source_list(theme_config)  # Returns the dictionary of sources

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
    set_active_source_id(theme_config, next_src_id)
    # self.update_text()

    # # If a timer is running, cancel it and start a new one
    # if self.update_wall_timer and self.update_wall_timer.is_alive():
    #     self.update_wall_timer.cancel()

    # self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
    # self.update_wall_timer.start()


def switch_prev_source(theme_config: ThemeConfig):
    active_source_id = get_active_source_id(theme_config)
    sources = get_source_list(theme_config)  # Returns the dictionary of sources

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
    set_active_source_id(theme_config, next_src_id)
    # self.update_text()

    # # If a timer is running, cancel it and start a new one
    # if self.update_wall_timer and self.update_wall_timer.is_alive():
    #     self.update_wall_timer.cancel()

    # self.update_wall_timer = threading.Timer(0.5, self.set_wallpaper)
    # self.update_wall_timer.start()
