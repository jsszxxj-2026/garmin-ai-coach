from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.db.session import get_db
from backend.app.jobs.poll_garmin import poll_garmin
from src.core.config import settings


logger = logging.getLogger(__name__)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    interval_minutes = max(int(settings.GARMIN_POLL_INTERVAL_MINUTES), 1)
    scheduler.add_job(
        _run_polling,
        trigger="interval",
        minutes=interval_minutes,
        id="garmin_polling",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(f"[Scheduler] Garmin polling scheduler started, interval={interval_minutes}m")
    return scheduler


def _run_polling() -> None:
    try:
        db = next(get_db())
        try:
            poll_garmin(db)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[Scheduler] polling failed: {e}")
