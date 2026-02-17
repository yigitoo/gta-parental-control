"""Entry point – main monitoring loop."""

import logging
import signal
import sys
import time

from config import (
    APP_NAME,
    DAILY_LIMIT_SECONDS,
    FINAL_WARNING_SECONDS,
    KILL_DELAY_SECONDS,
    LOG_FILE,
    POLL_ACTIVE,
    POLL_IDLE,
    WARNING_THRESHOLD_SECONDS,
    ensure_data_dir,
)
from monitor import is_game_running, kill_game
from notifier import notify_limit_reached, notify_warning_2, notify_warning_15
from timer import PlaytimeTracker
from tray import TrayApp

logger = logging.getLogger()


def setup_logging():
    ensure_data_dir()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    # File handler
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    # Stderr handler (visible only when running from console)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.setLevel(logging.DEBUG)


def main():
    setup_logging()
    logger.info("=== %s starting ===", APP_NAME)

    tracker = PlaytimeTracker()
    running = True

    def shutdown():
        nonlocal running
        running = False

    tray = TrayApp(tracker.get_remaining_seconds, shutdown)
    tray.start()

    # Graceful shutdown on SIGINT / SIGTERM
    def _sig_handler(signum, frame):
        logger.info("Signal %s received, shutting down.", signum)
        shutdown()

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    # Dedup flags for warnings
    warned_15 = False
    warned_2 = False
    was_running = False

    try:
        while running:
            game_running = is_game_running()

            # --- Rising edge: game just launched ---
            if game_running and not was_running:
                logger.info("Game detected – starting session.")
                tracker.start_session()
                warned_15 = False
                warned_2 = False

            # --- Falling edge: game just closed ---
            if not game_running and was_running:
                logger.info("Game no longer detected – ending session.")
                tracker.end_session()

            was_running = game_running

            if game_running:
                total = tracker.get_total_seconds_today()
                remaining = tracker.get_remaining_seconds()
                logger.debug("Playtime: %.0fs / %ds  (remaining: %.0fs)", total, DAILY_LIMIT_SECONDS, remaining)

                # Warning cascade
                if total >= WARNING_THRESHOLD_SECONDS and not warned_15:
                    notify_warning_15()
                    warned_15 = True
                    logger.info("15-minute warning sent.")

                if total >= FINAL_WARNING_SECONDS and not warned_2:
                    notify_warning_2()
                    warned_2 = True
                    logger.info("2-minute warning sent.")

                # Enforcement
                if tracker.is_limit_reached():
                    logger.info("Daily limit reached! Closing game in %ds.", KILL_DELAY_SECONDS)
                    notify_limit_reached()
                    time.sleep(KILL_DELAY_SECONDS)
                    kill_game()
                    tracker.end_session()
                    was_running = False
                    logger.info("Game killed. Enforcement complete for today.")

            # Adaptive polling
            interval = POLL_ACTIVE if game_running else POLL_IDLE

            # Sleep in small increments so shutdown is responsive
            deadline = time.monotonic() + interval
            while running and time.monotonic() < deadline:
                time.sleep(1)

    except Exception:
        logger.exception("Unhandled exception in main loop.")
    finally:
        if tracker.in_session:
            tracker.end_session()
        tray.stop()
        logger.info("=== %s stopped ===", APP_NAME)


if __name__ == "__main__":
    main()
