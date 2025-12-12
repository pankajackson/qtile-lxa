import subprocess
from pathlib import Path
from libqtile.log_utils import logger
from qtile_lxa.widget.theme.config import ThemeConfig
from qtile_lxa.utils.notification import send_notification
from qtile_lxa.utils.process_lock import ProcessLocker
from .utils import sync_config_for_source


class Git:
    def __init__(
        self,
        wallpaper_dir: Path,
        theme_config: ThemeConfig,
        wallpaper_repos: list[str] = ["https://github.com/pankajackson/wallpapers.git"],
        process_locker: ProcessLocker = ProcessLocker("git"),
    ):
        self.wallpaper_dir = wallpaper_dir
        self.theme_config = theme_config
        self.wallpaper_repos = wallpaper_repos
        self.process_locker = process_locker

    def sync_git(self):
        self.download_git_wallpaper_repos()

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
                    send_notification(
                        "Wallpaper Download",
                        "Internet connectivity issue detected.",
                        app_name="Wallpaper",
                        app_id=9998,
                        timeout=5000,
                    )
                else:
                    send_notification(
                        "Wallpaper Download",
                        f"Repository URL not accessible: {repo_url}\nError: {error_message}",
                        app_name="Wallpaper",
                        app_id=9998,
                        timeout=5000,
                    )
                return False

        def _clone_repo(repo_url: str, git_clone_dir: Path, progress_message: str):
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
                            send_notification(
                                title="Downloading Wallpapers",
                                msg=progress_message,
                                progress=percentage,
                                app_name="Wallpaper",
                                app_id=9999,
                                timeout=5000,
                            )
                git_clone_process.wait()
                send_notification(
                    "Wallpaper Download",
                    f"Wallpapers downloaded successfully!\n{repo_url}",
                    app_name="Wallpaper",
                    app_id=9998,
                    timeout=5000,
                )
                return True
            except subprocess.CalledProcessError:
                send_notification(
                    "Wallpaper Download",
                    f"Error cloning repo!\n{repo_url}",
                    app_name="Wallpaper",
                    app_id=9998,
                    timeout=5000,
                )
                return False

        def _detect_git_changes(git_clone_dir: Path):
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
                send_notification(
                    "Wallpaper Download",
                    f"Invalid repo URL: {repo_url}",
                    app_name="Wallpaper",
                    app_id=9998,
                    timeout=5000,
                )
                return "unknown_user", "unknown_repo"

        lock_fd = self.process_locker.acquire_lock()
        if not lock_fd:
            return

        try:

            if not self.wallpaper_repos:
                send_notification(
                    "Download Failed",
                    "Repo list empty, Wallpaper Download Failed...",
                    app_name="Wallpaper",
                    app_id=9998,
                    timeout=5000,
                )
                return

            self.wallpaper_dir.mkdir(parents=True, exist_ok=True)
            any_repo_cloned_or_updated = False

            for repo_index, repo_url in enumerate(self.wallpaper_repos, start=1):
                if not _is_git_repo_accessible(repo_url):
                    continue

                github_user, repo_name = _extract_github_info(repo_url)
                progress_message = f"{github_user}/{repo_name}... ({repo_index}/{len(self.wallpaper_repos)})"
                git_clone_dir = self.wallpaper_dir / f"{github_user}/{repo_name}"

                if git_clone_dir.exists():
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
                            sync_config_for_source(
                                theme_config=self.theme_config,
                                wallpaper_dir=self.wallpaper_dir,
                                data_dir=git_clone_dir,
                            )
                            any_repo_cloned_or_updated = True
                    except subprocess.CalledProcessError:
                        # Not a valid Git repo, delete and clone
                        subprocess.run(["rm", "-rf", git_clone_dir])
                        if _clone_repo(repo_url, git_clone_dir, progress_message):
                            sync_config_for_source(
                                theme_config=self.theme_config,
                                wallpaper_dir=self.wallpaper_dir,
                                data_dir=git_clone_dir,
                            )
                            any_repo_cloned_or_updated = True
                else:
                    # Directory does not exist, clone the repo
                    if _clone_repo(repo_url, git_clone_dir, progress_message):
                        sync_config_for_source(
                            theme_config=self.theme_config,
                            wallpaper_dir=self.wallpaper_dir,
                            data_dir=git_clone_dir,
                        )
                        any_repo_cloned_or_updated = True

            if any_repo_cloned_or_updated:
                send_notification(
                    "Wallpaper Download",
                    "Downloading Wallpapers Finished!",
                    app_name="Wallpaper",
                    app_id=9998,
                    timeout=5000,
                )
        finally:
            self.process_locker.release_lock(lock_fd)
