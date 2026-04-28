import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.background_job import BackgroundJob, BackgroundJobStatus
from app.repositories.background_jobs import BackgroundJobRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.jobs = BackgroundJobRepository(session)
        self.settings = get_settings()

    async def enqueue_task_assignment_email(
        self,
        *,
        workspace_id: str,
        task_id: str,
        assigned_to_id: str,
    ) -> BackgroundJob:
        job = await self.jobs.create(
            workspace_id=workspace_id,
            job_type="task_assignment_email",
            payload={
                "task_id": task_id,
                "assigned_to_id": assigned_to_id,
            },
        )
        if not self.settings.enable_background_jobs:
            await self.jobs.set_status(
                job,
                status=BackgroundJobStatus.SKIPPED,
                result={"reason": "background_jobs_disabled"},
            )
            logger.info("Skipped task assignment email job %s", job.id)
            return job

        from app.workers.jobs import send_task_assignment_email

        send_task_assignment_email.apply_async(args=[job.id], countdown=1)
        logger.info("Queued task assignment email job %s", job.id)
        return job
