"""Process detection and kill logic for GTA V."""

import logging
import subprocess

import psutil

from config import TARGET_PROCESSES, KILL_PROCESSES

logger = logging.getLogger(__name__)


def is_game_running() -> bool:
    """Return True if any target process is found."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] in TARGET_PROCESSES:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def get_game_pids() -> list[tuple[int, str]]:
    """Return list of (pid, name) for all kill-target processes."""
    pids = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            name = proc.info["name"]
            if name in KILL_PROCESSES:
                pids.append((proc.info["pid"], name))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def kill_game():
    """Force-close GTA V and related launcher processes."""
    pids = get_game_pids()
    if not pids:
        logger.info("No game processes found to kill.")
        return

    # Strategy 1: psutil terminate/kill
    for pid, name in pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            logger.info("Terminated %s (PID %d) via psutil.", name, pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
            logger.warning("psutil terminate failed for %s (PID %d): %s", name, pid, exc)

    # Strategy 2: taskkill fallback for anything that survived
    for process_name in KILL_PROCESSES:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", process_name],
                capture_output=True,
                timeout=5,
            )
        except FileNotFoundError:
            pass  # not on Windows (dev/test)
        except subprocess.TimeoutExpired:
            logger.warning("taskkill timed out for %s", process_name)
