import pytest
from app.services.media_trigger_service import MediaTriggerService


class TestMediaTriggerService:
    @pytest.fixture
    def service(self):
        return MediaTriggerService()

    def test_service_singleton(self):
        service1 = MediaTriggerService.get_instance()
        service2 = MediaTriggerService.get_instance()
        
        assert service1 is service2

    def test_generation_tasks_initialization(self, service):
        assert hasattr(service, '_generation_tasks')
        assert isinstance(service._generation_tasks, dict)

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, service):
        result = await service.get_task_status("nonexistent_task")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_task_status_found(self, service):
        task_id = "test_task_001"
        service._generation_tasks[task_id] = {
            "status": "completed",
            "type": "image"
        }
        
        result = await service.get_task_status(task_id)
        
        assert result is not None
        assert result["status"] == "completed"
        
        del service._generation_tasks[task_id]

    @pytest.mark.asyncio
    async def test_can_trigger_node_not_found(self, service):
        result = await service.can_trigger(
            script_id="script_001",
            node_id="nonexistent_node",
            cue_id="cue_001",
            session_id="session_001"
        )
        
        assert result["allowed"] is False
        assert result["reason"] == "node_not_found"

    @pytest.mark.asyncio
    async def test_trigger_media_insufficient_intimacy(self, service):
        result = await service.trigger_media(
            script_id="script_001",
            node_id="node_001",
            cue_id="cue_001",
            session_id="session_001",
            user_id="user_001",
            character_id="char_001"
        )
        
        assert result["allowed"] is False


class TestMediaTriggerServiceMethods:
    @pytest.fixture
    def service(self):
        return MediaTriggerService()

    def test_service_has_required_methods(self, service):
        assert hasattr(service, 'can_trigger')
        assert hasattr(service, 'trigger_media')
        assert hasattr(service, 'get_task_status')
        assert hasattr(service, '_get_triggered_cues')
        assert hasattr(service, '_mark_cue_triggered')

    @pytest.mark.asyncio
    async def test_get_triggered_cues_empty(self, service):
        result = await service._get_triggered_cues("nonexistent_session")
        
        assert result == []
