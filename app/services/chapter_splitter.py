"""Chapter detection and splitting service.

Uses a two-tier strategy:
1. Regex-based detection for common chapter heading patterns
2. LLM-assisted detection as fallback
3. Heuristic splitting as last resort
"""

import logging
import re

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Common chapter heading patterns
# Note: [^\n]* is used instead of \S* to avoid matching across line breaks.
CHAPTER_PATTERNS = [
    # English: "Chapter 1", "Chapter One", "CHAPTER 1", "Chapter 1: The Beginning"
    re.compile(r"^(?:Chapter|CHAPTER)\s+[\dIVXLCDMivxlcdm]+[^\n]*", re.MULTILINE),
    # English: "Part 1", "Book 1"
    re.compile(r"^(?:Part|PART|Book|BOOK)\s+[\dIVXLCDMivxlcdm]+[^\n]*", re.MULTILINE),
    # Chinese: "第一章", "第二章", "第1章" (章/回/卷/集/篇 only — not 节 which means section)
    re.compile(r"^第[一二三四五六七八九十百零\d]+[章回卷集篇部][^\n]*", re.MULTILINE),
    # Chinese: "一、", "二、" style
    re.compile(r"^[一二三四五六七八九十]+[、．.]", re.MULTILINE),
    # Markdown headings that look like chapters
    re.compile(r"^#{1,3}\s+(?:Chapter|第[一二三四五六七八九十百零\d]+[章回卷集篇部])", re.MULTILINE),
    # Numbered sections: "1.", "2.", etc. at start of line
    re.compile(r"^\d{1,3}[.、][^\n]*", re.MULTILINE),
]


class Chapter(BaseModel):
    """A detected chapter or section of the novel."""
    number: int
    title: str | None = None
    content: str
    start_char: int = 0


def split_chapters(text: str) -> list[Chapter]:
    """Split novel text into chapters using regex-based detection.

    Falls back to heuristic splitting if fewer than 2 chapters are detected.

    Args:
        text: The full novel text.

    Returns:
        List of Chapter objects.
    """
    # Try regex-based splitting first
    chapters = _regex_split(text)

    if len(chapters) >= 2:
        logger.info("Regex splitting found %d chapters", len(chapters))
        return chapters

    # Fallback: heuristic splitting
    chapters = _heuristic_split(text)
    logger.info("Heuristic splitting produced %d sections", len(chapters))
    return chapters


def _regex_split(text: str) -> list[Chapter]:
    """Attempt to split using regex chapter heading patterns."""
    for pattern in CHAPTER_PATTERNS:
        matches = list(pattern.finditer(text))
        if len(matches) >= 2:
            return _build_chapters_from_matches(text, matches)
    return []


def _build_chapters_from_matches(text: str, matches: list[re.Match]) -> list[Chapter]:
    """Build Chapter objects from regex match positions."""
    chapters = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        # Extract title from the match line
        heading_line = match.group(0).strip()

        # Remove the heading line from the content
        content_after_heading = text[match.end():end].strip()

        chapters.append(Chapter(
            number=i + 1,
            title=heading_line,
            content=content_after_heading,
            start_char=start,
        ))

    return chapters


def _heuristic_split(text: str) -> list[Chapter]:
    """Split text into roughly equal sections at paragraph boundaries.

    Targets 3 sections minimum, splitting at double newlines.
    """
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if len(paragraphs) < 3:
        # Text is too short to split meaningfully
        return [Chapter(number=1, title="Full Text", content=text, start_char=0)]

    # Determine number of sections: aim for ~3000-5000 words per section
    from app.services.file_parser import count_words
    total_words = count_words(text)
    target_words_per_section = 4000
    num_sections = max(3, min(total_words // target_words_per_section, len(paragraphs)))
    # Cap at a reasonable number
    num_sections = min(num_sections, 30)

    # Distribute paragraphs evenly
    sections = _distribute_paragraphs(paragraphs, num_sections)

    chapters = []
    char_offset = 0
    for i, section_paragraphs in enumerate(sections):
        content = "\n\n".join(section_paragraphs)
        chapters.append(Chapter(
            number=i + 1,
            title=f"Section {i + 1}",
            content=content,
            start_char=char_offset,
        ))
        char_offset += len(content) + 2  # account for join separator

    return chapters


def _distribute_paragraphs(paragraphs: list[str], num_sections: int) -> list[list[str]]:
    """Distribute paragraphs into roughly equal sections."""
    if num_sections <= 0:
        return [paragraphs]

    total_chars = sum(len(p) for p in paragraphs)
    target_chars = total_chars / num_sections

    sections = []
    current_section: list[str] = []
    current_chars = 0

    for para in paragraphs:
        current_section.append(para)
        current_chars += len(para)

        if current_chars >= target_chars and len(sections) < num_sections - 1:
            sections.append(current_section)
            current_section = []
            current_chars = 0

    # Add remaining paragraphs to last section
    if current_section:
        sections.append(current_section)

    return sections
