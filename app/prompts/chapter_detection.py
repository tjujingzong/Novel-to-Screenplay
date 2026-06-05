"""Prompt templates for LLM-assisted chapter boundary detection."""

SYSTEM_PROMPT = """You are a text analyst identifying chapter or section boundaries in novel text.
Your task is to find where natural chapter breaks occur, even when explicit headings are absent.

Look for these signals of chapter breaks:
- Explicit headings like "Chapter X", "第X章"
- Scene breaks marked by "***", "---", or blank lines with symbols
- Major time jumps ("Three years later", "The next morning")
- Location changes
- POV character changes
- Thematic shifts

Output a JSON object with this structure:
{
  "chapters": [
    {
      "position": 0,
      "title": "Chapter 1"
    },
    {
      "position": 3500,
      "title": "Chapter 2"
    }
  ]
}

The "position" field is the approximate character offset in the text where the chapter begins.
The first chapter always starts at position 0.
"""

USER_PROMPT_TEMPLATE = """Please identify chapter boundaries in the following novel text.

--- NOVEL TEXT START ---
{text}
--- NOVEL TEXT END ---

Return a JSON object with a "chapters" array listing each chapter boundary."""
