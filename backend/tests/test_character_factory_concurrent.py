"""
Concurrent tests for POST /admin/api/characters/from-template.

Tests verify:
1. Concurrent requests complete without race conditions
2. Partial failures don't crash the endpoint
3. Image generation failures don't block character creation
4. Correct response counts are returned

NOTE: generate_from_template() does NOT call LLM - it only uses random data
and template data. LLM is only used in generate_batch() via _generate_ai_profiles().

Slug uniqueness: The actual create_character() in character_service handles
slug conflicts by appending character ID suffix. Our mock simulates this behavior.
"""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.services.llm import LLMResponse


class TestConcurrentTemplateGeneration:
    """Tests for concurrent character generation from templates."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_character_factory_dependencies):
        self.mock_deps = mock_character_factory_dependencies
        yield

    @pytest.mark.asyncio
    async def test_concurrent_requests_all_succeed(self, async_admin_client):
        """
        5 concurrent requests should all return 200.
        """
        responses = await asyncio.gather(
            *[
                async_admin_client.post(
                    "/admin/api/characters/from-template",
                    json={
                        "template_id": "college_student",
                        "variations": 1,
                        "generate_images": False,
                        "optimize_seo": False,
                    }
                )
                for _ in range(5)
            ]
        )

        statuses = [r.status_code for r in responses]
        assert all(s == 200 for s in statuses), f"Expected all 200, got: {statuses}"

        for r in responses:
            data = r.json()
            assert data["success"] is True
            assert data["created_count"] == 1
            assert len(data["characters"]) == 1

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_templates(self, async_admin_client):
        """
        Concurrent requests with different templates should all succeed.
        """
        templates = ["college_student", "office_lady", "girl_next_door", "fitness_coach"]
        
        responses = await asyncio.gather(
            *[
                async_admin_client.post(
                    "/admin/api/characters/from-template",
                    json={
                        "template_id": template_id,
                        "variations": 1,
                        "generate_images": False,
                        "optimize_seo": False,
                    }
                )
                for template_id in templates
            ]
        )

        for i, r in enumerate(responses):
            assert r.status_code == 200, f"Template {templates[i]} failed: {r.text}"
            data = r.json()
            assert data["success"] is True
            assert data["created_count"] == 1
            assert data["characters"][0]["template_id"] == templates[i]

    @pytest.mark.asyncio
    async def test_single_request_multiple_variations(self, async_admin_client):
        """
        Single request with variations=3 should create 3 characters.
        """
        response = await async_admin_client.post(
            "/admin/api/characters/from-template",
            json={
                "template_id": "romantic_artist",
                "variations": 3,
                "generate_images": False,
                "optimize_seo": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["created_count"] == 3
        assert len(data["characters"]) == 3

    @pytest.mark.asyncio
    async def test_image_generation_failure_continues(self, async_admin_client):
        """
        Image generation failure should not prevent character creation.
        The exception is caught and character is still created (just without images).
        """
        self.mock_deps["media"].generate_image = AsyncMock(
            side_effect=Exception("Image generation failed")
        )

        response = await async_admin_client.post(
            "/admin/api/characters/from-template",
            json={
                "template_id": "mystic_witch",
                "variations": 1,
                "generate_images": True,
                "optimize_seo": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["created_count"] == 1
        assert len(data["characters"]) == 1

    @pytest.mark.asyncio
    async def test_all_create_failures_returns_empty(self, async_admin_client):
        """
        When all create_character calls fail, should return empty list (not error).
        """
        self.mock_deps["create_character"].side_effect = Exception("Database down")

        response = await async_admin_client.post(
            "/admin/api/characters/from-template",
            json={
                "template_id": "office_lady",
                "variations": 3,
                "generate_images": False,
                "optimize_seo": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["created_count"] == 0
        assert len(data["characters"]) == 0

    @pytest.mark.asyncio
    async def test_upload_failure_with_image_generation(self, async_admin_client):
        """
        Upload failure should not prevent character creation when generate_images=True.
        """
        self.mock_deps["upload"].side_effect = Exception("R2 upload failed")

        response = await async_admin_client.post(
            "/admin/api/characters/from-template",
            json={
                "template_id": "girl_next_door",
                "variations": 1,
                "generate_images": True,
                "optimize_seo": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["created_count"] == 1


class TestTemplateGenerationEdgeCases:
    """Edge case tests for template-based character generation."""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self):
        """
        Requests without admin authentication should be rejected.
        """
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/admin/api/characters/from-template",
                json={
                    "template_id": "college_student",
                    "variations": 1,
                }
            )

        assert response.status_code in [401, 403]


class TestTemplateGenerationKnownIssues:
    """
    Tests for previously known issues that have been fixed.
    """

    @pytest.mark.asyncio
    async def test_invalid_template_id_returns_400(self, async_admin_client, mock_character_factory_dependencies):
        """
        Fixed: Invalid template_id now returns 400 instead of 500.
        """
        response = await async_admin_client.post(
            "/admin/api/characters/from-template",
            json={
                "template_id": "nonexistent_template",
                "variations": 1,
                "generate_images": False,
                "optimize_seo": False,
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_variations_zero_returns_422(self, async_admin_client, mock_character_factory_dependencies):
        """
        Fixed: Pydantic validation error now returns 422 instead of 500.
        Using FastAPI's automatic request body validation.
        """
        response = await async_admin_client.post(
            "/admin/api/characters/from-template",
            json={
                "template_id": "college_student",
                "variations": 0,
                "generate_images": False,
                "optimize_seo": False,
            }
        )

        assert response.status_code == 422


class TestTemplateGenerationSlugHandling:
    """Tests for slug generation and conflict handling."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_character_factory_dependencies):
        self.mock_deps = mock_character_factory_dependencies
        yield

    @pytest.mark.asyncio
    async def test_slug_format_is_valid(self, async_admin_client):
        """
        Generated slugs should be valid (no special chars, no leading/trailing hyphens).
        """
        response = await async_admin_client.post(
            "/admin/api/characters/from-template",
            json={
                "template_id": "college_student",
                "variations": 1,
                "generate_images": False,
                "optimize_seo": True,
            }
        )

        assert response.status_code == 200
        slug = response.json()["characters"][0]["slug"]
        
        assert len(slug) > 0
        assert "--" not in slug, f"Double hyphen in slug: {slug}"
        assert not slug.startswith("-"), f"Leading hyphen in slug: {slug}"
        assert not slug.endswith("-"), f"Trailing hyphen in slug: {slug}"

    @pytest.mark.asyncio
    async def test_slug_with_special_characters_cleaned(self, async_admin_client):
        """
        Names with special characters should produce clean slugs.
        """
        from unittest.mock import patch
        import random

        special_names = ["O'Brien", "Mary-Jane"]

        with patch.object(random, "choice", side_effect=special_names):
            response = await async_admin_client.post(
                "/admin/api/characters/from-template",
                json={
                    "template_id": "office_lady",
                    "variations": 1,
                    "generate_images": False,
                    "optimize_seo": True,
                }
            )

        assert response.status_code == 200
        slug = response.json()["characters"][0]["slug"]
        
        assert "--" not in slug
        assert not slug.startswith("-")
        assert not slug.endswith("-")


class TestTemplateGenerationHighConcurrency:
    """High concurrency stress tests."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_character_factory_dependencies):
        self.mock_deps = mock_character_factory_dependencies
        yield

    @pytest.mark.asyncio
    async def test_10_concurrent_requests_all_succeed(self, async_admin_client):
        """
        10 concurrent requests should all succeed.
        """
        responses = await asyncio.gather(
            *[
                async_admin_client.post(
                    "/admin/api/characters/from-template",
                    json={
                        "template_id": "college_student",
                        "variations": 1,
                        "generate_images": False,
                        "optimize_seo": False,
                    }
                )
                for _ in range(10)
            ]
        )

        statuses = [r.status_code for r in responses]
        assert all(s == 200 for s in statuses), f"Failed statuses: {[s for s in statuses if s != 200]}"

    @pytest.mark.asyncio
    async def test_concurrent_different_variations_counts(self, async_admin_client):
        """
        Concurrent requests with different variation counts should all work correctly.
        """
        variation_counts = [1, 2, 3]
        
        responses = await asyncio.gather(
            *[
                async_admin_client.post(
                    "/admin/api/characters/from-template",
                    json={
                        "template_id": "fitness_coach",
                        "variations": count,
                        "generate_images": False,
                        "optimize_seo": False,
                    }
                )
                for count in variation_counts
            ]
        )

        for i, (r, expected_count) in enumerate(zip(responses, variation_counts)):
            assert r.status_code == 200
            data = r.json()
            assert data["created_count"] == expected_count

    @pytest.mark.asyncio
    async def test_concurrent_all_templates(self, async_admin_client):
        """
        Concurrent requests using all 8 templates should all succeed.
        """
        templates = [
            "college_student", "office_lady", "girl_next_door", "romantic_artist",
            "fitness_coach", "mystic_witch", "sweet_barista", "boss_lady"
        ]
        
        responses = await asyncio.gather(
            *[
                async_admin_client.post(
                    "/admin/api/characters/from-template",
                    json={
                        "template_id": template_id,
                        "variations": 1,
                        "generate_images": False,
                        "optimize_seo": False,
                    }
                )
                for template_id in templates
            ]
        )

        for i, r in enumerate(responses):
            assert r.status_code == 200, f"Template {templates[i]} failed"
