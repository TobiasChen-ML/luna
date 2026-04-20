import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.routers.admin.audit import router
from app.services.audit_service import AuditService, AuditAction


class TestAuditService:
    @pytest.mark.asyncio
    async def test_log_action(self):
        service = AuditService()
        
        with patch('app.services.audit_service.db') as mock_db:
            mock_db.execute = AsyncMock(return_value=1)
            
            log_id = await service.log_action(
                admin_id="admin-001",
                admin_email="admin@test.com",
                action=AuditAction.CREDIT_ADJUST.value,
                resource_type="user",
                resource_id="user-001",
                old_value={"balance": 100},
                new_value={"balance": 150, "adjustment": 50},
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
            )
            
            assert log_id == 1
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logs_with_filters(self):
        service = AuditService()
        
        mock_logs = [
            {
                "id": 1,
                "admin_id": "admin-001",
                "admin_email": "admin@test.com",
                "action": "credit_adjust",
                "resource_type": "user",
                "resource_id": "user-001",
                "old_value": '{"balance": 100}',
                "new_value": '{"balance": 150}',
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0",
                "metadata": None,
                "created_at": "2026-01-01T00:00:00",
            }
        ]
        
        with patch('app.services.audit_service.db') as mock_db:
            mock_db.execute = AsyncMock(side_effect=[
                {"count": 1},
                mock_logs,
            ])
            
            logs, total = await service.get_logs(
                action="credit_adjust",
                limit=10,
                offset=0,
            )
            
            assert total == 1
            assert len(logs) == 1
            mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_admin_activity_summary(self):
        service = AuditService()
        
        with patch('app.services.audit_service.db') as mock_db:
            mock_db.execute = AsyncMock(side_effect=[
                [{"action": "credit_adjust", "count": 5}],
                [{"admin_id": "admin-001", "admin_email": "admin@test.com", "count": 5}],
            ])
            
            summary = await service.get_admin_activity_summary(days=30)
            
            assert "total_actions" in summary
            assert "by_action" in summary
            assert "by_admin" in summary


class TestAuditActions:
    def test_audit_action_values(self):
        assert AuditAction.CHARACTER_CREATE.value == "character_create"
        assert AuditAction.CREDIT_ADJUST.value == "credit_adjust"
        assert AuditAction.USER_BAN.value == "user_ban"
        assert AuditAction.CREDIT_BATCH_ADJUST.value == "credit_batch_adjust"
