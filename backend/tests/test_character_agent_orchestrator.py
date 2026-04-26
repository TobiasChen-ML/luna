import pytest

from app.services.character_agent_orchestrator import CharacterAgentOrchestrator


class FakeLLM:
    async def detect_intent(self, user_message, context=None):
        return {"intent": "chat", "confidence": 0.1}


@pytest.mark.asyncio
async def test_selfie_request_routes_to_image_tool():
    orchestrator = CharacterAgentOrchestrator()

    plan = await orchestrator.plan_tool(
        user_message="can you take a selfie for me",
        character={"name": "Roxy"},
        llm_service=FakeLLM(),
    )

    assert plan.tool_name == "generate_image"
    assert plan.uses_media_tool is True


@pytest.mark.asyncio
async def test_video_request_routes_to_video_tool():
    orchestrator = CharacterAgentOrchestrator()

    plan = await orchestrator.plan_tool(
        user_message="can you make me a selfie video",
        character={"name": "Roxy"},
        llm_service=FakeLLM(),
    )

    assert plan.tool_name == "generate_video"
    assert plan.uses_media_tool is True
