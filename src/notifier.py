"""Windows toast notifications with fallback."""

import logging
import threading

logger = logging.getLogger(__name__)


def _show_toast(title: str, message: str):
    """Send a Windows 11 toast notification (blocking call)."""
    try:
        from win11toast import toast
        toast(title, message, duration="long")
    except Exception as exc:
        logger.warning("win11toast failed (%s), trying MessageBox fallback.", exc)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x40000)
        except Exception:
            logger.error("All notification methods failed.")


def notify(title: str, message: str):
    """Non-blocking notification via daemon thread."""
    t = threading.Thread(target=_show_toast, args=(title, message), daemon=True)
    t.start()


def notify_warning_15():
    notify(
        "System Maintenance",
        "Scheduled maintenance will begin in 15 minutes. Please save your work.",
    )


def notify_warning_2():
    notify(
        "System Maintenance",
        "Maintenance starting in 2 minutes. Save all work immediately.",
    )


def notify_limit_reached():
    notify(
        "System Maintenance",
        "Scheduled maintenance is starting now. The application will close.",
    )
