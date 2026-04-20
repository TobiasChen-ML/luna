import pytest
from app.models.character import CHARACTER_TEMPLATES

EXPECTED_TEMPLATES = {
    "college_student", "office_lady", "girl_next_door",
    "romantic_artist", "fitness_coach", "mystic_witch",
    "sweet_barista", "boss_lady"
}

REQUIRED_FIELDS = [
    "name", "description", "age_range", "personality_pool",
    "background_hints", "greeting_templates"
]


class TestCharacterTemplates:
    
    def test_template_count(self):
        assert len(CHARACTER_TEMPLATES) == 8
    
    def test_template_ids(self):
        assert set(CHARACTER_TEMPLATES.keys()) == EXPECTED_TEMPLATES
    
    @pytest.mark.parametrize("template_id", EXPECTED_TEMPLATES)
    def test_template_has_required_fields(self, template_id):
        template = CHARACTER_TEMPLATES[template_id]
        for field in REQUIRED_FIELDS:
            assert field in template, f"{template_id} missing {field}"
    
    @pytest.mark.parametrize("template_id", EXPECTED_TEMPLATES)
    def test_age_range_valid(self, template_id):
        template = CHARACTER_TEMPLATES[template_id]
        age_range = template["age_range"]
        assert len(age_range) == 2
        assert age_range[0] <= age_range[1]
        assert age_range[0] >= 18
    
    @pytest.mark.parametrize("template_id", EXPECTED_TEMPLATES)
    def test_personality_pool_not_empty(self, template_id):
        template = CHARACTER_TEMPLATES[template_id]
        assert len(template["personality_pool"]) >= 1
    
    @pytest.mark.parametrize("template_id", EXPECTED_TEMPLATES)
    def test_greeting_templates_have_placeholder(self, template_id):
        template = CHARACTER_TEMPLATES[template_id]
        for greeting in template["greeting_templates"]:
            assert "{name}" in greeting, \
                f"{template_id} greeting missing {{name}}: {greeting}"
    
    @pytest.mark.parametrize("template_id", EXPECTED_TEMPLATES)
    def test_name_not_empty(self, template_id):
        template = CHARACTER_TEMPLATES[template_id]
        assert template["name"], f"{template_id} has empty name"
        assert len(template["name"]) > 0
    
    @pytest.mark.parametrize("template_id", EXPECTED_TEMPLATES)
    def test_description_not_empty(self, template_id):
        template = CHARACTER_TEMPLATES[template_id]
        assert template["description"], f"{template_id} has empty description"
    
    @pytest.mark.parametrize("template_id", EXPECTED_TEMPLATES)
    def test_greeting_templates_not_empty(self, template_id):
        template = CHARACTER_TEMPLATES[template_id]
        assert len(template["greeting_templates"]) >= 1
