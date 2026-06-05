"""Pydantic models for the screenplay YAML schema.

These models serve as the single source of truth for the YAML structure.
They are used for validation, serialization, and JSON Schema generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# ─── Metadata ────────────────────────────────────────────────────────────────

class Metadata(BaseModel):
    """Top-level screenplay metadata."""
    title: str = Field(..., description="Work title")
    author: str = Field(..., description="Original novel author")
    adapted_by: str = Field(default="AI-Assisted Adaptation", description="Screenplay adapter")
    source_material: str | None = Field(default=None, description="e.g. 'Based on the novel [title] by [author]'")
    genre: str = Field(..., description="Primary genre (drama, comedy, thriller, etc.)")
    subgenres: list[str] = Field(default_factory=list, description="Secondary genre tags")
    format: str = Field(default="feature_film", description="feature_film | tv_episode | miniseries | short_film")
    target_audience: str | None = Field(default=None, description="e.g. adult, young_adult, family")
    estimated_duration_minutes: int | None = Field(default=None, description="Estimated runtime in minutes")
    language: str = Field(default="zh", description="ISO 639-1 language code")
    version: str = Field(default="1.0.0", description="Schema version")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 creation datetime",
    )
    modified_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 last modification datetime",
    )
    generator: str = Field(default="novel-to-screenplay v1.0", description="Tool that generated this screenplay")


# ─── Characters ──────────────────────────────────────────────────────────────

class Relationship(BaseModel):
    """A relationship between two characters."""
    target_id: str = Field(..., description="References another character.id")
    type: str = Field(..., description="e.g. sister, rival, love_interest, mentor")
    description: str = Field(default="", description="Brief nature of relationship")


class Character(BaseModel):
    """A character in the screenplay."""
    id: str = Field(..., description="Unique slug identifier, e.g. 'elizabeth-bennet'")
    name: str = Field(..., description="Display name")
    aliases: list[str] = Field(default_factory=list, description="Other names used")
    role: str = Field(default="supporting", description="protagonist | antagonist | supporting | minor | extra")
    description: str = Field(default="", description="Physical + personality sketch")
    age_range: str | None = Field(default=None, description="e.g. '20-25'")
    gender: str | None = Field(default=None, description="Character's gender identity")
    occupation: str | None = Field(default=None, description="Character's occupation")
    relationships: list[Relationship] = Field(default_factory=list, description="Connections to other characters")
    notes: str | None = Field(default=None, description="Actor direction, casting notes")
    first_appearance: str | None = Field(default=None, description="Scene ID where character first appears")


# ─── Scene Elements (Discriminated Union) ────────────────────────────────────

class ActionElement(BaseModel):
    """Describes physical action, setting, or visual information."""
    type: Literal["action"] = "action"
    text: str = Field(..., description="Action description in present tense")
    importance: str = Field(default="standard", description="key | standard | background")


class DialogueElement(BaseModel):
    """A character's spoken line."""
    type: Literal["dialogue"] = "dialogue"
    character_id: str = Field(..., description="References characters[].id")
    character_name: str = Field(..., description="Display name (denormalized for readability)")
    parenthetical: str | None = Field(default=None, description="Delivery direction, e.g. '(whispering)'")
    line: str = Field(..., description="The spoken dialogue")
    continuation: bool = Field(default=False, description="True if continuing interrupted dialogue")


class ParentheticalElement(BaseModel):
    """A direction inserted between dialogue lines."""
    type: Literal["parenthetical"] = "parenthetical"
    character_id: str = Field(..., description="Character this parenthetical applies to")
    text: str = Field(..., description="e.g. '(beat)', '(looking away)'")


class TransitionElement(BaseModel):
    """An explicit transition within or between scenes."""
    type: Literal["transition"] = "transition"
    style: str = Field(..., description="CUT_TO | FADE_TO_BLACK | DISSOLVE_TO | INTERCUT | MONTAGE | TIME_LAPSE")
    description: str | None = Field(default=None, description="Context for the transition")


class NoteElement(BaseModel):
    """Editor/adapter commentary, not part of the rendered screenplay."""
    type: Literal["note"] = "note"
    content: str = Field(..., description="The note text")
    author: str | None = Field(default=None, description="Note author")


ScreenplayElement = Annotated[
    Union[ActionElement, DialogueElement, ParentheticalElement, TransitionElement, NoteElement],
    Field(discriminator="type"),
]


# ─── Scene ───────────────────────────────────────────────────────────────────

class SceneHeading(BaseModel):
    """Scene heading (slug line)."""
    location: str = Field(..., description="e.g. 'BENNET HOUSE - DRAWING ROOM'")
    time_of_day: str = Field(default="DAY", description="DAY | NIGHT | DAWN | DUSK | CONTINUOUS | LATER | MOMENTS_LATER")
    int_ext: str = Field(default="INT", description="INT | EXT | INT_EXT | EXT_INT")


class Scene(BaseModel):
    """A single scene within an act."""
    id: str = Field(..., description="e.g. 'act-1-scene-3'")
    number: int = Field(..., description="Global scene number across all acts")
    heading: SceneHeading = Field(..., description="Scene heading (slug line)")
    description: str | None = Field(default=None, description="Scene purpose/summary")
    setting: str | None = Field(default=None, description="Detailed environment description")
    characters_present: list[str] = Field(default_factory=list, description="List of character IDs in this scene")
    elements: list[ScreenplayElement] = Field(default_factory=list, description="Ordered sequence of screenplay elements")
    transition_out: str | None = Field(default=None, description="CUT_TO | FADE_OUT | DISSOLVE_TO | SMASH_CUT | MATCH_CUT | WIPE_TO")


# ─── Act ─────────────────────────────────────────────────────────────────────

class Act(BaseModel):
    """A structural act within the screenplay."""
    id: str = Field(..., description="e.g. 'act-1'")
    number: int = Field(..., description="Sequential act number")
    title: str | None = Field(default=None, description="e.g. 'The Setup', 'Confrontation'")
    description: str | None = Field(default=None, description="Brief act summary")
    scenes: list[Scene] = Field(default_factory=list, description="Scenes within this act")


# ─── Structure ───────────────────────────────────────────────────────────────

class Structure(BaseModel):
    """The structural hierarchy of the screenplay."""
    acts: list[Act] = Field(default_factory=list, description="Ordered list of acts")


# ─── Notes ───────────────────────────────────────────────────────────────────

class ScreenplayNote(BaseModel):
    """A global annotation on the screenplay."""
    scope: str = Field(default="global", description="e.g. 'global', 'act-1', 'act-2-scene-3'")
    content: str = Field(..., description="The note text")
    author: str = Field(default="system", description="'system' or human editor name")


# ─── Root Model ──────────────────────────────────────────────────────────────

class Screenplay(BaseModel):
    """Root model for the complete screenplay."""
    metadata: Metadata = Field(..., description="Screenplay metadata")
    characters: list[Character] = Field(default_factory=list, description="Character catalog")
    structure: Structure = Field(default_factory=Structure, description="Acts and scenes")
    notes: list[ScreenplayNote] = Field(default_factory=list, description="Global annotations")
