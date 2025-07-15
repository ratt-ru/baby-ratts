import logging
import argparse
from pathlib import Path
import subprocess
import sys
import json
from time import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Globals
FOUND_COMMANDS = set()
LOG_PATH: Path
LOGGER: logging.Logger
STATE_FILE: Path
INSTALLATION_STATE: dict

# Flags
VERBOSE: bool = False
UPGRADE: bool = True
DRY_RUN: bool = False
INTERACTIVE: bool = False
ROLLBACK: bool = False


class SoftwareCategory(Enum):
    """Categories of software that can be installed"""

    ESSENTIAL = "essential"  # Basic system tools
    DEVELOPMENT = "development"  # Programming tools
    PYTHON = "python"  # Python ecosystem
    RESEARCH = "research"  # Research-specific tools
    MULTIMEDIA = "multimedia"  # Audio/video tools
    PRODUCTIVITY = "productivity"  # General productivity tools


@dataclass
class InstallationRecord:
    """Record of an installation attempt"""

    name: str
    category: SoftwareCategory
    method: str  # apt, snap, curl, etc.
    success: bool
    timestamp: float
    packages: list  # actual packages installed


# Software catalog - easy to extend for your research group
SOFTWARE_CATALOG = {
    SoftwareCategory.ESSENTIAL: {
        "curl": {
            "packages": ["curl"],
            "method": "apt",
            "description": "Data transfer tool",
        },
        "wget": {
            "packages": ["wget"],
            "method": "apt",
            "description": "Web downloader",
        },
        "git": {
            "packages": ["git"],
            "method": "apt",
            "description": "Version control system",
        },
        "vim": {"packages": ["vim"], "method": "apt", "description": "Text editor"},
        "htop": {
            "packages": ["htop"],
            "method": "apt",
            "description": "System monitor",
        },
        "tree": {
            "packages": ["tree"],
            "method": "apt",
            "description": "Directory tree viewer",
        },
        "zip": {
            "packages": ["zip", "unzip"],
            "method": "apt",
            "description": "Archive utilities",
        },
    },
    SoftwareCategory.DEVELOPMENT: {
        "build-essential": {
            "packages": ["build-essential"],
            "method": "apt",
            "description": "Compilation tools",
        },
        "cmake": {
            "packages": ["cmake"],
            "method": "apt",
            "description": "Build system",
        },
        "nodejs": {
            "packages": ["nodejs", "npm"],
            "method": "apt",
            "description": "Node.js runtime",
        },
        "docker": {
            "packages": ["docker.io"],
            "method": "apt",
            "description": "Container platform",
        },
        "code": {
            "packages": ["code"],
            "method": "snap",
            "description": "VS Code editor",
        },
    },
    SoftwareCategory.PYTHON: {
        "python3-dev": {
            "packages": ["python3-dev", "python3-pip"],
            "method": "apt",
            "description": "Python development",
        },
        "uv": {
            "packages": [],
            "method": "custom",
            "description": "Fast Python package manager",
        },
        "poetry": {
            "packages": [],
            "method": "custom",
            "description": "Python dependency management",
        },
        "pipx": {
            "packages": ["pipx"],
            "method": "apt",
            "description": "Install Python apps in isolation",
        },
    },
    SoftwareCategory.RESEARCH: {
        "r-base": {
            "packages": ["r-base"],
            "method": "apt",
            "description": "R statistical computing",
        },
        "texlive": {
            "packages": ["texlive-latex-base"],
            "method": "apt",
            "description": "LaTeX document system",
        },
        "pandoc": {
            "packages": ["pandoc"],
            "method": "apt",
            "description": "Document converter",
        },
    },
    SoftwareCategory.MULTIMEDIA: {
        "ffmpeg": {
            "packages": ["ffmpeg"],
            "method": "apt",
            "description": "Multimedia framework",
        },
        "imagemagick": {
            "packages": ["imagemagick"],
            "method": "apt",
            "description": "Image manipulation",
        },
        "vlc": {"packages": ["vlc"], "method": "snap", "description": "Media player"},
    },
    SoftwareCategory.PRODUCTIVITY: {
        "firefox": {
            "packages": ["firefox"],
            "method": "snap",
            "description": "Web browser",
        },
        "libreoffice": {
            "packages": ["libreoffice"],
            "method": "snap",
            "description": "Office suite",
        },
        "thunderbird": {
            "packages": ["thunderbird"],
            "method": "snap",
            "description": "Email client",
        },
    },
}


def parse_arguments():
    global VERBOSE, UPGRADE, DRY_RUN, LOG_PATH, INTERACTIVE, ROLLBACK, STATE_FILE
    parser = argparse.ArgumentParser(
        description="Post-installation script for setting up research group software",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Install essential software only
  %(prog)s --categories essential development # Install specific categories
  %(prog)s --interactive                      # Interactive selection
  %(prog)s --dry-run --verbose               # Preview what would be installed
  %(prog)s --rollback                        # Rollback last installation
        """,
    )
    parser.add_argument(
        "-m", "--minimal", action="store_true", help="Minimal installation used (Cannot run with -f)."
    )
    parser.add_argument(
        "-f", "--full", action="store_true", help="Full installation used (Cannot run with -m)."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-upgrade", action="store_true", help="Skip apt upgrade step"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Preview commands without executing",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive software selection",
    )
    parser.add_argument(
        "--rollback", action="store_true", help="Rollback previous installation"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=[cat.value for cat in SoftwareCategory],
        default=["essential"],
        help="Software categories to install (default: essential)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="Software names to exclude from installation",
    )
    parser.add_argument(
        "--log-file",
        default="post-install.log",
        help="Specify log file path (default: post-install.log)",
    )
    parser.add_argument(
        "--state-file",
        default="post-install-state.json",
        help="State file for tracking installations (default: post-install-state.json)",
    )

    args = parser.parse_args()
    VERBOSE = args.verbose
    UPGRADE = not args.no_upgrade
    DRY_RUN = args.dry_run
    INTERACTIVE = args.interactive
    ROLLBACK = args.rollback
    LOG_PATH = Path(args.log_file)
    STATE_FILE = Path(args.state_file)


def setup_logging():
    """Configure logging based on verbose flag"""
    global LOGGER
    level = logging.DEBUG if VERBOSE else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)-5s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_PATH),
        ],
    )
    LOGGER = logging.getLogger(__name__)


def safely_shutdown():
    LOGGER.info("Safely shutting down")
    sys.exit(1)


def cmd_exists(cmd: str) -> bool:
    if cmd in FOUND_COMMANDS:
        LOGGER.debug("Executable found. Previously checked")
        return True
    LOGGER.debug(f"Checking if new command {cmd} installed")
    if DRY_RUN and cmd not in FOUND_COMMANDS:
        FOUND_COMMANDS.add(cmd)
        LOGGER.debug("Executable found. Adding to checked (DRY RUN)")
        return True
    try:
        result = subprocess.run(
            ["which", cmd], check=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            FOUND_COMMANDS.add(cmd)
            LOGGER.debug("Executable found. Adding to checked")
            return True
    except Exception:
        pass
    LOGGER.debug("Executable not found")
    return False


def run_command(*cmd: str) -> int:
    if not cmd_exists(cmd[0]):
        LOGGER.debug(f"Command {cmd[0]} not found. Consider installing")
        return -1
    LOGGER.debug(f"Running: {' '.join(cmd)}")
    if DRY_RUN:
        FOUND_COMMANDS.add(cmd)
        LOGGER.debug(f"Completed [DRY-RUN]: {cmd[0]}")
        return 0
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        LOGGER.debug(f"Completed [{result.returncode}]: {cmd[0]}")
        return result.returncode
    except subprocess.CalledProcessError as error:
        LOGGER.error(f"Failed: {' '.join(cmd)}")
        LOGGER.error(f"Error: {error}")
        safely_shutdown()
    return 0


def apt_update() -> int:
    ret = run_command("apt", "update", "-y")
    if ret == -1:
        LOGGER.error("Missing apt command")
        return 1
    elif ret != 0:
        LOGGER.error("Failed to update apt package list")
        return 1
    else:
        LOGGER.debug("Update completed")
        return 0


def apt_upgrade() -> int:
    LOGGER.debug("Upgrading apt packages")
    ret = run_command("apt", "upgrade", "-y")
    if ret == -1:
        LOGGER.error("Missing apt command")
        return 1
    elif ret != 0:
        LOGGER.error("Failed to upgrade apt packages")
        return 1
    else:
        LOGGER.debug("Upgrade completed")
        return 0


def apt_install(*progs: str) -> int:
    if len(progs) == 0:
        LOGGER.error("No programs provided to install")
        return 1
    LOGGER.debug(f"Installing via apt: {', '.join(progs)}")
    ret = run_command("apt", "install", "-y", *progs)
    if ret == -1:
        LOGGER.error("Missing apt command")
        return 1
    elif ret != 0:
        LOGGER.error("Failed to install programs")
        return 1
    else:
        LOGGER.debug("Installation completed")
        return 0


def load_installation_state() -> dict:
    """Load previous installation state from file"""
    global INSTALLATION_STATE
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                INSTALLATION_STATE = json.load(f)
                LOGGER.debug(f"Loaded installation state from {STATE_FILE}")
        except Exception as e:
            LOGGER.warning(f"Could not load state file: {e}")
            INSTALLATION_STATE = {"installations": [], "version": "1.0"}
    else:
        INSTALLATION_STATE = {"installations": [], "version": "1.0"}
    return INSTALLATION_STATE


def save_installation_state() -> None:
    """Save current installation state to file"""
    if not DRY_RUN:
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(INSTALLATION_STATE, f, indent=2)
                LOGGER.debug(f"Saved installation state to {STATE_FILE}")
        except Exception as e:
            LOGGER.error(f"Could not save state file: {e}")


def add_installation_record(record: InstallationRecord) -> None:
    """Add an installation record to the state"""
    record_dict = {
        "name": record.name,
        "category": record.category.value,
        "method": record.method,
        "success": record.success,
        "timestamp": record.timestamp,
        "packages": record.packages,
    }
    INSTALLATION_STATE["installations"].append(record_dict)
    save_installation_state()


def rollback_installation() -> None:
    """Rollback the last installation session"""
    if not INSTALLATION_STATE.get("installations"):
        LOGGER.info("No installations to rollback")
        return

    # Get the latest session (installations from the same run)
    latest_session = []
    if INSTALLATION_STATE["installations"]:
        latest_timestamp = INSTALLATION_STATE["installations"][-1]["timestamp"]
        # Consider installations within 5 minutes as same session
        session_window = 300  # 5 minutes

        for install in reversed(INSTALLATION_STATE["installations"]):
            if latest_timestamp - install["timestamp"] <= session_window:
                latest_session.append(install)
            else:
                break

    if not latest_session:
        LOGGER.info("No recent installations to rollback")
        return

    LOGGER.info(f"Rolling back {len(latest_session)} installations...")
    rollback_success = True

    for install in latest_session:
        if install["success"] and install["packages"]:
            LOGGER.info(f"Rolling back {install['name']}")
            if install["method"] == "apt":
                ret = run_command("apt", "remove", "-y", *install["packages"])
                if ret != 0:
                    LOGGER.error(f"Failed to rollback {install['name']}")
                    rollback_success = False
            elif install["method"] == "snap":
                for pkg in install["packages"]:
                    ret = run_command("snap", "remove", pkg)
                    if ret != 0:
                        LOGGER.error(f"Failed to rollback snap package {pkg}")
                        rollback_success = False
            # Custom installations would need specific rollback logic

    if rollback_success:
        # Remove rolled back installations from state
        INSTALLATION_STATE["installations"] = [
            install
            for install in INSTALLATION_STATE["installations"]
            if install not in latest_session
        ]
        save_installation_state()
        LOGGER.info("Rollback completed successfully")
    else:
        LOGGER.error("Rollback completed with some errors")


def is_already_installed(software_name: str) -> bool:
    """Check if software was already installed in a previous run"""
    for install in INSTALLATION_STATE.get("installations", []):
        if install["name"] == software_name and install["success"]:
            LOGGER.debug(f"{software_name} already installed in previous run")
            return True
    return False


def interactive_software_selection(categories: list) -> dict:
    """Allow user to interactively select software to install"""
    selection = {}

    print("\n" + "=" * 60)
    print("INTERACTIVE SOFTWARE SELECTION")
    print("=" * 60)

    for category_name in categories:
        try:
            category = SoftwareCategory(category_name)
            software_list = SOFTWARE_CATALOG[category]

            print(f"\n📁 {category.value.upper()} SOFTWARE:")
            print("-" * 40)

            for software_name, info in software_list.items():
                if is_already_installed(software_name):
                    print(
                        f"  ✅ {software_name} - {info['description']} (already installed)"
                    )
                    selection[software_name] = False  # Skip already installed
                    continue

                while True:
                    response = (
                        input(
                            f"  Install {software_name} - {info['description']}? [Y/n/q]: "
                        )
                        .strip()
                        .lower()
                    )
                    if response in ["", "y", "yes"]:
                        selection[software_name] = True
                        break
                    elif response in ["n", "no"]:
                        selection[software_name] = False
                        break
                    elif response in ["q", "quit"]:
                        print("Exiting...")
                        sys.exit(0)
                    else:
                        print("  Please enter Y (yes), n (no), or q (quit)")

        except ValueError:
            LOGGER.error(f"Unknown category: {category_name}")

    return selection


def snap_install(*packages: str) -> int:
    """Install packages using snap"""
    if len(packages) == 0:
        LOGGER.error("No packages provided to snap install")
        return -1

    LOGGER.debug(f"Installing via snap: {', '.join(packages)}")
    success_count = 0

    for package in packages:
        ret = run_command("snap", "install", package)
        if ret == 0:
            success_count += 1
        else:
            LOGGER.error(f"Failed to install snap package: {package}")

    return 0 if success_count == len(packages) else 1


def install_custom_software(software_name: str) -> int:
    """Handle custom software installations"""
    if software_name == "uv":
        return install_uv_new()
    elif software_name == "poetry":
        return install_poetry()
    else:
        LOGGER.error(f"Unknown custom software: {software_name}")
        return 1


def install_uv_new() -> int:
    """Install uv with better error handling"""
    if cmd_exists("uv"):
        LOGGER.debug("uv already available")
        return 0

    LOGGER.debug("Installing uv from https://astral.sh/uv/install.sh")

    # Try curl first
    if cmd_exists("curl"):
        ret = run_command("curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh")
        if ret == 0:
            LOGGER.debug("uv installation completed via curl")
            return 0

    # Try wget as fallback
    if cmd_exists("wget"):
        ret = run_command("wget", "-qO-", "https://astral.sh/uv/install.sh", "|", "sh")
        if ret == 0:
            LOGGER.debug("uv installation completed via wget")
            return 0

    LOGGER.error("Failed to install uv - neither curl nor wget available")
    return 1


def install_poetry() -> int:
    """Install Poetry using the official installer"""
    if cmd_exists("poetry"):
        LOGGER.debug("poetry already available")
        return 0

    LOGGER.debug("Installing Poetry from get-poetry.py")

    if cmd_exists("curl"):
        ret = run_command(
            "curl", "-sSL", "https://install.python-poetry.org", "|", "python3", "-"
        )
        if ret == 0:
            LOGGER.debug("Poetry installation completed")
            return 0

    LOGGER.error("Failed to install Poetry")
    return 1


def install_software_by_category(
    categories: list,
    exclude_list: Optional[list] = None,
    interactive_selection: Optional[dict] = None,
) -> bool:
    """Install software from specified categories"""
    if exclude_list is None:
        exclude_list = []

    overall_success = True

    for category_name in categories:
        try:
            category = SoftwareCategory(category_name)
            software_list = SOFTWARE_CATALOG[category]

            LOGGER.info(f"📁 Installing {category.value} software...")

            for software_name, info in software_list.items():
                # Skip if excluded or user deselected in interactive mode
                if software_name in exclude_list:
                    LOGGER.debug(f"Skipping excluded software: {software_name}")
                    continue

                if interactive_selection and not interactive_selection.get(
                    software_name, True
                ):
                    LOGGER.debug(f"Skipping deselected software: {software_name}")
                    continue

                # Skip if already installed in previous run
                if is_already_installed(software_name):
                    LOGGER.info(f"✅ {software_name} already installed")
                    continue

                LOGGER.info(f"Installing {software_name}...")
                start_time = time()

                # Install based on method
                success = False
                packages_installed = []

                if info["method"] == "apt":
                    ret = apt_install(*info["packages"])
                    success = ret == 0
                    packages_installed = info["packages"] if success else []

                elif info["method"] == "snap":
                    ret = snap_install(*info["packages"])
                    success = ret == 0
                    packages_installed = info["packages"] if success else []

                elif info["method"] == "custom":
                    ret = install_custom_software(software_name)
                    success = ret == 0
                    packages_installed = [software_name] if success else []

                # Record the installation attempt
                record = InstallationRecord(
                    name=software_name,
                    category=category,
                    method=info["method"],
                    success=success,
                    timestamp=start_time,
                    packages=packages_installed,
                )
                add_installation_record(record)

                if success:
                    LOGGER.info(f"✅ {software_name} installed successfully")
                else:
                    LOGGER.error(f"❌ Failed to install {software_name}")
                    overall_success = False

        except ValueError:
            LOGGER.error(f"Unknown category: {category_name}")
            overall_success = False

    return overall_success


def main():
    """Main function orchestrating the post-installation process"""
    start = time()
    parse_arguments()
    setup_logging()

    LOGGER.info("🚀 RATT Ubuntu Post-Install Script v1.0")
    LOGGER.info(f"📝 Logging to: {LOG_PATH}")
    LOGGER.info(f"💾 State file: {STATE_FILE}")
    LOGGER.info(
        f"⚙️  Running with VERBOSE={VERBOSE}, UPGRADE={UPGRADE}, DRY_RUN={DRY_RUN}"
    )

    # Load previous installation state
    load_installation_state()

    # Handle rollback request
    if ROLLBACK:
        LOGGER.info("🔄 Rolling back previous installation...")
        rollback_installation()
        return

    # System updates
    LOGGER.info("📦 Updating system packages...")
    ret = apt_update()
    if ret != 0:
        LOGGER.error("Failed to update packages, continuing anyway...")

    if UPGRADE:
        LOGGER.info("⬆️  Upgrading system packages...")
        ret = apt_upgrade()
        if ret != 0:
            LOGGER.error("Failed to upgrade packages, continuing anyway...")
    else:
        LOGGER.info("⏭️  Skipping system upgrade (--no-upgrade specified)")

    # Get software selection
    categories = []
    exclude_list = []

    # Parse categories from args (we need to re-access them)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", default=["essential"])
    parser.add_argument("--exclude", nargs="+", default=[])
    parser.add_argument("--interactive", action="store_true")
    temp_args, _ = parser.parse_known_args()

    categories = temp_args.categories
    exclude_list = temp_args.exclude

    LOGGER.info(f"📋 Selected categories: {', '.join(categories)}")
    if exclude_list:
        LOGGER.info(f"🚫 Excluded software: {', '.join(exclude_list)}")

    # Interactive selection if requested
    user_selection = None
    if INTERACTIVE:
        user_selection = interactive_software_selection(categories)
        selected_count = sum(1 for selected in user_selection.values() if selected)
        LOGGER.info(f"👤 User selected {selected_count} software packages")

    # Install software
    LOGGER.info("🔧 Starting software installation...")
    success = install_software_by_category(categories, exclude_list, user_selection)

    # Summary
    duration = time() - start
    if success:
        LOGGER.info(f"✅ Post-install script completed successfully in {duration:.2f}s")
    else:
        LOGGER.warning(
            f"⚠️  Post-install script completed with some errors in {duration:.2f}s"
        )
        LOGGER.info("💡 You can run with --rollback to undo the last installation")

    LOGGER.info(
        f"📊 Total installations tracked: {len(INSTALLATION_STATE.get('installations', []))}"
    )
    LOGGER.info("🎉 Ready for research work!")


# Usage
if __name__ == "__main__":
    main()
