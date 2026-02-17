"""System tray icon using pystray."""

import logging
import threading

from PIL import Image, ImageDraw
import pystray

from config import APP_NAME

logger = logging.getLogger(__name__)


def _create_icon_image() -> Image.Image:
    """Generate a simple grey circle icon programmatically."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(128, 128, 128, 255))
    return img


class TrayApp:
    def __init__(self, get_remaining_fn, shutdown_fn):
        """
        Args:
            get_remaining_fn: callable returning remaining seconds (float).
            shutdown_fn: callable to trigger graceful app shutdown.
        """
        self._get_remaining = get_remaining_fn
        self._shutdown = shutdown_fn
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem("Status", self._on_status, default=True),
            pystray.MenuItem("Exit", self._on_exit),
        )
        self._icon = pystray.Icon(
            name="wsh",
            icon=_create_icon_image(),
            title=APP_NAME,
            menu=menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("Tray icon started.")

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            logger.info("Tray icon stopped.")

    def _on_status(self, icon, item):
        remaining = self._get_remaining()
        mins = int(remaining) // 60
        secs = int(remaining) % 60
        # Update tooltip / show via notification
        from notifier import notify
        notify(APP_NAME, f"Time remaining: {mins}m {secs}s")

    def _on_exit(self, icon, item):
        logger.info("Exit requested from tray menu.")
        self._shutdown()
