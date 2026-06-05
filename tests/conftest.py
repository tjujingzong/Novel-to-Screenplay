"""Shared test fixtures."""

import pytest
from pathlib import Path

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
from app.services.chapter_splitter import Chapter


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_novel_text() -> str:
    """A 3-chapter sample novel text."""
    return """Chapter 1: The Beginning

It was a bright cold day in April, and the clocks were striking thirteen.
Winston Smith hurried home to Victory Mansions, his head down against the bitter wind.

Inside his apartment, Winston sat at his desk and opened his notebook.
He began to write, his hand trembling slightly.

"We shall meet again," said a voice from the telescreen.

Winston jumped. It was only the usual morning announcement.

Chapter 2: The Meeting

The next day, Winston went to the canteen for lunch.
He saw Julia sitting at a nearby table, reading a novel.

"May I sit here?" Winston asked.

Julia looked up and smiled. "Of course. There's plenty of room."

They ate in silence for a while. Then Julia spoke.

"I've read your articles in the Times," she said. "They're quite good."

"Thank you," Winston replied, surprised. "I didn't think anyone read them."

Chapter 3: The Discovery

A week later, Winston and Julia met in the countryside.
The birds were singing and the air smelled of wildflowers.

"This is beautiful," Julia said, looking around.

"It won't last," Winston replied grimly. "Nothing does."

They walked along a narrow path through the woods.
Suddenly, Julia stopped and pointed ahead.

"Look!" she whispered. "What is that?"

In the clearing ahead, they saw an old stone building.
It looked abandoned, but smoke was rising from the chimney.
"""


@pytest.fixture
def sample_chapters() -> list[Chapter]:
    """Pre-split sample chapters."""
    return [
        Chapter(
            number=1,
            title="Chapter 1: The Beginning",
            content="It was a bright cold day in April...\n\nWinston Smith hurried home...\n\n\"We shall meet again,\" said a voice.",
            start_char=0,
        ),
        Chapter(
            number=2,
            title="Chapter 2: The Meeting",
            content="The next day, Winston went to the canteen...\n\nJulia looked up and smiled...",
            start_char=200,
        ),
        Chapter(
            number=3,
            title="Chapter 3: The Discovery",
            content="A week later, Winston and Julia met in the countryside...\n\nThey walked along a narrow path...",
            start_char=400,
        ),
    ]


@pytest.fixture
def sample_characters() -> list[Character]:
    """Sample character catalog."""
    return [
        Character(
            id="winston-smith",
            name="Winston Smith",
            role="protagonist",
            description="A quiet, thoughtful man who works at the Ministry of Truth.",
            gender="male",
            age_range="35-40",
        ),
        Character(
            id="julia",
            name="Julia",
            role="protagonist",
            description="A bold, vivacious young woman.",
            gender="female",
            age_range="25-30",
        ),
    ]


@pytest.fixture
def sample_screenplay(sample_characters) -> Screenplay:
    """A minimal valid screenplay."""
    scene = Scene(
        id="act-1-scene-1",
        number=1,
        heading=SceneHeading(location="VICTORY MANSIONS - APARTMENT", time_of_day="DAY", int_ext="INT"),
        description="Winston begins writing in his notebook.",
        setting="A shabby apartment in Victory Mansions.",
        characters_present=["winston-smith"],
        elements=[
            ActionElement(
                type="action",
                text="WINSTON SMITH sits at his desk and opens a notebook.",
                importance="key",
            ),
            DialogueElement(
                type="dialogue",
                character_id="winston-smith",
                character_name="Winston",
                line="We shall meet again.",
                parenthetical="(whispering to himself)",
            ),
        ],
        transition_out="CUT_TO",
    )

    act = Act(
        id="act-1",
        number=1,
        title="The Beginning",
        description="Winston starts his rebellion.",
        scenes=[scene],
    )

    metadata = Metadata(
        title="1984",
        author="George Orwell",
        genre="dystopian",
        language="en",
    )

    return Screenplay(
        metadata=metadata,
        characters=sample_characters,
        structure=Structure(acts=[act]),
    )
