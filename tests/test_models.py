"""Tests for the Pydantic screenplay models."""


from app.models.screenplay import (
    ActionElement,
    Act,
    Character,
    DialogueElement,
    Metadata,
    NoteElement,
    ParentheticalElement,
    Relationship,
    Scene,
    SceneHeading,
    Screenplay,
    Structure,
    TransitionElement,
)


class TestMetadata:
    def test_required_fields(self):
        m = Metadata(title="Test", author="Author", genre="drama")
        assert m.title == "Test"
        assert m.adapted_by == "AI-Assisted Adaptation"
        assert m.version == "1.0.0"

    def test_auto_timestamps(self):
        m = Metadata(title="Test", author="Author", genre="drama")
        assert m.created_at is not None
        assert m.modified_at is not None


class TestCharacter:
    def test_basic_character(self):
        c = Character(id="hero", name="Hero", role="protagonist", description="The hero.")
        assert c.id == "hero"
        assert c.aliases == []
        assert c.relationships == []

    def test_character_with_relationships(self):
        c = Character(
            id="hero",
            name="Hero",
            relationships=[Relationship(target_id="villain", type="rival", description="Enemy")],
        )
        assert len(c.relationships) == 1
        assert c.relationships[0].target_id == "villain"


class TestElements:
    def test_action_element(self):
        e = ActionElement(type="action", text="The door opens.")
        assert e.type == "action"
        assert e.importance == "standard"

    def test_dialogue_element(self):
        e = DialogueElement(
            type="dialogue",
            character_id="hero",
            character_name="Hero",
            line="Hello there.",
            parenthetical="(cheerfully)",
        )
        assert e.type == "dialogue"
        assert e.line == "Hello there."

    def test_transition_element(self):
        e = TransitionElement(type="transition", style="CUT_TO")
        assert e.type == "transition"

    def test_note_element(self):
        e = NoteElement(type="note", content="Consider removing this scene.")
        assert e.type == "note"

    def test_parenthetical_element(self):
        e = ParentheticalElement(type="parenthetical", character_id="hero", text="(beat)")
        assert e.type == "parenthetical"


class TestScene:
    def test_scene_with_elements(self):
        scene = Scene(
            id="act-1-scene-1",
            number=1,
            heading=SceneHeading(location="OFFICE", time_of_day="DAY", int_ext="INT"),
            elements=[
                ActionElement(type="action", text="The phone rings."),
                DialogueElement(
                    type="dialogue",
                    character_id="boss",
                    character_name="Boss",
                    line="Answer it!",
                ),
            ],
        )
        assert len(scene.elements) == 2
        assert scene.heading.location == "OFFICE"


class TestScreenplay:
    def test_full_screenplay_creation(self):
        sp = Screenplay(
            metadata=Metadata(title="Test Film", author="Writer", genre="thriller"),
            characters=[Character(id="lead", name="Lead", role="protagonist")],
            structure=Structure(
                acts=[Act(
                    id="act-1",
                    number=1,
                    scenes=[Scene(
                        id="act-1-scene-1",
                        number=1,
                        heading=SceneHeading(location="STREET", time_of_day="NIGHT", int_ext="EXT"),
                        elements=[ActionElement(type="action", text="It is raining.")],
                    )],
                )],
            ),
        )
        assert sp.metadata.title == "Test Film"
        assert len(sp.characters) == 1
        assert len(sp.structure.acts) == 1
        assert len(sp.structure.acts[0].scenes) == 1
