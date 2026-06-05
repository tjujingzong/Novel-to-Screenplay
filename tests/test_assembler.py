"""Tests for the assembler service."""

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
from app.services.assembler import assemble_screenplay
from app.services.converter import ConversionResult


def _make_conversion_result(act_num: int, num_scenes: int = 1) -> ConversionResult:
    """Helper to create a minimal ConversionResult."""
    scenes = []
    for i in range(num_scenes):
        scenes.append(Scene(
            id=f"act-{act_num}-scene-{i + 1}",
            number=0,  # Will be renumbered
            heading=SceneHeading(location=f"LOCATION {i + 1}", time_of_day="DAY", int_ext="INT"),
            elements=[
                DialogueElement(
                    type="dialogue",
                    character_id="winston-smith",
                    character_name="Winston",
                    line=f"Line in scene {i + 1}",
                ),
                ActionElement(type="action", text=f"Action in scene {i + 1}"),
            ],
        ))

    act = Act(
        id=f"act-{act_num}",
        number=act_num,
        title=f"Act {act_num}",
        scenes=scenes,
    )

    return ConversionResult(act=act, summary=f"Act {act_num} summary")


class TestAssembly:
    def test_assemble_basic(self, sample_characters):
        results = [
            _make_conversion_result(1, 2),
            _make_conversion_result(2, 1),
        ]
        metadata = Metadata(title="Test", author="Author", genre="drama")

        screenplay = assemble_screenplay(metadata, sample_characters, results)

        assert screenplay.metadata.title == "Test"
        assert len(screenplay.structure.acts) == 2
        assert len(screenplay.structure.acts[0].scenes) == 2
        assert len(screenplay.structure.acts[1].scenes) == 1

    def test_scene_numbering_is_global(self, sample_characters):
        results = [
            _make_conversion_result(1, 2),
            _make_conversion_result(2, 3),
        ]
        metadata = Metadata(title="Test", author="Author", genre="drama")

        screenplay = assemble_screenplay(metadata, sample_characters, results)

        all_scene_numbers = []
        for act in screenplay.structure.acts:
            for scene in act.scenes:
                all_scene_numbers.append(scene.number)

        assert all_scene_numbers == [1, 2, 3, 4, 5]

    def test_characters_present_populated(self, sample_characters):
        results = [_make_conversion_result(1, 1)]
        metadata = Metadata(title="Test", author="Author", genre="drama")

        screenplay = assemble_screenplay(metadata, sample_characters, results)

        scene = screenplay.structure.acts[0].scenes[0]
        assert "winston-smith" in scene.characters_present

    def test_first_appearance_set(self, sample_characters):
        # Create a result where winston-smith appears in scene 1
        scene = Scene(
            id="act-1-scene-1",
            number=1,
            heading=SceneHeading(location="ROOM", time_of_day="DAY", int_ext="INT"),
            elements=[DialogueElement(
                type="dialogue",
                character_id="winston-smith",
                character_name="Winston",
                line="Hello",
            )],
            characters_present=["winston-smith"],
        )
        act = Act(id="act-1", number=1, scenes=[scene])
        result = ConversionResult(act=act, summary="Test")

        metadata = Metadata(title="Test", author="Author", genre="drama")
        screenplay = assemble_screenplay(metadata, sample_characters, [result])

        winston = next(c for c in screenplay.characters if c.id == "winston-smith")
        assert winston.first_appearance == "act-1-scene-1"
