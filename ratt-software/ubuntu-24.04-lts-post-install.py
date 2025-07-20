from abc import ABC, abstractmethod
import logging
import argparse
import os
import datetime as dt
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import json
from time import time
from enum import Enum
from typing import Any, Optional
import re
from typing import Dict, Callable

# Meta-information
TARGET_OS = "Ubuntu 24.04 LTS"
VERSION = "0.1"
LAST_MODIFIED = "19/07/2025"
AUTHORS = [("Brian Welman", "github/kwazzi-jack")]  # Name, GitHub Username

# Globals
FOUND_COMMANDS = set()
LOG_PATH: Path
LOGGER: logging.Logger

# Flags
VERBOSE: bool = False
UPGRADE: bool = True
DRY_RUN: bool = False
INTERACTIVE: bool = False
ROLLBACK: bool = False

# Compile regex patterns once at module level for better performance
MARKUP_REGEX = re.compile(r"`([^`]+)`|\[(\w+)\](.*?)\[/\2\]")
ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Pre-built formatter lookup table with lambdas (compiled once at import)
FORMATTERS: Dict[str, Callable[[str], str]] = {
    "bold": lambda text: f"\033[1m{text}\033[0m",
    "italics": lambda text: f"\033[3m{text}\033[0m",
    "underline": lambda text: f"\033[4m{text}\033[0m",
    "red": lambda text: f"\033[31m{text}\033[0m",
    "green": lambda text: f"\033[32m{text}\033[0m",
    "blue": lambda text: f"\033[34m{text}\033[0m",
    "yellow": lambda text: f"\033[33m{text}\033[0m",
    "orange": lambda text: f"\033[38;5;214m{text}\033[0m",
    "gray": lambda text: f"\033[90m{text}\033[0m",
    "white": lambda text: f"\033[37m{text}\033[0m",
}


def get_terminal_width() -> int:
    try:
        width = shutil.get_terminal_size().columns
        return width if width > 60 else 60
    except OSError:
        return 80  # fallback width


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from text"""
    return ANSI_ESCAPE_REGEX.sub("", text)


def timestamp() -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone()
    utc_offset = now.strftime("%z")
    formatted_time = now.strftime("%d/%m/%Y-%H:%M:%S")
    return FORMATTERS["gray"](f"[{formatted_time}{utc_offset}]")


def line():
    print(FORMATTERS["gray"]("=" * get_terminal_width()))


def info(message: str) -> None:
    """Print info message with formatting and log clean version"""
    print(f"{timestamp()} {message}")
    LOGGER.info(message)


def debug(message: str) -> None:
    """Print debug message with formatting and log clean version"""
    if VERBOSE:
        formatted_msg = FORMATTERS["italics"](FORMATTERS["blue"](message))
        print(f"{timestamp()} {formatted_msg}")
    LOGGER.debug(message)


def warn(message: str) -> None:
    """Print warning message with formatting and log clean version"""
    formatted_msg = FORMATTERS["bold"](FORMATTERS["yellow"](message))
    print(f"{timestamp()} {formatted_msg}")
    LOGGER.warning(message)


def error(message: str) -> None:
    """Print error message with formatting and log clean version"""
    formatted_msg = FORMATTERS["bold"](FORMATTERS["red"](message))
    print(f"{timestamp()} {formatted_msg}")
    LOGGER.error(message)


def success(message: str) -> None:
    """Print success message with formatting and log clean version"""
    formatted_msg = FORMATTERS["italics"](FORMATTERS["green"](message))
    print(f"{timestamp()} {formatted_msg}")
    LOGGER.info(message)


def show_legend():
    print(
        "Legend:",
        ",".join(
            [
                "INFO=White",
                FORMATTERS["bold"](FORMATTERS["yellow"]("WARNING=Yellow")),
                FORMATTERS["bold"](FORMATTERS["red"]("ERROR=Red")),
                FORMATTERS["italics"](FORMATTERS["blue"]("DEBUG=Blue")),
            ]
        ),
    )
    line()
    print()


def show_header():
    """Prints a formatted header with script information."""
    print()
    title = FORMATTERS["bold"](
        FORMATTERS["green"](f"RATT {TARGET_OS} Post-Install Script v{VERSION}")
    )
    line()
    print(title)
    line()

    # Meta information
    print(f"Last modified: {FORMATTERS['blue'](LAST_MODIFIED)}")
    print(
        f"\nReport issues to:\n{FORMATTERS['blue'](FORMATTERS['underline']('https://github.com/ratt-ru/baby-ratts/issues'))}\n"
    )
    print("Author(s):")
    for name, username in AUTHORS:
        print(FORMATTERS["blue"](f"- {name} ({username})"))

    # Warnings and disclaimers
    print()
    print(
        FORMATTERS["bold"](
            FORMATTERS["yellow"](
                "Caution:\n"
                "- It is strongly recommended to use\n"
                "  `--dry-run` to review changes first.\n\n"
                "- This script is provided as-is. Use \n"
                "  at your own risk.\n"
            )
        )
    )
    line()


def setup_logging():
    """Configure logging based on verbose flag"""
    global LOGGER, LOG_PATH
    now = dt.datetime.now().strftime("%d_%m_%Y-%H_%M_%S")
    LOG_PATH = Path.home() / ".logs" / f"post-install-{now}.log"
    log_dir = LOG_PATH.parent
    log_dir.mkdir(exist_ok=True)
    level = logging.DEBUG if VERBOSE else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH),
        ],
    )
    LOGGER = logging.getLogger(__name__)


def safely_shutdown():
    """Safely shutdown the application"""
    info("Safely shutting down")
    sys.exit(1)


def command_exists(cmd: str) -> bool:
    """Check whether a command is present on the system using
    the GNU `which` command. If `which` is missing, then probably
    best to reinstall your operating system.

    Args:
        cmd (str): System command to check for.

    Returns:
        bool: Whether the command exists on the system or not.

    Examples:
    >>> command_exists("python3")
    True
    >>> command_exists("nonexistent_command")
    False
    """
    # Check if previously checked
    if cmd in FOUND_COMMANDS:
        LOGGER.debug("Executable found. Previously checked")
        return True
    LOGGER.debug(f"Checking if new command {cmd} installed")
    # If dry-run, assume it is present
    if DRY_RUN and cmd not in FOUND_COMMANDS:
        FOUND_COMMANDS.add(cmd)
        LOGGER.debug("Executable found. Adding to checked (DRY RUN)")
        return True
    try:
        # Use `which` command to see if exe present
        result = subprocess.run(
            ["which", cmd], check=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            # Successfully found
            FOUND_COMMANDS.add(cmd)
            LOGGER.debug("Executable found. Adding to checked")
            return True
    except Exception:
        # Any error is assumed to be failure
        pass
    # Failed to find executable
    LOGGER.debug("Executable not found")
    return False


def confirm(text: str = "Confirm", default: str = "yes") -> bool:
    """
    Prompt the user for confirmation with yes, no, or cancel options.

    Args:
        text (str): The prompt text to display to the user.
        default (str): The default response ("yes", "no", or "cancel").

    Returns:
        bool: True if the user confirms with "yes", False if "no".

    Raises:
        ValueError: If any of the input arguments are invalid.

    Examples:
        >>> confirm("Do you want to continue?")
        Confirm [y/n/c] (default: yes): y
        True

        >>> confirm("Delete file?", default="no")
        Delete file? [y/n/c] (default: no): n
        False
    """
    # Validate input arguments
    if not text or not isinstance(text, str):
        raise ValueError("Prompt text must be a non-empty string")

    if default not in ["yes", "no", "cancel"]:
        raise ValueError("Default value must be 'yes', 'no', or 'cancel'")

    # Build the prompt message
    choices = "/".join(
        [
            f"{FORMATTERS['underline']('y')}es",
            f"{FORMATTERS['underline']('N')}o",
            f"{FORMATTERS['underline']('C')}ancel",
        ]
    )
    prompt_text = f"{text} [{choices}] (default: {default}):"
    prompt = f"{timestamp()} {prompt_text} "

    while True:
        response = input(prompt).strip().lower()

        # Use default if no input provided
        if not response:
            response = default

        # Handle single letter or whole word inputs
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        elif response in ["c", "cancel"]:
            safely_shutdown()

        # Invalid input
        error(
            "Invalid response. Please choose '', 'y/Y/yes/Yes', 'n/N/no/No', or 'c/C/cancel/Cancel'."
        )


class InstallMode(Enum):
    STANDARD = "standard"
    MINIMAL = "minimal"
    FULL = "full"
    CUSTOM = "custom"


def arguments():
    """Parse command line arguments and update global flags"""
    global VERBOSE, UPGRADE, DRY_RUN, INTERACTIVE, ROLLBACK

    parser = argparse.ArgumentParser(
        description=f"RATT {TARGET_OS} Post-Install Script v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s --dry-run --verbose standard    # Test standard install with verbose output
  %(prog)s --no-upgrade full               # Full install without package upgrades
  %(prog)s custom                          # Interactive custom installation

Report issues: https://github.com/ratt-ru/baby-ratts/issues
Authors: {', '.join([f'{name} ({username})' for name, username in AUTHORS])}
        """,
    )

    # Operational flags
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose information during installation",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run installation script without installing anything to verify everything works",
    )

    parser.add_argument(
        "--no-upgrade",
        dest="upgrade",
        action="store_false",
        default=UPGRADE,
        help="Perform various package upgrades if available (default: %(default)s)",
    )

    parser.add_argument(
        "mode",
        choices=[mode.value for mode in InstallMode],
        default=InstallMode.STANDARD.value,
        help="Installation mode: standard (default), minimal, full, or custom",
    )

    # Parse arguments
    args = parser.parse_args()

    # Update global flags
    VERBOSE = args.verbose
    UPGRADE = args.upgrade
    DRY_RUN = args.dry_run

    # Return parsed mode for use in main logic
    return InstallMode(args.mode)


class Installer(ABC):
    """Abstract base class for all installation methods."""

    def __init__(
        self,
        name: str,
        dependencies: Optional[list["SoftwarePackage"]] = None,
        version: Optional[str] = None,
    ):
        self.name = name
        self.dependencies = dependencies or []
        self.version = version
        self._installed: Optional[bool] = None

    def is_installed(self) -> bool:
        """Check if the software is installed. Caches the result."""
        if self._installed is None:
            debug(f"Checking if {self.name} is installed.")
            self._installed = self._check_installed()
            if self._installed:
                debug(f"{self.name} is installed.")
            else:
                debug(f"{self.name} is NOT installed.")
        return self._installed

    @abstractmethod
    def _check_installed(self) -> bool:
        """Subclasses must implement this to check if the software is installed."""
        raise NotImplementedError

    def install(self) -> bool:
        """Install all dependencies and then the software itself."""
        debug(f"Starting installation for {self.name}")
        if self.is_installed():
            success(f"{self.name} is already installed.")
            return True

        # Install dependencies first
        for dep in self.dependencies:
            if not dep.is_installed():
                info(f"Installing dependency for {self.name}: {dep.name}")
                if not dep.install():
                    error(f"Failed to install dependency: {dep.name}")
                    return False

        # Install the software
        info(f"Installing {self.name}...")
        if self._install_package():
            self._installed = True
            success(f"Successfully installed {self.name}")
            return True
        else:
            error(f"Failed to install {self.name}")
            return False

    @abstractmethod
    def _install_package(self) -> bool:
        """Subclasses must implement the installation logic."""
        raise NotImplementedError

    @abstractmethod
    def uninstall(self) -> bool:
        """Subclasses must implement the uninstallation logic."""
        raise NotImplementedError

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """Subclasses must implement logic to get the installed version."""
        raise NotImplementedError

    def run(self, *args: str, **kwargs: Any) -> bool:
        """
        Execute the command with given arguments.

        Args:
            *args: Command line arguments to pass to the command
            **kwargs: Additional keyword arguments (passed to subprocess.run)

        Returns:
            bool: True if command executed successfully (returncode 0), False otherwise
        """
        if not self.is_installed():
            error(f"Cannot run {self.name} as it is not installed.")
            return False

        cmd = [self.name] + list(args)
        debug(f"Running command: {' '.join(cmd)}")

        try:
            subprocess_kwargs = {
                "capture_output": kwargs.get("capture_output", False),
                "text": kwargs.get("text", True),
                "check": kwargs.get("check", False),
                "cwd": kwargs.get("cwd"),
                "env": kwargs.get("env"),
                "timeout": kwargs.get("timeout"),
            }
            # Remove None values
            subprocess_kwargs = {
                k: v for k, v in subprocess_kwargs.items() if v is not None
            }

            result = subprocess.run(cmd, **subprocess_kwargs)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            error(f"Command '{self.name}' timed out.")
            return False
        except subprocess.CalledProcessError as e:
            error(f"Command '{self.name}' failed with return code {e.returncode}.")
            return False
        except FileNotFoundError:
            error(f"Command '{self.name}' not found.")
            return False
        except Exception as e:
            error(f"An unexpected error occurred while running '{self.name}': {e}")
            return False


class SoftwarePackage:
    """Represents a piece of software that can be installed by one or more methods."""

    def __init__(self, name: str, installers: list[Installer]):
        if not installers:
            raise ValueError("A SoftwarePackage must have at least one installer.")
        self.name = name
        self.installers = installers
        self._installed_by: Optional[Installer] = None

    def is_installed(self) -> bool:
        """Check if the software is installed by any of the available installers."""
        if self._installed_by:
            return True
        for installer in self.installers:
            if installer.is_installed():
                self._installed_by = installer
                return True
        return False

    def install(self) -> bool:
        """Try to install the software using the available installers in order."""
        if self.is_installed():
            success(
                f"{self.name} is already installed (via {self._installed_by.name})."
            )
            return True

        for installer in self.installers:
            info(
                f"Attempting to install {self.name} using {installer.__class__.__name__}..."
            )
            try:
                if installer.install():
                    # Verify that the installation was successful with the method that should now work
                    if installer.is_installed():
                        self._installed_by = installer
                        success(
                            f"Successfully installed {self.name} using {installer.__class__.__name__}."
                        )
                        return True
                    else:
                        warn(
                            f"Installer {installer.__class__.__name__} for {self.name} reported success, but verification failed."
                        )
                else:
                    warn(
                        f"Installation of {self.name} with {installer.__class__.__name__} failed."
                    )
            except Exception as e:
                error(
                    f"An exception occurred while trying to install {self.name} with {installer.__class__.__name__}: {e}"
                )
        error(f"All installation methods for {self.name} failed.")
        return False


class AptPackage(Installer):
    """Represents software installed via apt."""

    def __init__(
        self,
        name: str,
        dependencies: Optional[list[SoftwarePackage]] = None,
        version: Optional[str] = None,
    ):
        super().__init__(name, dependencies, version)
        if not command_exists("apt"):
            msg = "apt command not found. This script requires apt to function."
            error(msg)
            raise RuntimeError(msg)

    def _check_installed(self) -> bool:
        # dpkg-query is a reliable way to check for installed packages
        return (
            subprocess.run(
                ["dpkg-query", "-W", "-f='${Status}'", self.name],
                capture_output=True,
                text=True,
            ).stdout.find("install ok installed")
            != -1
        )

    def _install_package(self) -> bool:
        cmd = ["sudo", "apt", "install", "-y", self.name]
        if DRY_RUN:
            info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        return subprocess.run(cmd).returncode == 0

    def uninstall(self) -> bool:
        cmd = ["sudo", "apt", "remove", "-y", self.name]
        if DRY_RUN:
            info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        return subprocess.run(cmd).returncode == 0

    def get_version(self) -> Optional[str]:
        if not self.is_installed():
            return None
        try:
            # apt-cache policy can show the installed version
            result = subprocess.run(
                ["apt-cache", "policy", self.name],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.splitlines():
                if "Installed:" in line:
                    version = line.split("Installed:")[1].strip()
                    return version if version != "(none)" else None
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


class SnapPackage(Installer):
    """Represents software installed via snap."""

    def __init__(
        self,
        name: str,
        dependencies: Optional[list[SoftwarePackage]] = None,
        version: Optional[str] = None,
    ):
        super().__init__(name, dependencies, version)
        if not command_exists("snap"):
            info("Snap command not found, attempting to install snapd...")
            snapd_installer = AptPackage("snapd")
            if not snapd_installer.install():
                msg = "Failed to install snapd, which is required for snap packages."
                error(msg)
                raise RuntimeError(msg)
            success("snapd installed successfully.")

    def _check_installed(self) -> bool:
        # The `snap list` command shows installed snaps
        result = subprocess.run(["snap", "list"], capture_output=True, text=True)
        return self.name in result.stdout

    def _install_package(self) -> bool:
        cmd = ["sudo", "snap", "install", self.name]
        if DRY_RUN:
            info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        return subprocess.run(cmd).returncode == 0

    def uninstall(self) -> bool:
        cmd = ["sudo", "snap", "remove", self.name]
        if DRY_RUN:
            info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        return subprocess.run(cmd).returncode == 0

    def get_version(self) -> Optional[str]:
        if not self.is_installed():
            return None
        try:
            result = subprocess.run(
                ["snap", "list", self.name],
                capture_output=True,
                text=True,
                check=True,
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) > 1:
                return lines[1].split()[1]  # Version is in the second column
            return None
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            return None


class PipPackage(Installer):
    """Represents a Python package installed via pip."""

    def __init__(
        self,
        name: str,
        pip_executable: str = "pip3",
        dependencies: Optional[list[SoftwarePackage]] = None,
        version: Optional[str] = None,
    ):
        super().__init__(name, dependencies, version)
        self.pip_executable = pip_executable
        if not command_exists(self.pip_executable):
            info(
                f"{self.pip_executable} command not found, attempting to install python3-pip..."
            )
            pip_installer = AptPackage("python3-pip")
            if not pip_installer.install():
                msg = (
                    "Failed to install python3-pip, which is required for pip packages."
                )
                error(msg)
                raise RuntimeError(msg)
            success("python3-pip installed successfully.")

    def _check_installed(self) -> bool:
        # `pip show` is a good way to check for a package
        return (
            subprocess.run(
                [self.pip_executable, "show", self.name],
                capture_output=True,
                text=True,
            ).returncode
            == 0
        )

    def _install_package(self) -> bool:
        target = self.name
        if self.version:
            target += f"=={self.version}"
        cmd = [self.pip_executable, "install", target]
        if DRY_RUN:
            info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        return subprocess.run(cmd).returncode == 0

    def uninstall(self) -> bool:
        cmd = [self.pip_executable, "uninstall", "-y", self.name]
        if DRY_RUN:
            info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        return subprocess.run(cmd).returncode == 0

    def get_version(self) -> Optional[str]:
        if not self.is_installed():
            return None
        try:
            result = subprocess.run(
                [self.pip_executable, "show", self.name],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":")[1].strip()
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


class ScriptInstaller(Installer):
    """Represents software installed by executing a shell script, often fetched with curl or wget."""

    def __init__(
        self,
        name: str,
        install_script_url: str,
        executable_path: str,
        dependencies: Optional[list[SoftwarePackage]] = None,
    ):
        super().__init__(name, dependencies)
        self.install_script_url = install_script_url
        self.executable_path = Path(executable_path).expanduser()
        if not command_exists("curl"):
            info("curl command not found, attempting to install...")
            curl_installer = AptPackage("curl")
            if not curl_installer.install():
                msg = "Failed to install curl, which is required for script-based installations."
                error(msg)
                raise RuntimeError(msg)
            success("curl installed successfully.")

    def _check_installed(self) -> bool:
        # Check if the executable exists at the specified path
        return self.executable_path.exists()

    def _install_package(self) -> bool:
        # This is a simplified example. Real-world scripts can be complex.
        # Assumes a curl | bash pattern.
        cmd = f"curl -sSL {self.install_script_url} | bash"
        if DRY_RUN:
            info(f"[DRY RUN] Would run: {cmd}")
            return True
        try:
            # Using shell=True is necessary here but use with caution.
            subprocess.run(cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            error(f"Installation script for {self.name} failed: {e}")
            return False

    def uninstall(self) -> bool:
        # Uninstallation for script-based installs is often not standardized.
        # A common pattern is to just remove the executable.
        if self.executable_path.exists():
            info(f"Attempting to remove {self.executable_path}")
            if DRY_RUN:
                info(f"[DRY RUN] Would remove: {self.executable_path}")
                return True
            self.executable_path.unlink()
            return True
        warn(f"Could not find {self.executable_path} to uninstall.")
        return False

    def get_version(self) -> Optional[str]:
        if not self.is_installed():
            return None
        # Version fetching depends heavily on the installed tool.
        # Common patterns are --version or -v.
        for flag in ["--version", "-v", "version"]:
            try:
                result = subprocess.run(
                    [str(self.executable_path), flag],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # This is a simple regex, might need adjustment for specific tools
                match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        debug(f"Could not determine version for {self.name}")
        return None


def install_minimal(): ...


def install_standard():
    """Defines and executes the standard installation sequence."""
    info("Starting standard installation process...")

    # Define dependencies that might be shared
    curl_dep = SoftwarePackage("curl", [AptPackage("curl")])
    snapd_dep = SoftwarePackage("snapd", [AptPackage("snapd")])
    pip_dep = SoftwarePackage("python3-pip", [AptPackage("python3-pip")])

    # Define software to be installed
    packages_to_install = [
        SoftwarePackage("vim", [AptPackage("vim")]),
        SoftwarePackage("git", [AptPackage("git")]),
        SoftwarePackage(
            "vscode",
            [
                SnapPackage("code", dependencies=[snapd_dep]),
                # Could add an alternative to download .deb and install with apt
            ],
        ),
        SoftwarePackage("uv", [PipPackage("uv", dependencies=[pip_dep])]),
        SoftwarePackage(
            "nvm",
            [
                ScriptInstaller(
                    name="nvm",
                    install_script_url="https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh",
                    executable_path="~/.nvm/nvm.sh",
                    dependencies=[curl_dep],
                )
            ],
        ),
    ]

    # Install all packages
    for pkg in packages_to_install:
        if not pkg.install():
            error(f"Stopping installation due to failure in installing {pkg.name}.")
            safely_shutdown()

    success("Standard installation completed successfully!")


def install_full(): ...


def install_custom(): ...


def main():
    setup_logging()
    try:
        # Show preamble
        show_header()
        show_legend()

        # Parse arguments and get installation mode
        install_mode = arguments()

        # Display configuration values
        info(f"Logging to: {str(LOG_PATH)}")
        info(f"Script version: {VERSION}")
        info(f"Target Operating System: {TARGET_OS}")
        info(f"Flags: {VERBOSE=}, {UPGRADE=}, {DRY_RUN=}")
        info(f"Install mode: {install_mode.value}")

        if not confirm(text="Would you like to start?"):
            # Stop installation
            safely_shutdown()

        # Perfrom installation based on mode
        match install_mode:
            case InstallMode.STANDARD:
                debug("Starting standard installation")
                install_standard()
                debug("Ending STANDARD installation")
            case InstallMode.MINIMAL:
                debug("Starting MINIMAL installation")
                install_minimal()
                debug("Ending MINIMAL installation")
            case InstallMode.FULL:
                debug("Starting FULL installation")
                install_full()
                debug("Ending FULL installation")
            case InstallMode.CUSTOM:
                debug("Starting CUSTOM installation")
                install_custom()
                debug("Ending CUSTOM installation")
    except KeyboardInterrupt:
        error("Installation interrupted by user")
    except Exception as e:
        error(f"Error during installation: {e}. Halting")
    safely_shutdown()


# Usage
if __name__ == "__main__":
    main()
