"""Tests for the file parser service."""

import pytest

from app.services.file_parser import (
    extract_text,
    detect_file_type,
    count_words,
    FileParsingError,
)


class TestDetectFileType:
    def test_txt(self):
        assert detect_file_type("novel.txt") == "txt"

    def test_md(self):
        assert detect_file_type("novel.md") == "md"

    def test_markdown(self):
        assert detect_file_type("novel.markdown") == "md"

    def test_docx(self):
        assert detect_file_type("novel.docx") == "docx"

    def test_pdf(self):
        assert detect_file_type("novel.pdf") == "pdf"

    def test_unsupported(self):
        with pytest.raises(FileParsingError, match="Unsupported"):
            detect_file_type("novel.html")


class TestExtractText:
    def test_extract_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello world.\nThis is a test.", encoding="utf-8")
        result = extract_text(f, "txt")
        assert "Hello world" in result
        assert "This is a test" in result

    def test_extract_txt_utf8_bom(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"\xef\xbb\xbfHello BOM")
        result = extract_text(f, "txt")
        assert "Hello BOM" in result

    def test_extract_md_strips_formatting(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Chapter 1\n\nThis is **bold** and *italic*.", encoding="utf-8")
        result = extract_text(f, "md")
        assert "Chapter 1" in result
        assert "bold" in result
        assert "italic" in result
        assert "**" not in result
        assert "*" not in result

    def test_extract_md_strips_links(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("Click [here](http://example.com) for more.", encoding="utf-8")
        result = extract_text(f, "md")
        assert "here" in result
        assert "http" not in result

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileParsingError, match="not found"):
            extract_text(tmp_path / "nonexistent.txt", "txt")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        with pytest.raises(FileParsingError, match="No text"):
            extract_text(f, "txt")

    def test_unsupported_type(self, tmp_path):
        f = tmp_path / "test.html"
        f.write_text("<html></html>", encoding="utf-8")
        with pytest.raises(FileParsingError, match="Unsupported"):
            extract_text(f, "html")


class TestCountWords:
    def test_english_text(self):
        assert count_words("hello world foo bar") == 4

    def test_chinese_text(self):
        # Each CJK character counts as one word
        count = count_words("你好世界")
        assert count == 4

    def test_mixed_text(self):
        count = count_words("Hello 你好 world")
        assert count == 4  # "Hello", "你", "好", "world"

    def test_empty_text(self):
        assert count_words("") == 0

    def test_with_punctuation(self):
        count = count_words("Hello, world! How are you?")
        assert count == 5
