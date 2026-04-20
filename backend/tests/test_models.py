import pytest
from datetime import datetime

from app.models.schemas import (
    User, Character, Story, Task, TaskStatus,
    SubscriptionTier, ChatSession, ChatMessage,
    CharacterCreate, StoryCreate
)


class TestUser:
    def test_user_creation(self):
        user = User(
            id="user_001",
            email="test@example.com",
            display_name="Test User",
            subscription_tier=SubscriptionTier.FREE,
            credits=100,
            created_at=datetime.now()
        )
        assert user.id == "user_001"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.credits == 100

    def test_user_default_tier(self):
        user = User(
            id="user_002",
            created_at=datetime.now()
        )
        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.credits == 0


class TestCharacter:
    def test_character_creation(self):
        char = Character(
            id="char_001",
            name="Test Character",
            slug="test-character",
            description="A test character",
            created_at=datetime.now()
        )
        assert char.id == "char_001"
        assert char.name == "Test Character"
        assert char.slug == "test-character"
        assert char.is_public is True
        assert char.tags == []

    def test_character_create_schema(self):
        char_data = CharacterCreate(
            name="New Character",
            slug="new-character",
            description="Description",
            tags=["tag1", "tag2"]
        )
        assert char_data.name == "New Character"
        assert len(char_data.tags) == 2


class TestStory:
    def test_story_creation(self):
        story = Story(
            id="story_001",
            title="Test Story",
            character_id="char_001",
            created_at=datetime.now()
        )
        assert story.id == "story_001"
        assert story.title == "Test Story"
        assert story.character_id == "char_001"
        assert story.nodes == []

    def test_story_create_schema(self):
        story_data = StoryCreate(
            title="New Story",
            character_id="char_001",
            nodes=[{"id": "node_1", "content": "Start"}]
        )
        assert story_data.title == "New Story"
        assert len(story_data.nodes) == 1


class TestTask:
    def test_task_creation(self):
        task = Task(
            id="task_001",
            type="image_generation",
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        assert task.id == "task_001"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0

    def test_task_with_result(self):
        task = Task(
            id="task_002",
            type="video_generation",
            status=TaskStatus.COMPLETED,
            result={"url": "https://example.com/video.mp4"},
            created_at=datetime.now()
        )
        assert task.status == TaskStatus.COMPLETED
        assert task.result["url"] == "https://example.com/video.mp4"


class TestChatSession:
    def test_session_creation(self):
        session = ChatSession(
            id="session_001",
            user_id="user_001",
            character_id="char_001",
            created_at=datetime.now()
        )
        assert session.id == "session_001"
        assert session.user_id == "user_001"
        assert session.character_id == "char_001"


class TestChatMessage:
    def test_message_creation(self):
        msg = ChatMessage(
            id="msg_001",
            session_id="session_001",
            role="user",
            content="Hello!",
            created_at=datetime.now()
        )
        assert msg.id == "msg_001"
        assert msg.role == "user"
        assert msg.content == "Hello!"