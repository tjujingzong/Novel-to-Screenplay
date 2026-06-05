"""Character extraction service using LLM."""

import logging
import re

from pydantic import BaseModel

from app.models.screenplay import Character
from app.prompts import character_extraction as prompts
from app.services.chapter_splitter import Chapter
from app.services.llm_client import DeepSeekClient

logger = logging.getLogger(__name__)


class CharacterExtractionResult(BaseModel):
    """Intermediate result from LLM character extraction."""
    characters: list[dict] = []


async def extract_characters(
    chapters: list[Chapter],
    client: DeepSeekClient,
) -> list[Character]:
    """Extract a character catalog from novel chapters.

    Samples the first 3 chapters (plus mid/end samples for longer novels)
    and consolidates the results.

    Args:
        chapters: List of chapters from the novel.
        client: The LLM client.

    Returns:
        Deduplicated list of Character objects.
    """
    # Select chapters to sample
    sample_indices = _select_sample_indices(chapters)

    all_characters: list[dict] = []

    for idx in sample_indices:
        chapter = chapters[idx]
        # Truncate very long chapters
        text = chapter.content[:8000] if len(chapter.content) > 8000 else chapter.content

        user_prompt = prompts.USER_PROMPT_TEMPLATE.format(
            chapter_title=chapter.title or f"Section {chapter.number}",
            text=text,
        )

        try:
            result = await client.complete(
                system_prompt=prompts.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=CharacterExtractionResult,
            )
            all_characters.extend(result.characters)
        except Exception as e:
            logger.warning("Failed to extract characters from chapter %d: %s", chapter.number, e)
            continue

    # Convert dicts to Character objects and deduplicate
    characters = _consolidate_characters(all_characters)

    if not characters:
        logger.warning("No characters extracted, creating placeholder")
        characters = [Character(
            id="narrator",
            name="Narrator",
            role="protagonist",
            description="Main character (auto-generated placeholder)",
        )]

    return characters


def _select_sample_indices(chapters: list[Chapter]) -> list[int]:
    """Select which chapters to sample for character extraction."""
    n = len(chapters)
    if n <= 3:
        return list(range(n))

    # First 3, middle, and last chapter
    indices = [0, 1, 2]
    mid = n // 2
    if mid not in indices:
        indices.append(mid)
    if n - 1 not in indices:
        indices.append(n - 1)

    return sorted(indices)


def _consolidate_characters(raw_characters: list[dict]) -> list[Character]:
    """Merge and deduplicate character entries from multiple extraction passes."""
    if not raw_characters:
        return []

    # Group by normalized name
    by_id: dict[str, dict] = {}

    for char_data in raw_characters:
        char_id = _make_slug(char_data.get("id") or char_data.get("name", "unknown"))
        if not char_id:
            continue

        if char_id in by_id:
            # Merge: keep richer data
            existing = by_id[char_id]
            if len(char_data.get("description", "")) > len(existing.get("description", "")):
                existing["description"] = char_data["description"]
            # Merge aliases
            existing_aliases = set(existing.get("aliases", []))
            existing_aliases.update(char_data.get("aliases", []))
            existing["aliases"] = list(existing_aliases)
            # Merge relationships
            existing_rels = {(r.get("target_id"), r.get("type")) for r in existing.get("relationships", [])}
            for rel in char_data.get("relationships", []):
                key = (rel.get("target_id"), rel.get("type"))
                if key not in existing_rels:
                    existing.setdefault("relationships", []).append(rel)
        else:
            char_data["id"] = char_id
            by_id[char_id] = char_data

    characters = []
    for char_data in by_id.values():
        try:
            characters.append(Character(
                id=char_data["id"],
                name=char_data.get("name", char_data["id"]),
                aliases=char_data.get("aliases", []),
                role=char_data.get("role", "supporting"),
                description=char_data.get("description", ""),
                age_range=char_data.get("age_range"),
                gender=char_data.get("gender"),
                occupation=char_data.get("occupation"),
                relationships=[],  # Will be validated later
                notes=char_data.get("notes"),
            ))
        except Exception as e:
            logger.warning("Failed to create Character from data: %s, error: %s", char_data, e)

    return characters


def _make_slug(name: str) -> str:
    """Create a lowercase-hyphenated slug from a name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", slug)
    slug = slug.strip("-")
    return slug
