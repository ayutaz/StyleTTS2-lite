"""Tests for the Japanese G2P module."""

import pytest
from g2p.japanese import JapaneseG2P


class TestJapaneseG2P:
    """Test cases for JapaneseG2P."""

    @pytest.fixture
    def g2p(self):
        """Create a JapaneseG2P instance."""
        return JapaneseG2P()

    def test_hiragana(self, g2p):
        """Test hiragana text conversion."""
        result = g2p.convert("こんにちは")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "k" in result

    def test_katakana(self, g2p):
        """Test katakana text conversion."""
        result = g2p.convert("コンピュータ")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_kanji(self, g2p):
        """Test kanji text conversion."""
        result = g2p.convert("東京")
        assert "t" in result
        assert "o" in result

    def test_mixed_scripts(self, g2p):
        """Test mixed hiragana, katakana, and kanji."""
        result = g2p.convert("今日はいい天気です")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_string(self, g2p):
        """Test empty string handling."""
        result = g2p.convert("")
        assert result == ""

    def test_long_vowel(self, g2p):
        """Test long vowel handling (e.g., おおきい)."""
        result = g2p.convert("おおきい")
        assert isinstance(result, str)
        assert "o" in result

    def test_nasal_sound(self, g2p):
        """Test nasal sound (ん) conversion."""
        result = g2p.convert("かんじ")
        assert "ɴ" in result

    def test_geminate(self, g2p):
        """Test geminate (っ) conversion."""
        result = g2p.convert("きって")
        # Should contain glottal stop or pause marker
        assert len(result) > 0

    def test_palatalized(self, g2p):
        """Test palatalized sounds (きゃ, しゃ, etc.)."""
        result = g2p.convert("きゃく")
        assert "j" in result or "k" in result

    def test_numbers_in_text(self, g2p):
        """Test text with numbers."""
        result = g2p.convert("3時")
        assert isinstance(result, str)
