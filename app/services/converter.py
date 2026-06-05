"""Core prose-to-screenplay conversion service."""

import json
import logging

from pydantic import BaseModel

from app.models.screenplay import Act, Scene
from app.prompts import screenplay_conversion as conv_prompts
from app.prompts import continuity as cont_prompts
from app.services.chapter_splitter import Chapter
from app.services.llm_client import DeepSeekClient

logger = logging.getLogger(__name__)


class ConversionContext:
    """State passed between sequential chapter conversions for continuity."""

    def __init__(self):
        self.previous_scene_summary: str = "This is the beginning of the story."
        self.running_scene_number: int = 0
        self.act_number: int = 1


class ConversionResult(BaseModel):
    """Result from converting a single chapter."""
    act: Act
    summary: str


class ChapterActResult(BaseModel):
    """Intermediate LLM response for chapter conversion."""
    act: dict


async def convert_chapter(
    chapter: Chapter,
    character_catalog_str: str,
    context: ConversionContext,
    client: DeepSeekClient,
    stream_callback=None,
) -> ConversionResult:
    """Convert a single novel chapter into screenplay scenes.

    Args:
        chapter: The chapter to convert.
        character_catalog_str: Formatted character catalog string.
        context: Running conversion context for continuity.
        client: The LLM client.
        stream_callback: Optional async callback that receives streaming chunks.

    Returns:
        ConversionResult with the generated Act and a continuity summary.
    """
    # Truncate very long chapters to fit token budget
    text = chapter.content
    if len(text) > 12000:
        text = text[:12000] + "\n\n[... text truncated for length ...]"

    user_prompt = conv_prompts.USER_PROMPT_TEMPLATE.format(
        character_catalog=character_catalog_str,
        previous_context=context.previous_scene_summary,
        chapter_number=chapter.number,
        chapter_title=chapter.title or f"Section {chapter.number}",
        chapter_text=text,
    )

    try:
        if stream_callback:
            # Use streaming mode
            stream_result, chunk_gen = await client.complete_stream(
                system_prompt=conv_prompts.SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            async for chunk in chunk_gen:
                await stream_callback(chunk)
            await stream_callback("\n")
            content = stream_result.full_text
            # Parse the full text as JSON
            act_data = _parse_json_content(content)
            act = _parse_act(act_data.get("act", act_data), context)
        else:
            result = await client.complete(
                system_prompt=conv_prompts.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=ChapterActResult,
            )
            act = _parse_act(result.act, context)
    except Exception as e:
        logger.error("Failed to convert chapter %d: %s", chapter.number, e)
        act = _create_fallback_act(chapter, context)

    # Generate continuity summary
    summary = await _generate_summary(act, chapter.number, client)

    # Update context for next chapter
    context.previous_scene_summary = summary
    context.running_scene_number += len(act.scenes)

    return ConversionResult(act=act, summary=summary)


def _parse_json_content(content: str) -> dict:
    """Parse JSON from LLM content, handling markdown fences."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


def format_character_catalog(characters) -> str:
    """Format character list into a compact string for the prompt."""
    if not characters:
        return "No characters identified yet."

    lines = []
    for char in characters:
        aliases = f" (aka: {', '.join(char.aliases)})" if char.aliases else ""
        lines.append(f"- {char.id}: {char.name}{aliases} [{char.role}] — {char.description}")

    return "\n".join(lines)


def _parse_act(act_data: dict, context: ConversionContext) -> Act:
    """Parse the LLM's act response into a Pydantic Act model."""
    scenes = []

    for i, scene_data in enumerate(act_data.get("scenes", [])):
        # Assign global scene number
        context.running_scene_number += 1
        scene_number = context.running_scene_number

        elements = []
        for elem_data in scene_data.get("elements", []):
            elem_type = elem_data.get("type", "action")
            try:
                if elem_type == "action":
                    from app.models.screenplay import ActionElement
                    elements.append(ActionElement(**elem_data))
                elif elem_type == "dialogue":
                    from app.models.screenplay import DialogueElement
                    elements.append(DialogueElement(**elem_data))
                elif elem_type == "parenthetical":
                    from app.models.screenplay import ParentheticalElement
                    elements.append(ParentheticalElement(**elem_data))
                elif elem_type == "transition":
                    from app.models.screenplay import TransitionElement
                    elements.append(TransitionElement(**elem_data))
                elif elem_type == "note":
                    from app.models.screenplay import NoteElement
                    elements.append(NoteElement(**elem_data))
            except Exception as e:
                logger.warning("Failed to parse element %d in scene %d: %s", i, scene_number, e)

        from app.models.screenplay import SceneHeading
        heading_data = scene_data.get("heading", {})
        heading = SceneHeading(
            location=heading_data.get("location", f"LOCATION {scene_number}"),
            time_of_day=heading_data.get("time_of_day", "DAY"),
            int_ext=heading_data.get("int_ext", "INT"),
        )

        scene_id = f"act-{context.act_number}-scene-{i + 1}"
        scenes.append(Scene(
            id=scene_id,
            number=scene_number,
            heading=heading,
            description=scene_data.get("description"),
            setting=scene_data.get("setting"),
            characters_present=scene_data.get("characters_present", []),
            elements=elements,
            transition_out=scene_data.get("transition_out"),
        ))

    return Act(
        id=f"act-{context.act_number}",
        number=context.act_number,
        title=act_data.get("title", f"Act {context.act_number}"),
        description=act_data.get("description"),
        scenes=scenes,
    )


def _create_fallback_act(chapter: Chapter, context: ConversionContext) -> Act:
    """Create a minimal act when LLM conversion fails."""
    from app.models.screenplay import SceneHeading, ActionElement

    context.running_scene_number += 1

    scene = Scene(
        id=f"act-{context.act_number}-scene-1",
        number=context.running_scene_number,
        heading=SceneHeading(location="VARIOUS LOCATIONS", time_of_day="DAY", int_ext="INT"),
        description=f"Scene adapted from {chapter.title or f'Chapter {chapter.number}'}",
        elements=[ActionElement(
            type="action",
            text=f"[This chapter could not be fully converted: {chapter.title or f'Chapter {chapter.number}'}]",
            importance="key",
        )],
    )

    return Act(
        id=f"act-{context.act_number}",
        number=context.act_number,
        title=chapter.title or f"Act {context.act_number}",
        scenes=[scene],
    )


async def _generate_summary(act: Act, chapter_number: int, client: DeepSeekClient) -> str:
    """Generate a 2-sentence continuity summary for the chapter ending."""
    # Build a brief text describing the chapter's scenes
    scene_texts = []
    for scene in act.scenes:
        elem_summary = " ".join(
            e.text if hasattr(e, "text") else e.line if hasattr(e, "line") else ""
            for e in scene.elements[:3]
        )
        scene_texts.append(f"Scene at {scene.heading.location}: {elem_summary}")

    scenes_text = "\n".join(scene_texts[:5])  # Limit to avoid token overflow

    user_prompt = cont_prompts.USER_PROMPT_TEMPLATE.format(
        chapter_number=chapter_number,
        scene_summaries=scenes_text,
    )

    try:
        summary = await client.complete(
            system_prompt=cont_prompts.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        return summary if isinstance(summary, str) else str(summary)
    except Exception as e:
        logger.warning("Failed to generate continuity summary: %s", e)
        # Fallback: use last scene description
        if act.scenes:
            last_scene = act.scenes[-1]
            return f"Chapter {chapter_number} ends at {last_scene.heading.location}."
        return f"Chapter {chapter_number} has ended."
