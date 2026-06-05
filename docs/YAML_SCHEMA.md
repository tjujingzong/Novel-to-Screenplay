# Screenplay YAML Schema v1.0

## 1. Overview

This document defines the YAML Schema for the **Novel-to-Screenplay** conversion tool. The schema describes how a screenplay is structured in YAML format, enabling machine validation, human editing, and interoperability with other tools.

### Design Philosophy

The schema is built on three core principles:

1. **Round-trippable**: YAML -> rendered screenplay -> YAML preserves meaning. Every field has a clear mapping to standard screenplay formatting, so the YAML can serve as a lossless interchange format.

2. **LLM-friendly**: Field names are descriptive and unambiguous enough that an LLM can populate them without confusion. Rather than cryptic abbreviations, we use clear English names (`character_id`, `time_of_day`, `transition_out`).

3. **Human-editable**: A screenwriter can open the YAML in any text editor and make meaningful changes. The structure is intuitive, optional fields are truly optional, and the format is not cluttered with boilerplate.

### Industry Standards Referenced

- **Fountain** (fountain.io): The open-source screenplay markup standard. We adopted its element type taxonomy (action, dialogue, parenthetical, transition).
- **Final Draft XML Structure**: The hierarchical acts -> scenes -> elements organization mirrors Final Draft's document model.
- **WGA (Writers Guild of America) Standards**: Scene heading format (INT/EXT. LOCATION - TIME), present-tense action lines, and character name conventions follow WGA formatting guidelines.

---

## 2. Top-Level Structure

```yaml
screenplay:
  metadata: { ... }        # Work information
  characters: [ ... ]      # Character catalog
  structure:               # Hierarchical content
    acts: [ ... ]
  notes: [ ... ]           # Optional annotations
```

---

## 3. Field Reference

### 3.1 Metadata

Information about the screenplay as a whole.

| Field | Type | Required | Default | Description | Example |
|-------|------|----------|---------|-------------|---------|
| `title` | string | Yes | - | Work title | `"Pride and Prejudice"` |
| `author` | string | Yes | - | Original novel author | `"Jane Austen"` |
| `adapted_by` | string | No | `"AI-Assisted Adaptation"` | Screenplay adapter | `"John Smith"` |
| `source_material` | string | No | `null` | Attribution text | `"Based on the novel by Jane Austen"` |
| `genre` | string | Yes | - | Primary genre | `"romance"` |
| `subgenres` | [string] | No | `[]` | Secondary genres | `["drama", "comedy_of_manners"]` |
| `format` | string | No | `"feature_film"` | See Format enum below | `"tv_episode"` |
| `target_audience` | string | No | `null` | Target audience | `"young_adult"` |
| `estimated_duration_minutes` | int | No | `null` | Estimated runtime | `120` |
| `language` | string | No | `"zh"` | ISO 639-1 code | `"en"`, `"zh"` |
| `version` | string | No | `"1.0.0"` | Schema version | `"1.0.0"` |
| `created_at` | string | No | auto | ISO 8601 datetime | `"2026-06-05T10:30:00Z"` |
| `modified_at` | string | No | auto | ISO 8601 datetime | `"2026-06-05T10:30:00Z"` |
| `generator` | string | No | `"novel-to-screenplay v1.0"` | Generating tool | `"novel-to-screenplay v1.0"` |

**Design rationale**: Metadata is deliberately kept flat (not nested) to make it easy to find and edit. Timestamps and generator are auto-populated but can be overridden. The `format` field uses an enum to constrain valid screenplay types, ensuring downstream tools can reliably determine rendering behavior.

### 3.2 Characters

A catalog of all characters in the screenplay.

| Field | Type | Required | Default | Description | Example |
|-------|------|----------|---------|-------------|---------|
| `id` | string | Yes | - | Unique slug identifier | `"elizabeth-bennet"` |
| `name` | string | Yes | - | Display name | `"Elizabeth Bennet"` |
| `aliases` | [string] | No | `[]` | Other names used | `["Lizzy", "Eliza"]` |
| `role` | string | No | `"supporting"` | See RoleType enum | `"protagonist"` |
| `description` | string | No | `""` | Physical + personality | `"Witty, intelligent second daughter"` |
| `age_range` | string | No | `null` | Age range | `"20-25"` |
| `gender` | string | No | `null` | Gender identity | `"female"` |
| `occupation` | string | No | `null` | Occupation | `"Student"` |
| `relationships` | [Relationship] | No | `[]` | See below | - |
| `notes` | string | No | `null` | Casting/direction notes | `"Needs strong comedic timing"` |
| `first_appearance` | string | No | auto | Scene ID of first appearance | `"act-1-scene-1"` |

**Design rationale**: Characters are stored as a flat catalog (not nested within acts/scenes) to serve as a single source of truth. The `id` slug is the canonical reference used throughout the screenplay — display names may vary, but IDs are stable. The `first_appearance` field is auto-calculated during assembly to aid casting and production planning.

#### Relationship (nested within characters)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_id` | string | Yes | References another `character.id` |
| `type` | string | Yes | Relationship type: `sister`, `rival`, `love_interest`, `mentor`, etc. |
| `description` | string | No | Brief description of the relationship |

### 3.3 Structure > Acts

The structural hierarchy: Acts contain Scenes.

| Field | Type | Required | Default | Description | Example |
|-------|------|----------|---------|-------------|---------|
| `id` | string | Yes | - | Unique identifier | `"act-1"` |
| `number` | int | Yes | - | Sequential act number | `1` |
| `title` | string | No | `null` | Act title | `"The Arrival"` |
| `description` | string | No | `null` | Brief act summary | `"Bingley and Darcy arrive"` |
| `scenes` | [Scene] | No | `[]` | Scenes in this act | See below |

**Design rationale**: The three-act structure is the most common screenplay framework. Each act maps roughly to 1-3 novel chapters, providing a natural pacing structure. The `number` field is always sequential starting from 1.

### 3.4 Scenes

Each scene represents a continuous sequence at a single location and time.

| Field | Type | Required | Default | Description | Example |
|-------|------|----------|---------|-------------|---------|
| `id` | string | Yes | - | Unique identifier | `"act-1-scene-3"` |
| `number` | int | Yes | - | Global scene number | `5` |
| `heading` | SceneHeading | Yes | - | See below | - |
| `description` | string | No | `null` | Scene purpose/summary | `"Mrs. Bennet delivers the news"` |
| `setting` | string | No | `null` | Environment description | `"A modest country drawing room"` |
| `characters_present` | [string] | No | auto | Character IDs in scene | `["elizabeth-bennet", "mr-darcy"]` |
| `elements` | [Element] | Yes | `[]` | Ordered screenplay elements | See below |
| `transition_out` | string | No | `null` | See TransitionType enum | `"CUT_TO"` |

#### SceneHeading

| Field | Type | Required | Default | Description | Example |
|-------|------|----------|---------|-------------|---------|
| `location` | string | Yes | - | UPPERCASE location | `"BENNET HOUSE - DRAWING ROOM"` |
| `time_of_day` | string | Yes | `"DAY"` | See TimeOfDay enum | `"NIGHT"` |
| `int_ext` | string | Yes | `"INT"` | See IntExt enum | `"EXT"` |

**Design rationale**: The scene heading is split into structured sub-fields rather than a single string. This enables tools to filter scenes by location, time, or interior/exterior setting. The `characters_present` field is auto-populated from dialogue elements but can be manually extended to include characters who appear silently.

### 3.5 Elements (within scenes)

Elements are the building blocks of a scene. They appear in an ordered array and are distinguished by their `type` field (discriminated union).

#### Action Element

Describes physical action, setting details, or visual information. Always written in **present tense**.

```yaml
- type: action
  text: "ELIZABETH enters the drawing room, clutching a letter."
  importance: "key"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `"action"` | Yes | - | Always "action" |
| `text` | string | Yes | - | Action description in present tense |
| `importance` | string | No | `"standard"` | `key` / `standard` / `background` |

**Design rationale**: The `importance` field helps rendering tools emphasize key actions (bold, larger font) and allows editors to quickly identify critical plot points during revision.

#### Dialogue Element

A character's spoken line.

```yaml
- type: dialogue
  character_id: "elizabeth-bennet"
  character_name: "Elizabeth"
  line: "I daresay the whole neighbourhood will be in an uproar."
  parenthetical: "(amused)"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `"dialogue"` | Yes | - | Always "dialogue" |
| `character_id` | string | Yes | - | References `characters[].id` |
| `character_name` | string | Yes | - | Display name (denormalized for readability) |
| `line` | string | Yes | - | The spoken dialogue |
| `parenthetical` | string | No | `null` | Delivery direction: `"(whispering)"` |
| `continuation` | bool | No | `false` | True if continuing interrupted dialogue |

**Design rationale**: `character_name` is deliberately denormalized (duplicated from the character catalog) to improve human readability. An editor can read dialogue without cross-referencing the character list. The `character_id` remains the canonical reference for programmatic use.

#### Parenthetical Element

A standalone direction between dialogue lines (e.g., `(beat)`, `(looking away)`).

```yaml
- type: parenthetical
  character_id: "mr-darcy"
  text: "(pauses, then turns slowly)"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"parenthetical"` | Yes | Always "parenthetical" |
| `character_id` | string | Yes | Character this applies to |
| `text` | string | Yes | The direction text |

#### Transition Element

An explicit transition within or between scenes.

```yaml
- type: transition
  style: "TIME_LAPSE"
  description: "Two weeks pass"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"transition"` | Yes | Always "transition" |
| `style` | string | Yes | See TransitionType enum |
| `description` | string | No | Context for the transition |

#### Note Element

Editor/adapter commentary that is **not rendered** in the final screenplay output.

```yaml
- type: note
  content: "Consider combining this scene with the next for pacing"
  author: "editor"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"note"` | Yes | Always "note" |
| `content` | string | Yes | The note text |
| `author` | string | No | Note author |

### 3.6 Notes (global)

Optional annotations at the screenplay level.

```yaml
notes:
  - scope: "global"
    content: "The adaptation condenses chapters 5-7 into Act 2"
    author: "system"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `scope` | string | No | `"global"` | `"global"`, `"act-1"`, `"act-2-scene-3"` |
| `content` | string | Yes | - | The note text |
| `author` | string | No | `"system"` | `"system"` or human editor name |

---

## 4. Enumerations

### Format (screenplay format)
| Value | Description |
|-------|-------------|
| `feature_film` | Feature-length film screenplay |
| `tv_episode` | Television episode |
| `miniseries` | Limited series |
| `short_film` | Short film |

### RoleType (character role)
| Value | Description |
|-------|-------------|
| `protagonist` | Main character driving the story |
| `antagonist` | Primary opposition to the protagonist |
| `supporting` | Significant secondary character |
| `minor` | Small but named role |
| `extra` | Background/unnamed character |

### TimeOfDay
| Value | Description |
|-------|-------------|
| `DAY` | Daytime |
| `NIGHT` | Nighttime |
| `DAWN` | Early morning |
| `DUSK` | Evening/twilight |
| `CONTINUOUS` | Immediately follows previous scene |
| `LATER` | Same location, later time |
| `MOMENTS_LATER` | Same location, moments later |

### IntExt (interior/exterior)
| Value | Description |
|-------|-------------|
| `INT` | Interior (inside a building) |
| `EXT` | Exterior (outdoors) |
| `INT_EXT` | Both interior and exterior |
| `EXT_INT` | Exterior transitioning to interior |

### TransitionType
| Value | Description |
|-------|-------------|
| `CUT_TO` | Standard cut between scenes |
| `FADE_OUT` | Gradual fade to black |
| `FADE_TO_BLACK` | Explicit fade to black |
| `DISSOLVE_TO` | Overlapping dissolve |
| `SMASH_CUT` | Abrupt, jarring cut |
| `MATCH_CUT` | Cut between visually similar images |
| `WIPE_TO` | Wipe transition |
| `INTERCUT` | Alternating between two scenes |
| `MONTAGE` | Montage sequence |
| `TIME_LAPSE` | Time passage |

### ElementImportance
| Value | Description |
|-------|-------------|
| `key` | Critical plot action, must be prominent |
| `standard` | Normal action |
| `background` | Ambient/atmospheric detail |

---

## 5. Rendering Guide

How each YAML element maps to traditional screenplay formatting:

| Element | Rendering |
|---------|-----------|
| **Scene Heading** | Left-aligned, ALL CAPS, e.g. `INT. BENNET HOUSE - DRAWING ROOM - DAY` |
| **Action** | Left-aligned, standard paragraph, present tense |
| **Dialogue** | Centered block: CHARACTER NAME (all caps, centered), then dialogue text indented |
| **Parenthetical** | Centered, in parentheses, between character name and dialogue |
| **Transition** | Right-aligned, ALL CAPS, e.g. `CUT TO:` |
| **Note** | Not rendered in final output (editorial only) |

---

## 6. Validation Rules

Beyond type checking, the following cross-reference constraints must hold:

1. **Character references**: Every `character_id` in dialogue and parenthetical elements must reference a valid `characters[].id`.
2. **Sequential numbering**: Act numbers must be sequential (1, 2, 3...). Scene numbers must be globally sequential across all acts.
3. **Non-empty structure**: The screenplay must contain at least one act. Each act must contain at least one scene. Each scene must contain at least one element.
4. **ID uniqueness**: Character `id` values must be unique. Scene `id` values must be unique.
5. **Relationship integrity**: `Relationship.target_id` must reference a valid character ID.
6. **Scene heading format**: `location` should be UPPERCASE. `time_of_day` and `int_ext` must use valid enum values.

---

## 7. Complete Example

```yaml
# Screenplay YAML v1.0.0
# Generated by novel-to-screenplay tool
---
screenplay:
  metadata:
    title: "Pride and Prejudice"
    author: "Jane Austen"
    adapted_by: "AI-Assisted Adaptation"
    source_material: "Based on the novel Pride and Prejudice by Jane Austen"
    genre: "romance"
    subgenres:
      - "drama"
      - "comedy_of_manners"
    format: "feature_film"
    language: "en"
    version: "1.0.0"
    created_at: "2026-06-05T10:30:00Z"
    modified_at: "2026-06-05T10:30:00Z"
    generator: "novel-to-screenplay v1.0"

  characters:
    - id: "elizabeth-bennet"
      name: "Elizabeth Bennet"
      aliases:
        - "Lizzy"
        - "Eliza"
      role: "protagonist"
      description: "Witty, intelligent second daughter. Sharp-tongued with keen irony."
      age_range: "20-21"
      gender: "female"
      relationships:
        - target_id: "mr-darcy"
          type: "love_interest"
          description: "Initial disdain evolving into deep respect and love"
        - target_id: "jane-bennet"
          type: "sister"
          description: "Closest sister and confidante"
      first_appearance: "act-1-scene-1"

    - id: "mr-darcy"
      name: "Mr. Fitzwilliam Darcy"
      role: "protagonist"
      description: "Wealthy, proud gentleman whose aloofness masks deep integrity."
      age_range: "28-30"
      gender: "male"
      first_appearance: "act-1-scene-2"

    - id: "mrs-bennet"
      name: "Mrs. Bennet"
      role: "supporting"
      description: "Nervous, excitable mother obsessed with marrying off her daughters."
      gender: "female"
      first_appearance: "act-1-scene-1"

    - id: "mr-bennet"
      name: "Mr. Bennet"
      role: "supporting"
      description: "Sardonic father who prefers his library to family drama."
      gender: "male"
      first_appearance: "act-1-scene-1"

  structure:
    acts:
      - id: "act-1"
        number: 1
        title: "The Arrival"
        description: "Bingley and Darcy arrive at Netherfield; first impressions are formed."
        scenes:
          - id: "act-1-scene-1"
            number: 1
            heading:
              location: "LONGBOURN - DRAWING ROOM"
              time_of_day: "DAY"
              int_ext: "INT"
            description: "Mrs. Bennet delivers news of Bingley's arrival."
            setting: "A modest but comfortable country drawing room, early 19th century."
            characters_present:
              - "mrs-bennet"
              - "mr-bennet"
              - "elizabeth-bennet"
            elements:
              - type: action
                text: "MRS. BENNET bursts into the drawing room where MR. BENNET sits reading."
                importance: "key"

              - type: dialogue
                character_id: "mrs-bennet"
                character_name: "Mrs. Bennet"
                line: "My dear Mr. Bennet, have you heard? A young man of large fortune has taken Netherfield Park!"
                parenthetical: "(breathless, excited)"

              - type: dialogue
                character_id: "mr-bennet"
                character_name: "Mr. Bennet"
                line: "Well, my dear, I have not."
                parenthetical: "(without looking up from his book)"

              - type: action
                text: "Elizabeth glances up with an amused smile."

              - type: dialogue
                character_id: "elizabeth-bennet"
                character_name: "Elizabeth"
                line: "I daresay the whole neighbourhood will be in an uproar."

            transition_out: "CUT_TO"

          - id: "act-1-scene-2"
            number: 2
            heading:
              location: "NETHERFIELD PARK - BALLROOM"
              time_of_day: "NIGHT"
              int_ext: "INT"
            description: "First meeting between Elizabeth and Darcy at the ball."
            characters_present:
              - "elizabeth-bennet"
              - "mr-darcy"
            elements:
              - type: action
                text: "The ballroom is alive with music and chatter. Elizabeth dances with Charlotte Lucas."
                importance: "standard"

              - type: action
                text: "Mr. Darcy stands apart from the crowd, observing with an expression of disdain."
                importance: "key"

              - type: transition
                style: "CUT_TO"

      - id: "act-2"
        number: 2
        title: "Pride and Prejudice"
        description: "Misunderstandings deepen as Elizabeth and Darcy circle each other."
        scenes: []

  notes:
    - scope: "global"
      content: "This is an AI-generated first draft. Manual refinement of dialogue and pacing is recommended."
      author: "system"
```

---

## 8. Extension Points

The schema is designed to be extended without breaking validation:

- **Custom fields**: Any YAML parser will preserve unknown fields. Downstream tools should ignore fields they don't recognize.
- **Custom element types**: New element types can be added to the `elements` array. The `type` discriminator enables safe parsing of known types while unknown types can be treated as notes.
- **Genre-specific fields**: Horror screenplays might add `scare_level` to action elements. Musical screenplays might add `song` elements.
- **Production metadata**: Fields like `budget_note`, `casting_priority`, or `vfx_required` can be added to scenes without affecting the screenplay structure.

---

## 9. Schema Versioning

This document describes **Schema v1.0**. The version is recorded in the `metadata.version` field of each generated YAML file. Future versions will maintain backward compatibility by:

- Never removing existing fields
- Only adding optional fields
- Never changing field types
- Documenting all breaking changes in a changelog
