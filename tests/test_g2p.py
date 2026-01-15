"""Tests for the unified G2P pipeline."""

import pytest
from g2p import G2PPipeline


class TestG2PPipeline:
    """Test cases for G2PPipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create a G2PPipeline instance."""
        return G2PPipeline()

    def test_japanese_basic(self, pipeline):
        """Test basic Japanese text conversion."""
        result = pipeline.convert("こんにちは")
        assert "k" in result
        # N before 'n' becomes N_n -> 'n' (alveolar nasal)
        assert "n" in result

    def test_japanese_n_uvular(self, pipeline):
        """Test Japanese text with uvular N (word-final)."""
        result = pipeline.convert("にほん")
        # Word-final N becomes N_uvular -> 'ɴ' (uvular nasal)
        assert "ɴ" in result

    def test_english_basic(self, pipeline):
        """Test basic English text conversion."""
        result = pipeline.convert("Hello world")
        assert "h" in result

    def test_mixed_language(self, pipeline):
        """Test mixed Japanese-English text conversion."""
        result = pipeline.convert("Hello、こんにちは")
        assert len(result) > 0

    def test_language_detection_japanese(self, pipeline):
        """Test language detection for Japanese text."""
        assert pipeline._detect_language("こんにちは") == "ja"

    def test_language_detection_english(self, pipeline):
        """Test language detection for English text."""
        assert pipeline._detect_language("Hello") == "en"

    def test_language_detection_mixed(self, pipeline):
        """Test language detection for mixed text."""
        assert pipeline._detect_language("Hello、こんにちは") == "mixed"

    def test_normalize_punctuation(self, pipeline):
        """Test text normalization for punctuation."""
        normalized = pipeline._normalize("こんにちは。")
        assert "." in normalized

    def test_normalize_whitespace(self, pipeline):
        """Test text normalization for whitespace."""
        normalized = pipeline._normalize("hello   world")
        assert "  " not in normalized

    def test_explicit_language_ja(self, pipeline):
        """Test explicit Japanese language specification."""
        result = pipeline.convert("test", language="ja")
        assert len(result) > 0

    def test_explicit_language_en(self, pipeline):
        """Test explicit English language specification."""
        result = pipeline.convert("hello", language="en")
        assert len(result) > 0
        assert "h" in result
