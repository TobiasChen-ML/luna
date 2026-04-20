import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio


class TestCharacterFactoryLLMFallback:
    """Test LLM fallback paths in character_factory.py"""

    @pytest.mark.asyncio
    async def test_llm_api_failure_uses_defaults(self):
        """When LLM API fails, should use default profile values"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        with patch.object(factory, '_get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate.side_effect = Exception("API connection failed")
            mock_get_llm.return_value = mock_llm
            
            profiles = await factory._generate_ai_profiles(count=1, top_category="girls")
            
            assert len(profiles) == 1
            profile = profiles[0]
            assert "year-old" in profile["description"]
            assert profile["backstory"] == ""
            assert "Hi, I'm" in profile["greeting"]

    @pytest.mark.asyncio
    async def test_llm_invalid_json_uses_defaults(self):
        """When LLM returns invalid JSON, should use default profile values"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        with patch.object(factory, '_get_llm_service') as mock_get_llm:
            mock_response = MagicMock()
            mock_response.content = "This is not valid JSON"
            mock_llm = AsyncMock()
            mock_llm.generate.return_value = mock_response
            mock_get_llm.return_value = mock_llm
            
            profiles = await factory._generate_ai_profiles(count=1)
            
            assert len(profiles) == 1
            assert profiles[0]["backstory"] == ""

    @pytest.mark.asyncio
    async def test_llm_empty_response_uses_defaults(self):
        """When LLM returns empty response, should use default profile values"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        with patch.object(factory, '_get_llm_service') as mock_get_llm:
            mock_response = MagicMock()
            mock_response.content = ""
            mock_llm = AsyncMock()
            mock_llm.generate.return_value = mock_response
            mock_get_llm.return_value = mock_llm
            
            profiles = await factory._generate_ai_profiles(count=1)
            
            assert len(profiles) == 1
            assert profiles[0]["backstory"] == ""

    @pytest.mark.asyncio
    async def test_llm_timeout_uses_defaults(self):
        """When LLM times out, should use default profile values"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        with patch.object(factory, '_get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate.side_effect = asyncio.TimeoutError()
            mock_get_llm.return_value = mock_llm
            
            profiles = await factory._generate_ai_profiles(count=1)
            
            assert len(profiles) == 1
            assert profiles[0]["backstory"] == ""

    @pytest.mark.asyncio
    async def test_llm_json_with_markdown_code_block(self):
        """When LLM returns JSON wrapped in markdown code block, should parse correctly"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        with patch.object(factory, '_get_llm_service') as mock_get_llm:
            mock_response = MagicMock()
            mock_response.content = '''```json
{"description": "A gentle woman", "personality_summary": "Caring", "backstory": "From Paris", "greeting": "Hello!"}
```'''
            mock_llm = AsyncMock()
            mock_llm.generate.return_value = mock_response
            mock_get_llm.return_value = mock_llm
            
            profiles = await factory._generate_ai_profiles(count=1)
            
            assert len(profiles) == 1
            assert profiles[0]["description"] == "A gentle woman"
            assert profiles[0]["backstory"] == "From Paris"

    @pytest.mark.asyncio
    async def test_generate_batch_continues_on_partial_failure(self):
        """Batch generation should continue even if some character creations fail"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        profiles_data = [
            {"name": "Emma", "first_name": "Emma", "age": 25, "gender": "female",
             "top_category": "girls", "personality_tags": ["gentle"],
             "description": "Test", "greeting": "Hi", "backstory": "", "generation_mode": "batch"},
            {"name": "Sophia", "first_name": "Sophia", "age": 26, "gender": "female",
             "top_category": "girls", "personality_tags": ["caring"],
             "description": "Test", "greeting": "Hi", "backstory": "", "generation_mode": "batch"},
        ]
        
        with patch.object(factory, '_generate_ai_profiles', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = profiles_data
        with patch.object(factory, '_generate_character_images', new_callable=AsyncMock) as mock_img:
            mock_img.return_value = {"avatar_url": "http://example.com/a.jpg"}
        with patch.object(factory, '_generate_seo_content', new_callable=AsyncMock) as mock_seo:
            mock_seo.return_value = {"slug": "test-slug"}
        with patch('app.services.character_factory.character_service') as mock_svc:
            mock_svc.create_character = AsyncMock(side_effect=[
                {"id": "c1", "name": "Emma"},
                Exception("DB error"),
            ])
            
            result = await factory.generate_batch(count=2, generate_images=False)
            
            assert len(result) == 1
            assert result[0]["name"] == "Emma"

    @pytest.mark.asyncio
    async def test_generate_batch_all_fail_returns_empty_list(self):
        """When all character creations fail, should return empty list"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        profiles_data = [
            {"name": "Emma", "first_name": "Emma", "age": 25, "gender": "female",
             "top_category": "girls", "personality_tags": ["gentle"],
             "description": "Test", "greeting": "Hi", "backstory": "", "generation_mode": "batch"},
        ]
        
        with patch.object(factory, '_generate_ai_profiles', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = profiles_data
        with patch.object(factory, '_generate_character_images', new_callable=AsyncMock) as mock_img:
            mock_img.return_value = {}
        with patch.object(factory, '_generate_seo_content', new_callable=AsyncMock) as mock_seo:
            mock_seo.return_value = {"slug": "test"}
        with patch('app.services.character_factory.character_service') as mock_svc:
            mock_svc.create_character = AsyncMock(side_effect=Exception("DB error"))
            
            result = await factory.generate_batch(count=1, generate_images=False)
            
            assert result == []


class TestCharacterFactoryProfileGeneration:
    """Test profile generation with various parameters"""

    @pytest.mark.asyncio
    async def test_profile_age_range_respected(self):
        """Generated profile age should be within specified range"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        with patch.object(factory, '_get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate.side_effect = Exception("Skip LLM")
            mock_get_llm.return_value = mock_llm
            
            for _ in range(10):
                profiles = await factory._generate_ai_profiles(
                    count=1, age_min=25, age_max=35
                )
                assert 25 <= profiles[0]["age"] <= 35

    @pytest.mark.asyncio
    async def test_profile_personality_preferences_used(self):
        """Generated profile should use provided personality preferences"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        custom_traits = ["mysterious", "intellectual", "wise"]
        
        with patch.object(factory, '_get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate.side_effect = Exception("Skip LLM")
            mock_get_llm.return_value = mock_llm
            
            profiles = await factory._generate_ai_profiles(
                count=1, personality_preferences=custom_traits
            )
            
            for tag in profiles[0]["personality_tags"]:
                assert tag in custom_traits


class TestCharacterFactoryMatureFallbacks:
    """Test Mature fallback paths in character_factory.py"""

    @pytest.mark.asyncio
    async def test_generate_character_images_mature_falls_back_to_txt2img_when_sfw_fails(self):
        from app.services.character_factory import CharacterFactory

        factory = CharacterFactory()
        profile = {
            "name": "Test Character",
            "age": 25,
            "ethnicity": "asian",
            "occupation": "college_student",
            "personality_tags": ["playful"],
        }

        novita_provider = MagicMock()
        novita_provider.img2img_async = AsyncMock()
        # SFW avatar + cover fail; Mature avatar + cover txt2img succeed
        novita_provider.txt2img_async = AsyncMock(side_effect=[
            Exception("sfw avatar failed"),
            Exception("sfw cover failed"),
            "task_mature_avatar",
            "task_mature_cover",
        ])
        novita_provider.wait_for_task = AsyncMock(side_effect=[
            MagicMock(image_url="https://novita.example/mature-avatar.png"),
            MagicMock(image_url="https://novita.example/mature-cover.png"),
        ])

        with patch.object(factory, '_get_novita_image_provider', return_value=novita_provider):
            with patch('app.services.character_factory.storage_service') as mock_storage:
                mock_storage.upload_from_url = AsyncMock(
                    side_effect=lambda url, folder=None: (
                        f"https://r2.example.com/{url.rsplit('/', 1)[-1]}"
                    )
                )

                images = await factory._generate_character_images(profile)

        assert images["mature_image_url"] == "https://r2.example.com/mature-avatar.png"
        assert images["mature_cover_url"] == "https://r2.example.com/mature-cover.png"
        # No source images → img2img skipped, txt2img called 4 times total (2 SFW fail + 2 Mature)
        assert novita_provider.img2img_async.await_count == 0
        assert novita_provider.txt2img_async.await_count == 4

    @pytest.mark.asyncio
    async def test_generate_batch_uses_mature_cover_for_video(self):
        from app.services.character_factory import CharacterFactory

        factory = CharacterFactory()
        profile = {
            "name": "Emma",
            "first_name": "Emma",
            "age": 25,
            "gender": "female",
            "top_category": "girls",
            "personality_tags": ["gentle"],
            "description": "Test",
            "greeting": "Hi",
            "backstory": "",
            "generation_mode": "batch",
        }

        with patch.object(factory, '_generate_ai_profiles', new_callable=AsyncMock) as mock_profiles:
            with patch.object(factory, '_generate_character_images', new_callable=AsyncMock) as mock_images:
                with patch.object(factory, '_generate_seo_content', new_callable=AsyncMock) as mock_seo:
                    with patch.object(factory, '_generate_character_video', new_callable=AsyncMock) as mock_video:
                        with patch('app.services.character_factory.character_service') as mock_svc:
                            mock_profiles.return_value = [profile]
                            mock_images.return_value = {"mature_cover_url": "https://example.com/mature-cover.png"}
                            mock_seo.return_value = {"slug": "test-slug"}
                            mock_video.return_value = "https://example.com/video.mp4"
                            mock_svc.create_character = AsyncMock(return_value={"id": "c1", "name": "Emma"})

                            result = await factory.generate_batch(
                                count=1,
                                generate_images=True,
                                generate_video=True,
                                optimize_seo=False,
                            )

        assert len(result) == 1
        mock_video.assert_awaited_once()
        assert mock_video.call_args[0][1] == "https://example.com/mature-cover.png"


class TestCharacterFactoryRegenerateImages:
    """Test regenerate_images functionality"""

    @pytest.mark.asyncio
    async def test_regenerate_images_character_not_found(self):
        """Should raise ValueError when character doesn't exist"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        with patch('app.services.character_factory.character_service') as mock_svc:
            mock_svc.get_character_by_id = AsyncMock(return_value=None)
            
            with pytest.raises(ValueError, match="Character not found"):
                await factory.regenerate_images("non_existent_id")

    @pytest.mark.asyncio
    async def test_regenerate_images_success(self):
        """Should update character with new images"""
        from app.services.character_factory import CharacterFactory
        from app.models.character import CharacterUpdate
        
        factory = CharacterFactory()
        
        mock_character = {
            "id": "char_001",
            "name": "Test Character",
            "gender": "female",
        }
        
        mock_updated_character = {
            "id": "char_001",
            "name": "Test Character",
            "avatar_url": "https://r2.example.com/new_avatar.png",
            "cover_url": "https://r2.example.com/new_cover.png",
            "avatar_card_url": "https://r2.example.com/new_card.png",
        }
        
        with patch('app.services.character_factory.character_service') as mock_svc:
            with patch.object(factory, '_generate_character_images', new_callable=AsyncMock) as mock_gen_img:
                mock_svc.get_character_by_id = AsyncMock(return_value=mock_character)
                mock_svc.update_character = AsyncMock(return_value=mock_updated_character)
                mock_gen_img.return_value = {
                    "avatar_url": "https://r2.example.com/new_avatar.png",
                    "cover_url": "https://r2.example.com/new_cover.png",
                    "avatar_card_url": "https://r2.example.com/new_card.png",
                }
                
                result = await factory.regenerate_images("char_001")
                
                assert result is not None
                assert result["avatar_url"] == "https://r2.example.com/new_avatar.png"
                mock_gen_img.assert_called_once_with(mock_character)
                mock_svc.update_character.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_images_partial_images(self):
        """Should only update fields that have new images"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        mock_character = {
            "id": "char_001",
            "name": "Test Character",
        }
        
        mock_updated_character = {
            "id": "char_001",
            "name": "Test Character",
            "avatar_url": "https://r2.example.com/new_avatar.png",
        }
        
        with patch('app.services.character_factory.character_service') as mock_svc:
            with patch.object(factory, '_generate_character_images', new_callable=AsyncMock) as mock_gen_img:
                mock_svc.get_character_by_id = AsyncMock(return_value=mock_character)
                mock_svc.update_character = AsyncMock(return_value=mock_updated_character)
                mock_gen_img.return_value = {
                    "avatar_url": "https://r2.example.com/new_avatar.png",
                }
                
                result = await factory.regenerate_images("char_001")
                
                assert result is not None
                mock_svc.update_character.assert_called_once()
                call_args = mock_svc.update_character.call_args
                update_data = call_args[0][1]
                assert hasattr(update_data, 'avatar_url')
                assert update_data.avatar_url == "https://r2.example.com/new_avatar.png"

    @pytest.mark.asyncio
    async def test_regenerate_images_empty_images(self):
        """Should still call update_character even with no new images"""
        from app.services.character_factory import CharacterFactory
        
        factory = CharacterFactory()
        
        mock_character = {
            "id": "char_001",
            "name": "Test Character",
        }
        
        mock_updated_character = {
            "id": "char_001",
            "name": "Test Character",
        }
        
        with patch('app.services.character_factory.character_service') as mock_svc:
            with patch.object(factory, '_generate_character_images', new_callable=AsyncMock) as mock_gen_img:
                mock_svc.get_character_by_id = AsyncMock(return_value=mock_character)
                mock_svc.update_character = AsyncMock(return_value=mock_updated_character)
                mock_gen_img.return_value = {}
                
                result = await factory.regenerate_images("char_001")
                
                assert result is not None
                mock_svc.update_character.assert_called_once()
