"""Assembly service: merge per-chapter conversions into a complete screenplay."""

import logging

from app.models.screenplay import (
    Act,
    Character,
    DialogueElement,
    Metadata,
    Screenplay,
    Structure,
)
from app.services.converter import ConversionResult

logger = logging.getLogger(__name__)


def assemble_screenplay(
    metadata: Metadata,
    characters: list[Character],
    conversion_results: list[ConversionResult],
) -> Screenplay:
    """Assemble a complete screenplay from individual chapter conversions.

    Args:
        metadata: Screenplay metadata.
        characters: Character catalog.
        conversion_results: Per-chapter conversion results.

    Returns:
        Complete Screenplay object.
    """
    acts = [result.act for result in conversion_results]

    # Renumber acts and scenes globally
    _renumber_acts_and_scenes(acts)

    # Populate characters_present in each scene
    _populate_characters_present(acts, characters)

    # Set first_appearance for each character
    _set_first_appearances(acts, characters)

    structure = Structure(acts=acts)

    return Screenplay(
        metadata=metadata,
        characters=characters,
        structure=structure,
    )


def _renumber_acts_and_scenes(acts: list[Act]):
    """Ensure sequential numbering for acts and global scene numbers."""
    global_scene_num = 0
    for i, act in enumerate(acts):
        act.number = i + 1
        act.id = f"act-{i + 1}"

        for j, scene in enumerate(act.scenes):
            global_scene_num += 1
            scene.number = global_scene_num
            scene.id = f"act-{i + 1}-scene-{j + 1}"


def _populate_characters_present(acts: list[Act], characters: list[Character]):
    """Scan dialogue elements to populate characters_present for each scene."""
    char_ids = {c.id for c in characters}

    for act in acts:
        for scene in act.scenes:
            if scene.characters_present:
                # Already populated by LLM, validate IDs
                scene.characters_present = [
                    cid for cid in scene.characters_present if cid in char_ids
                ]
                continue

            # Extract from dialogue elements
            seen = set()
            for elem in scene.elements:
                if isinstance(elem, DialogueElement) and elem.character_id in char_ids:
                    seen.add(elem.character_id)

            scene.characters_present = sorted(seen)


def _set_first_appearances(acts: list[Act], characters: list[Character]):
    """Set first_appearance for each character based on the earliest scene."""
    char_first_seen: dict[str, str] = {}

    for act in acts:
        for scene in act.scenes:
            for char_id in scene.characters_present:
                if char_id not in char_first_seen:
                    char_first_seen[char_id] = scene.id

    for character in characters:
        if character.id in char_first_seen:
            character.first_appearance = char_first_seen[character.id]
