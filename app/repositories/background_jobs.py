from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob, BackgroundJobStatus


class BackgroundJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, job_id: str) -> BackgroundJob | None:
        return await self.session.get(BackgroundJob, job_id)

    async def create(
        self,
        *,
        workspace_id: str | None,
        job_type: str,
        payload: dict,
    ) -> BackgroundJob:
        job = BackgroundJob(
            workspace_id=workspace_id,
            job_type=job_type,
            payload=payload,
            status=BackgroundJobStatus.QUEUED,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def set_status(
        self,
        job: BackgroundJob,
        *,
        status: BackgroundJobStatus,
        result: dict | None = None,
        error: str | None = None,
    ) -> BackgroundJob:
        job.status = status
        job.result = result
        job.error = error
        await self.session.flush()
        return job
