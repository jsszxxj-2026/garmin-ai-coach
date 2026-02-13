from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.db.session import get_db
from backend.app.jobs.poll_garmin import poll_garmin


logger = logging.getLogger(__name__)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        _run_polling,
        trigger="interval",
        minutes=30,
        id="garmin_polling",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[Scheduler] Garmin polling scheduler started")
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
