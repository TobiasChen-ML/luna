from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional
import logging

from ..services import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["tasks"])

task_service = TaskService()


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    from ..services import FirebaseService
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization[7:]
    decoded = FirebaseService().verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded.get("uid")


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.task_id,
        "type": task.task_type,
        "provider": task.provider,
        "status": task.status,
        "progress": task.progress,
        "result_url": task.result_url,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_current_user),
) -> dict:
    tasks, total = await task_service.list_tasks(
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "type": t.task_type,
                "status": t.status,
                "progress": t.progress,
                "result_url": t.result_url,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/media/tasks/{task_id}")
async def get_media_task(task_id: str) -> dict:
    return await get_task(task_id)


@router.post("/media/provider-webhook/{provider}")
async def provider_webhook(
    provider: str,
    request: Request,
) -> dict:
    payload = await request.json()
    
    task_id = payload.get("task_id") or payload.get("request_id")
    
    if task_id:
        task = await task_service.handle_webhook(task_id, payload)
        if task:
            return {
                "task_id": task_id,
                "status": task.status,
            }
    
    return {"status": "received", "provider": provider}


@router.post("/callbacks/novita")
async def novita_callback(request: Request) -> dict:
    payload = await request.json()
    task_id = payload.get("task_id") or payload.get("request_id")
    
    if task_id:
        task = await task_service.handle_webhook(task_id, payload)
        if task:
            return {"task_id": task_id, "status": task.status}
    
    return {"status": "received"}


@router.post("/callbacks/media")
async def media_callback(request: Request) -> dict:
    payload = await request.json()
    task_id = payload.get("task_id") or payload.get("request_id")
    
    if task_id:
        task = await task_service.handle_webhook(task_id, payload)
        if task:
            return {"task_id": task_id, "status": task.status}
    
    return {"status": "received"}


@router.get("/admin/characters/quick-create/status/{task_id}")
async def quick_create_status(task_id: str) -> dict:
    return await get_task(task_id)


@router.get("/admin/api/batch-jobs/{batch_job_id}")
async def admin_batch_job_status(batch_job_id: str) -> dict:
    from ..services import AdminService
    admin_service = AdminService()
    
    job = await admin_service.get_batch_job(batch_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
