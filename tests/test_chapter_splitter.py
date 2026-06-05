"""Tests for the chapter splitter service."""

import pytest

from app.services.chapter_splitter import split_chapters, Chapter


class TestRegexSplitting:
    def test_english_chapters(self):
        text = "Chapter 1\n\nFirst chapter content.\n\nChapter 2\n\nSecond chapter content.\n\nChapter 3\n\nThird chapter content."
        chapters = split_chapters(text)
        assert len(chapters) == 3
        assert chapters[0].number == 1
        assert chapters[1].number == 2
        assert chapters[2].number == 3

    def test_chinese_chapters(self):
        text = "第一章\n\n第一节的内容。\n\n第二章\n\n第二节的内容。\n\n第三章\n\n第三节的内容。"
        chapters = split_chapters(text)
        assert len(chapters) == 3
        assert chapters[0].title is not None
        assert "第一章" in chapters[0].title

    def test_roman_numeral_chapters(self):
        text = "Chapter I\n\nFirst.\n\nChapter II\n\nSecond.\n\nChapter III\n\nThird."
        chapters = split_chapters(text)
        assert len(chapters) == 3

    def test_preserves_content(self):
        text = "Chapter 1\n\nSome important content here.\n\nChapter 2\n\nMore content."
        chapters = split_chapters(text)
        assert "important content" in chapters[0].content
        assert "More content" in chapters[1].content


class TestHeuristicSplitting:
    def test_no_chapter_headings(self):
        # Long text without chapter headings should be split heuristically
        paragraphs = ["Paragraph one. " * 200] * 30
        text = "\n\n".join(paragraphs)
        chapters = split_chapters(text)
        assert len(chapters) >= 2

    def test_single_chapter_short_text(self):
        text = "Just a short piece of text without any chapters."
        chapters = split_chapters(text)
        assert len(chapters) >= 1
        assert "short piece" in chapters[0].content

    def test_heuristic_respects_paragraphs(self):
        # Ensure splits happen at paragraph boundaries
        text = "\n\n".join([f"Para {i}: " + "word " * 500 for i in range(20)])
        chapters = split_chapters(text)
        for ch in chapters:
            # Each chapter's content should end cleanly
            assert not ch.content.endswith("wor")


class TestChapterModel:
    def test_chapter_creation(self):
        ch = Chapter(number=1, title="Test", content="Content", start_char=0)
        assert ch.number == 1
        assert ch.title == "Test"

    def test_chapter_optional_title(self):
        ch = Chapter(number=1, content="Content")
        assert ch.title is None
