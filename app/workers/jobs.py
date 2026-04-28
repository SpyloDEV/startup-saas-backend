import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.models.background_job import BackgroundJobStatus
from app.repositories.background_jobs import BackgroundJobRepository
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="notifications.send_task_assignment_email")
def send_task_assignment_email(job_id: str) -> None:
    asyncio.run(_send_task_assignment_email(job_id))


async def _send_task_assignment_email(job_id: str) -> None:
    async with AsyncSessionLocal() as session:
        jobs = BackgroundJobRepository(session)
        job = await jobs.get(job_id)
        if job is None:
            logger.warning("Task assignment email job %s was not found", job_id)
            return

        await jobs.set_status(job, status=BackgroundJobStatus.RUNNING)
        await session.commit()

        try:
            payload = job.payload
            logger.info(
                "Fake email notification: user %s was assigned to task %s",
                payload["assigned_to_id"],
                payload["task_id"],
            )
            await jobs.set_status(
                job,
                status=BackgroundJobStatus.SUCCEEDED,
                result={"delivered": True, "transport": "fake_email"},
            )
            await session.commit()
        except Exception as exc:
            await jobs.set_status(
                job,
                status=BackgroundJobStatus.FAILED,
                error=str(exc),
            )
            await session.commit()
            raise
