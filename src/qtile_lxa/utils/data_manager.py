from pathlib import Path
import shutil
import filecmp


def sync_dirs(source: Path, target: Path, hard_sync: bool = False) -> None:
    """
    Recursively sync source directory into target directory.

    :param source: Source directory as Path
    :param target: Target directory as Path
    :param hard_sync: If True, delete extra files/dirs in target not present in source
    """
    if not source.is_dir():
        raise ValueError(f"Source is not a directory: {source}")

    target.mkdir(parents=True, exist_ok=True)

    source_entries = {entry.name: entry for entry in source.iterdir()}
    target_entries = {entry.name: entry for entry in target.iterdir()}

    # If hard_sync is True, delete items in target that aren't in source
    if hard_sync:
        for name in target_entries.keys() - source_entries.keys():
            target_entry = target_entries[name]
            if target_entry.is_dir():
                shutil.rmtree(target_entry)
            else:
                target_entry.unlink()

    # Add or update entries from source
    for name, source_entry in source_entries.items():
        target_entry = target / name

        if source_entry.is_dir():
            sync_dirs(source_entry, target_entry, hard_sync=hard_sync)
        else:
            # Only copy if file doesn't exist or is different
            if not target_entry.exists() or not filecmp.cmp(
                source_entry, target_entry, shallow=False
            ):
                shutil.copy2(source_entry, target_entry)
