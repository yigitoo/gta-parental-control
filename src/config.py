"""Configuration constants for the parental control application."""

import os
import sys

# --- Process Detection ---
TARGET_PROCESSES = ["GTA5.exe", "GTA5_Enhanced.exe", "PlayGTAV.exe"]
KILL_PROCESSES = ["GTA5.exe", "GTA5_Enhanced.exe", "PlayGTAV.exe", "GTAVLauncher.exe", "subprocess.exe"]

# --- Time Limits (seconds) ---
DAILY_LIMIT_SECONDS = 7200          # 2 hours
WARNING_THRESHOLD_SECONDS = 6300    # 1h 45m  -> 15 min warning
FINAL_WARNING_SECONDS = 7080        # 1h 58m  -> 2 min warning
KILL_DELAY_SECONDS = 3              # delay after limit before force-close

# --- Polling Intervals (seconds) ---
POLL_IDLE = 30      # game not running
POLL_ACTIVE = 10    # game running

# --- Paths ---
_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Microsoft", "WindowsServices", "NetFrameworkCache",
)
DATA_FILE = os.path.join(_DATA_DIR, "svchost_cache.json")
LOG_FILE = os.path.join(_DATA_DIR, "svchost_service.log")

# --- Display / Disguise ---
APP_NAME = "Windows Service Helper"
EXE_NAME = "WinServiceHelper"


def ensure_data_dir():
    """Create the hidden data directory if it doesn't exist."""
    if not os.path.isdir(_DATA_DIR):
        os.makedirs(_DATA_DIR, exist_ok=True)
        # Set hidden attribute on the top-level custom folder
        hidden_root = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            "Microsoft", "WindowsServices",
        )
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(hidden_root, 0x02)  # FILE_ATTRIBUTE_HIDDEN
        except Exception:
            pass


def resource_path(relative: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)
