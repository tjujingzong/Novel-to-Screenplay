"""Tests for the validator service."""

import pytest

from app.models.screenplay import (
    Act,
    ActionElement,
    Character,
    DialogueElement,
    Metadata,
    Scene,
    SceneHeading,
    Screenplay,
    Structure,
)
from app.services.validator import validate_screenplay


class TestValidation:
    def test_valid_screenplay(self, sample_screenplay):
        issues = validate_screenplay(sample_screenplay)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_empty_title(self, sample_screenplay):
        sample_screenplay.metadata.title = ""
        issues = validate_screenplay(sample_screenplay)
        title_issues = [i for i in issues if "title" in i.path.lower()]
        assert len(title_issues) > 0

    def test_no_acts(self, sample_screenplay):
        sample_screenplay.structure.acts = []
        issues = validate_screenplay(sample_screenplay)
        act_errors = [i for i in issues if "acts" in i.path]
        assert len(act_errors) > 0

    def test_invalid_character_reference(self, sample_screenplay):
        # Add a dialogue element referencing a non-existent character
        scene = sample_screenplay.structure.acts[0].scenes[0]
        scene.elements.append(DialogueElement(
            type="dialogue",
            character_id="nonexistent-char",
            character_name="Nobody",
            line="This should fail validation.",
        ))
        issues = validate_screenplay(sample_screenplay)
        char_errors = [i for i in issues if "nonexistent" in i.message]
        assert len(char_errors) > 0

    def test_empty_scene_elements(self, sample_screenplay):
        scene = sample_screenplay.structure.acts[0].scenes[0]
        scene.elements = []
        issues = validate_screenplay(sample_screenplay)
        empty_issues = [i for i in issues if "elements" in i.path.lower() or "元素" in i.message]
        assert len(empty_issues) > 0

    def test_invalid_characters_present(self, sample_screenplay):
        scene = sample_screenplay.structure.acts[0].scenes[0]
        scene.characters_present = ["ghost-character"]
        issues = validate_screenplay(sample_screenplay)
        ghost_warnings = [i for i in issues if "ghost-character" in i.message]
        assert len(ghost_warnings) > 0
