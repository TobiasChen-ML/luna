from unittest.mock import AsyncMock


class TestRewardsRouter:
    async def _mock_claim(self, monkeypatch, result=None, side_effect=None):
        from app.routers import rewards

        mock = AsyncMock()
        if side_effect is not None:
            mock.side_effect = side_effect
        else:
            mock.return_value = result
        monkeypatch.setattr(rewards.reward_service, "claim_share_reward", mock)
        return mock

    def test_claim_share_reward_success(self, client, monkeypatch):
        payload = {
            "success": True,
            "granted": True,
            "reason": "granted",
            "reward_amount": 10,
            "new_balance": 120.0,
        }
        mock = AsyncMock(return_value=payload)
        from app.routers import rewards
        monkeypatch.setattr(rewards.reward_service, "claim_share_reward", mock)

        response = client.post(
            "/api/rewards/share/claim",
            json={"share_key": "gallery:item_1", "channel": "gallery_media"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["granted"] is True
        assert data["reward_amount"] == 10

    def test_claim_share_reward_duplicate(self, client, monkeypatch):
        payload = {
            "success": True,
            "granted": False,
            "reason": "duplicate",
            "reward_amount": 0,
            "new_balance": 120.0,
        }
        from app.routers import rewards
        monkeypatch.setattr(rewards.reward_service, "claim_share_reward", AsyncMock(return_value=payload))

        response = client.post(
            "/api/rewards/share/claim",
            json={"share_key": "gallery:item_1", "channel": "gallery_media"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["granted"] is False
        assert data["reason"] == "duplicate"

    def test_claim_share_reward_daily_limit(self, client, monkeypatch):
        payload = {
            "success": True,
            "granted": False,
            "reason": "daily_limit",
            "reward_amount": 0,
            "new_balance": 120.0,
            "daily_limit": 3,
        }
        from app.routers import rewards
        monkeypatch.setattr(rewards.reward_service, "claim_share_reward", AsyncMock(return_value=payload))

        response = client.post(
            "/api/rewards/share/claim",
            json={"share_key": "discover:char_1", "channel": "discover_profile"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reason"] == "daily_limit"
        assert data["daily_limit"] == 3

    def test_claim_share_reward_bad_request(self, client):
        response = client.post(
            "/api/rewards/share/claim",
            json={"share_key": "", "channel": "gallery_media"},
        )
        assert response.status_code == 422
