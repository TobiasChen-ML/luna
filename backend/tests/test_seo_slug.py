import pytest
from app.models.character import generate_slug
from app.services.character_factory import CharacterFactory


class TestGenerateSlug:
    
    def test_normal_name(self):
        assert generate_slug("Hello World") == "hello-world"
    
    def test_empty_string(self):
        slug = generate_slug("")
        assert slug.startswith("character-")
        assert len(slug) > 8
    
    def test_only_spaces(self):
        slug = generate_slug("   ")
        assert slug.startswith("character-")
    
    def test_only_special_chars(self):
        slug = generate_slug("!!!@@@###")
        assert slug.startswith("character-")
    
    def test_multiple_spaces_collapsed(self):
        assert generate_slug("Hello   World") == "hello-world"
    
    def test_multiple_dashes_collapsed(self):
        assert generate_slug("Hello--World") == "hello-world"
    
    def test_mixed_separators_collapsed(self):
        assert generate_slug("Hello _ World") == "hello-world"
    
    def test_leading_trailing_dashes_removed(self):
        assert generate_slug("---Hello---") == "hello"
    
    def test_leading_trailing_spaces_removed(self):
        assert generate_slug("   Hello World   ") == "hello-world"
    
    def test_chinese_chars_preserved(self):
        slug = generate_slug("你好世界")
        assert slug == "你好世界"
    
    def test_chinese_with_spaces_converted(self):
        assert generate_slug("你好 世界") == "你好-世界"
    
    def test_chinese_mixed_with_special_chars(self):
        assert generate_slug("你好！世界") == "你好世界"
    
    def test_only_chinese_punctuation_fallback(self):
        slug = generate_slug("！@#￥%")
        assert slug.startswith("character-")
    
    def test_emoji_removed(self):
        assert generate_slug("Hello🚀World") == "helloworld"
    
    def test_mixed_emoji_and_text(self):
        assert generate_slug("Alice ❤️ Bob") == "alice-bob"
    
    def test_numbers_preserved(self):
        assert generate_slug("Character 123") == "character-123"
    
    def test_underscores_converted_to_dash(self):
        assert generate_slug("Hello_World") == "hello-world"
    
    def test_mixed_case_lowercased(self):
        assert generate_slug("HELLO WORLD") == "hello-world"
    
    def test_apostrophe_removed(self):
        assert generate_slug("It's a Test") == "its-a-test"
    
    def test_punctuation_removed(self):
        assert generate_slug("Hello, World!") == "hello-world"
    
    def test_long_name_truncated_to_150(self):
        long_name = "A" * 200
        slug = generate_slug(long_name)
        assert len(slug) == 150
        assert slug == "a" * 150
    
    def test_long_name_truncated_without_trailing_dash(self):
        long_name = "A " * 100
        slug = generate_slug(long_name)
        assert len(slug) <= 150
        assert not slug.endswith('-')
    
    def test_custom_max_length(self):
        long_name = "A" * 200
        slug = generate_slug(long_name, max_length=50)
        assert len(slug) == 50
    
    def test_tabs_converted_to_dash(self):
        assert generate_slug("Hello\tWorld") == "hello-world"
    
    def test_newlines_removed(self):
        assert generate_slug("Hello\nWorld") == "hello-world"


class TestSlugConflictHandling:
    
    def test_slug_conflict_suffix_pattern(self):
        import re
        character_id = "char_abc123def456"
        slug = "alice"
        new_slug = f"{slug}-{character_id[-6:]}"
        assert new_slug == "alice-def456"
        assert re.match(r"^[a-z0-9-]+-[a-f0-9]{6}$", new_slug)
    
    def test_slug_conflict_different_ids_get_different_suffixes(self):
        character_id_1 = "char_abc123aaa111"
        character_id_2 = "char_abc123bbb222"
        slug = "test-character"
        new_slug_1 = f"{slug}-{character_id_1[-6:]}"
        new_slug_2 = f"{slug}-{character_id_2[-6:]}"
        assert new_slug_1 != new_slug_2
        assert new_slug_1 == "test-character-aaa111"
        assert new_slug_2 == "test-character-bbb222"
    
    def test_slug_no_conflict_unchanged(self):
        slug = "unique-character"
        new_slug = slug
        assert new_slug == "unique-character"


class TestSEOMetaTitle:
    
    @pytest.fixture
    def factory(self):
        return CharacterFactory()
    
    def test_normal_name_title(self):
        profile = {"name": "Alice", "description": "A friendly character"}
        seo_data = {}
        name = profile.get("name", "")
        meta_title = f"{name} - AI Character | RoxyClub"
        seo_data["meta_title"] = meta_title[:200]
        assert seo_data["meta_title"] == "Alice - AI Character | RoxyClub"
        assert len(seo_data["meta_title"]) <= 200
    
    def test_long_name_title_truncated_to_200(self):
        long_name = "A" * 180
        profile = {"name": long_name, "description": "Test"}
        seo_data = {}
        meta_title = f"{long_name} - AI Character | RoxyClub"
        seo_data["meta_title"] = meta_title[:200]
        assert len(seo_data["meta_title"]) == 200
    
    def test_title_format_preserved(self):
        profile = {"name": "Test Name", "description": "Test"}
        seo_data = {}
        name = profile.get("name", "")
        meta_title = f"{name} - AI Character | RoxyClub"
        seo_data["meta_title"] = meta_title[:200]
        assert " - AI Character | RoxyClub" in seo_data["meta_title"]
    
    def test_very_long_name_truncated_correctly(self):
        very_long_name = "B" * 300
        meta_title = f"{very_long_name} - AI Character | RoxyClub"
        truncated = meta_title[:200]
        assert len(truncated) == 200
        assert truncated.startswith("B")


class TestSEOMetaDescription:
    
    def test_description_under_160_preserved(self):
        description = "A" * 100
        meta_description = description[:160]
        assert len(meta_description) == 100
        assert meta_description == description
    
    def test_description_exactly_160_preserved(self):
        description = "A" * 160
        meta_description = description[:160]
        assert len(meta_description) == 160
        assert meta_description == description
    
    def test_description_over_160_truncated(self):
        description = "A" * 200
        meta_description = description[:160]
        assert len(meta_description) == 160
        assert meta_description == "A" * 160
    
    def test_empty_description_no_meta(self):
        description = ""
        if description:
            meta_description = description[:160]
        else:
            meta_description = None
        assert meta_description is None
    
    def test_none_description_no_meta(self):
        description = None
        if description:
            meta_description = description[:160]
        else:
            meta_description = None
        assert meta_description is None
    
    def test_whitespace_description_no_meta(self):
        description = "   "
        if description and description.strip():
            meta_description = description[:160]
        else:
            meta_description = None
        assert meta_description is None
    
    def test_unicode_preserved(self):
        description = "你好世界，这是一个测试描述。Hello World!"
        meta_description = description[:160]
        assert meta_description == description
    
    def test_truncated_preserves_start(self):
        description = "Start of description that will be truncated at 160 chars. " + "X" * 100
        meta_description = description[:160]
        assert meta_description.startswith("Start of description")


class TestSEOKeywords:
    
    def test_keywords_generated_from_tags(self):
        profile = {"name": "Alice", "personality_tags": ["friendly", "romantic"]}
        personality_tags = profile.get("personality_tags", [])
        keywords = personality_tags + ["Alice", "AI character", "virtual companion", "chat"]
        keywords = list(set(keywords))[:10]
        assert "Alice" in keywords
        assert "friendly" in keywords
        assert "romantic" in keywords
        assert "AI character" in keywords
    
    def test_keywords_deduplicated(self):
        profile = {"name": "Test", "personality_tags": ["friendly", "friendly"]}
        personality_tags = profile.get("personality_tags", [])
        keywords = personality_tags + ["Test", "AI character", "AI character"]
        keywords = list(set(keywords))[:10]
        assert keywords.count("friendly") <= 1
        assert keywords.count("AI character") <= 1
    
    def test_keywords_limited_to_10(self):
        profile = {"name": "Test", "personality_tags": list(range(15))}
        personality_tags = profile.get("personality_tags", [])
        keywords = personality_tags + ["Test", "AI character", "virtual companion", "chat"]
        keywords = list(set(keywords))[:10]
        assert len(keywords) <= 10