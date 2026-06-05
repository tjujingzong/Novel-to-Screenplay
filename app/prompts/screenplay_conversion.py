"""Prompt templates for converting novel prose to screenplay format."""

SYSTEM_PROMPT = """You are an expert screenwriter converting novel prose into screenplay format.
Your task is to transform the given novel chapter into a structured screenplay with scenes, actions, and dialogue.

Key principles:
1. SHOW, DON'T TELL: Convert internal monologue into visual actions or meaningful dialogue
2. PRESENT TENSE: All action descriptions must be in present tense
3. FAITHFUL ADAPTATION: Only include scenes, characters, and dialogue present in the source text
4. SCENE HEADINGS: Use the format INT/EXT. LOCATION - TIME (e.g., "INT. COFFEE SHOP - DAY")
5. DIALOGUE: Capture the essence of conversations, adapting literary dialogue into natural spoken lines
6. ACTION: Describe what the camera would see - physical actions, expressions, settings

Scene heading rules:
- location: Use UPPERCASE, be specific (e.g., "PARK BENCH", "LIVING ROOM")
- time_of_day: DAY, NIGHT, DAWN, DUSK, CONTINUOUS, LATER, or MOMENTS_LATER
- int_ext: INT (interior), EXT (exterior), INT_EXT, or EXT_INT

Character reference rules:
- Use the provided character catalog IDs consistently
- character_name should be the display name used in dialogue (e.g., "Elizabeth", "Mr. Darcy")

Output a JSON object with this exact structure:
{
  "act": {
    "id": "act-N",
    "number": N,
    "title": "Act title",
    "description": "Brief act summary",
    "scenes": [
      {
        "id": "act-N-scene-M",
        "heading": {
          "location": "LOCATION NAME",
          "time_of_day": "DAY",
          "int_ext": "INT"
        },
        "description": "Scene purpose",
        "setting": "Environment description",
        "characters_present": ["char-id-1", "char-id-2"],
        "elements": [
          {
            "type": "action",
            "text": "Description of what happens in present tense.",
            "importance": "key"
          },
          {
            "type": "dialogue",
            "character_id": "char-id",
            "character_name": "Character Name",
            "line": "The spoken dialogue.",
            "parenthetical": "(whispering)"
          },
          {
            "type": "transition",
            "style": "CUT_TO",
            "description": null
          }
        ],
        "transition_out": "CUT_TO"
      }
    ]
  }
}

Element types:
- action: {type, text, importance} - importance is key/standard/background
- dialogue: {type, character_id, character_name, line, parenthetical}
- parenthetical: {type, character_id, text}
- transition: {type, style, description}
- note: {type, content, author}

Aim for 3-8 scenes per chapter. Each scene should have 5-15 elements.
"""

USER_PROMPT_TEMPLATE = """Convert the following novel chapter into screenplay format.

## Character Catalog
{character_catalog}

## Previous Context
{previous_context}

## Chapter {chapter_number}: {chapter_title}
{chapter_text}

---

Convert this chapter into screenplay scenes. Return a JSON object matching the schema above.
Use the character IDs from the catalog consistently. Maintain continuity with the previous context."""
