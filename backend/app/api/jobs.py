from fastapi import APIRouter, Depends, HTTPException
from rq.job import Job

from app.api.auth import get_current_user
from app.core.redis_client import get_redis_connection
from app.models.user import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    redis_conn = get_redis_connection()

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    # Security: only owner can view
    owner = job.meta.get("user_id")
    if owner and owner != str(current_user.id):
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.get_status(),
        "created_at": str(job.created_at) if job.created_at else None,
        "ended_at": str(job.ended_at) if job.ended_at else None,
        "result": job.result,
        "error": job.exc_info,
        "meta": job.meta,
    }