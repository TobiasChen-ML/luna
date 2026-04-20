import asyncio
import logging
from typing import Optional, Callable, Any
from ..core.config import get_settings
from ..models.task import Task

logger = logging.getLogger(__name__)


class TaskRegistryService:
    _providers: dict[str, Any] = {}
    _poll_interval: int = 5
    _max_poll_attempts: int = 60
    
    def __init__(self):
        self.settings = get_settings()
    
    @classmethod
    def register_provider(cls, name: str, provider: Any):
        cls._providers[name] = provider
    
    @classmethod
    def get_provider(cls, name: str) -> Optional[Any]:
        return cls._providers.get(name)
    
    async def submit_and_wait(
        self,
        task: Task,
        poll_callback: Optional[Callable] = None
    ) -> Task:
        provider = self._providers.get(task.provider)
        if not provider:
            logger.error(f"Provider {task.provider} not registered")
            return task
        
        if task.webhook_received:
            return task
        
        attempts = 0
        while attempts < self._max_poll_attempts:
            try:
                status = await provider.poll_status(task)
                
                if status.get("status") == "completed":
                    task.result_url = status.get("result_url")
                    task.status = "completed"
                    task.progress = 100.0
                    return task
                elif status.get("status") == "failed":
                    task.error_message = status.get("error", "Unknown error")
                    task.status = "failed"
                    return task
                
                if poll_callback:
                    await poll_callback(status)
                
                await asyncio.sleep(self._poll_interval)
                attempts += 1
            except Exception as e:
                logger.error(f"Poll error for task {task.task_id}: {e}")
                attempts += 1
                await asyncio.sleep(self._poll_interval)
        
        task.status = "timeout"
        task.error_message = "Polling timeout"
        return task
    
    async def submit_async(
        self,
        task: Task,
        webhook_url: Optional[str] = None
    ) -> Task:
        provider = self._providers.get(task.provider)
        if not provider:
            raise ValueError(f"Provider {task.provider} not registered")
        
        submit_data = {
            "task_id": task.task_id,
            "input_data": task.input_data,
            "webhook_url": webhook_url,
            "webhook_first": True
        }
        
        result = await provider.submit(submit_data)
        
        if result.get("success"):
            task.status = "processing"
        else:
            task.status = "failed"
            task.error_message = result.get("error", "Submit failed")
        
        return task
    
    async def handle_provider_callback(
        self,
        provider_name: str,
        payload: dict
    ) -> Optional[Task]:
        provider = self._providers.get(provider_name)
        if not provider:
            logger.error(f"Provider {provider_name} not registered")
            return None
        
        task_id = provider.extract_task_id(payload)
        if not task_id:
            logger.error("Could not extract task_id from callback payload")
            return None
        
        return await provider.handle_callback(task_id, payload)