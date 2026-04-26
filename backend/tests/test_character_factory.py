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
    async def test_generate_mature_with_ipadapter_samples_single_trigger_word(self):
        from app.services.character_factory import CharacterFactory

        factory = CharacterFactory()

        novita = MagicMock()
        novita.DEFAULT_MODEL = "mock-model"
        novita._download_image_base64 = AsyncMock(return_value="base64")
        novita.img2img_async = AsyncMock(return_value="task_1")
        novita.wait_for_task = AsyncMock(return_value=MagicMock(image_url="https://novita.example/mature.png"))

        loras = [{
            "name": "NsfwPovAllInOneLoraSdxl",
            "model_name": "NsfwPovAllInOneLoraSdxl",
            "strength": 0.8,
            "trigger_word": "reverse gang bang,sidefuck,undressing",
            "prompt_template_mode": "append_trigger",
        }]

        with patch("app.services.character_factory.random.choice", return_value="sidefuck"):
            with patch("app.services.character_factory.storage_service") as mock_storage:
                mock_storage.upload_from_url = AsyncMock(return_value="https://r2.example.com/mature.png")

                result = await factory._generate_mature_with_ipadapter(
                    novita,
                    name="Test",
                    age=25,
                    ethnicity_style={"avatar": "woman"},
                    personality="playful",
                    sfw_avatar_url="https://r2.example.com/avatar.png",
                    loras=loras,
                )

        assert result == "https://r2.example.com/mature.png"
        prompt = novita.img2img_async.await_args.kwargs["prompt"]
        assert prompt.startswith("sidefuck, ")
        assert "reverse gang bang,sidefuck,undressing" not in prompt
        assert novita.img2img_async.await_args.kwargs["strength"] == 0.72
        assert novita.img2img_async.await_args.kwargs["seed"] > 0

    @pytest.mark.asyncio
    async def test_generate_character_images_skips_mature_when_sfw_fails(self):
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
        novita_provider.txt2img_async = AsyncMock(side_effect=Exception("sfw avatar failed"))
        novita_provider.wait_for_task = AsyncMock()

        with patch.object(factory, '_get_txt2img_provider', return_value=novita_provider):
            with patch('app.services.character_factory.storage_service') as mock_storage:
                mock_storage.upload_from_url = AsyncMock(
                    side_effect=lambda url, folder=None: (
                        f"https://r2.example.com/{url.rsplit('/', 1)[-1]}"
                    )
                )

                images = await factory._generate_character_images(profile)

        assert images == {}
        assert novita_provider.img2img_async.await_count == 0
        assert novita_provider.txt2img_async.await_count == 1

    def test_assign_batch_visual_briefs_spreads_choices_and_seeds(self):
        from app.services.character_factory import CharacterFactory

        profiles = [{"name": f"Character {i}"} for i in range(5)]

        CharacterFactory._assign_batch_visual_briefs(profiles)

        briefs = [profile["_visual_brief"] for profile in profiles]
        avatar_backgrounds = [brief["avatar"]["background"] for brief in briefs]
        avatar_poses = [brief["avatar"]["pose"] for brief in briefs]
        mature_backgrounds = [brief["mature"]["background"] for brief in briefs]
        video_motions = [brief["video"]["motion"] for brief in briefs]
        seeds = [
            brief[section]["seed"]
            for brief in briefs
            for section in ("avatar", "mature", "video")
        ]

        assert len(set(avatar_backgrounds)) == len(avatar_backgrounds)
        assert len(set(avatar_poses)) == len(avatar_poses)
        assert len(set(mature_backgrounds)) == len(mature_backgrounds)
        assert len(set(video_motions)) == len(video_motions)
        assert all(isinstance(seed, int) and seed > 0 for seed in seeds)
        assert len(set(seeds)) == len(seeds)

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

    @pytest.mark.asyncio
    async def test_generate_character_images_retries_mature_prompt_three_times(self):
        from app.services.character_factory import CharacterFactory

        factory = CharacterFactory()
        profile = {
            "name": "Retry Character",
            "age": 25,
            "ethnicity": "asian",
            "occupation": "college_student",
            "personality_tags": ["playful"],
        }

        novita_provider = MagicMock()
        novita_provider.txt2img_async = AsyncMock(return_value="task_avatar")
        novita_provider.wait_for_task = AsyncMock(
            return_value=MagicMock(image_url="https://novita.example/avatar.png")
        )

        with patch.object(factory, "_get_txt2img_provider", new_callable=AsyncMock) as mock_provider:
            with patch.object(factory, "_select_lora_from_db", new_callable=AsyncMock) as mock_select_lora:
                with patch.object(factory, "_generate_mature_with_ipadapter", new_callable=AsyncMock) as mock_mature:
                    with patch("app.services.character_factory.storage_service") as mock_storage:
                        mock_provider.return_value = novita_provider
                        mock_select_lora.return_value = []
                        mock_mature.side_effect = [
                            None,
                            None,
                            "https://r2.example.com/mature-final.png",
                        ]
                        mock_storage.upload_from_url = AsyncMock(
                            return_value="https://r2.example.com/avatar.png"
                        )

                        images = await factory._generate_character_images(profile)

        assert images["mature_image_url"] == "https://r2.example.com/mature-final.png"
        assert images["mature_cover_url"] == "https://r2.example.com/mature-final.png"
        assert mock_mature.await_count == 3
        personalities = [call.kwargs["personality"] for call in mock_mature.await_args_list]
        assert personalities[0] == "playful"
        assert "seductive" in personalities[1]
        assert "intimate lighting" in personalities[2]

    @pytest.mark.asyncio
    async def test_generate_character_images_mature_missing_after_three_retries(self):
        from app.services.character_factory import CharacterFactory

        factory = CharacterFactory()
        profile = {
            "name": "Retry Fail Character",
            "age": 24,
            "ethnicity": "latina",
            "occupation": "college_student",
            "personality_tags": ["confident"],
        }

        novita_provider = MagicMock()
        novita_provider.txt2img_async = AsyncMock(return_value="task_avatar")
        novita_provider.wait_for_task = AsyncMock(
            return_value=MagicMock(image_url="https://novita.example/avatar.png")
        )

        with patch.object(factory, "_get_txt2img_provider", new_callable=AsyncMock) as mock_provider:
            with patch.object(factory, "_select_lora_from_db", new_callable=AsyncMock) as mock_select_lora:
                with patch.object(factory, "_generate_mature_with_ipadapter", new_callable=AsyncMock) as mock_mature:
                    with patch("app.services.character_factory.storage_service") as mock_storage:
                        mock_provider.return_value = novita_provider
                        mock_select_lora.return_value = []
                        mock_mature.side_effect = [None, None, None]
                        mock_storage.upload_from_url = AsyncMock(
                            return_value="https://r2.example.com/avatar.png"
                        )

                        images = await factory._generate_character_images(profile)

        assert images["avatar_url"] == "https://r2.example.com/avatar.png"
        assert "mature_image_url" not in images
        assert "mature_cover_url" not in images
        assert mock_mature.await_count == 3


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
