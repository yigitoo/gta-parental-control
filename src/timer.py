"""Playtime tracking with JSON persistence and daily reset."""

import json
import logging
import time
from datetime import date

from config import DATA_FILE, DAILY_LIMIT_SECONDS, ensure_data_dir

logger = logging.getLogger(__name__)


class PlaytimeTracker:
    def __init__(self):
        ensure_data_dir()
        self._session_start: float | None = None
        self._today: str = str(date.today())
        self._accumulated: float = 0.0  # seconds already persisted for today
        self._load()

    # --- persistence ---

    def _load(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            saved_date = data.get("date", "")
            if saved_date == self._today:
                self._accumulated = float(data.get("seconds", 0.0))
                logger.info("Loaded %.0f persisted seconds for today.", self._accumulated)
            else:
                logger.info("New day detected (saved=%s, today=%s). Resetting.", saved_date, self._today)
                self._accumulated = 0.0
        except FileNotFoundError:
            self._accumulated = 0.0
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("Corrupted data file, resetting: %s", exc)
            self._accumulated = 0.0

    def _save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({"date": self._today, "seconds": self._accumulated}, f)
        except OSError as exc:
            logger.error("Failed to save data: %s", exc)

    # --- session management ---

    def start_session(self):
        if self._session_start is None:
            self._check_midnight()
            self._session_start = time.monotonic()
            logger.info("Session started. Accumulated so far: %.0fs", self._accumulated)

    def end_session(self):
        if self._session_start is not None:
            elapsed = time.monotonic() - self._session_start
            self._accumulated += elapsed
            self._session_start = None
            self._save()
            logger.info("Session ended. +%.0fs -> total %.0fs today.", elapsed, self._accumulated)

    @property
    def in_session(self) -> bool:
        return self._session_start is not None

    # --- queries ---

    def get_total_seconds_today(self) -> float:
        self._check_midnight()
        total = self._accumulated
        if self._session_start is not None:
            total += time.monotonic() - self._session_start
        return total

    def get_remaining_seconds(self) -> float:
        return max(0.0, DAILY_LIMIT_SECONDS - self.get_total_seconds_today())

    def is_limit_reached(self) -> bool:
        return self.get_total_seconds_today() >= DAILY_LIMIT_SECONDS

    # --- helpers ---

    def _check_midnight(self):
        today = str(date.today())
        if today != self._today:
            logger.info("Midnight rollover: %s -> %s", self._today, today)
            self._today = today
            self._accumulated = 0.0
            self._session_start = None
            self._save()
