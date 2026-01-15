"""Tests for the English G2P module."""

import pytest
from g2p.english import EnglishG2P


class TestEnglishG2P:
    """Test cases for EnglishG2P."""

    @pytest.fixture
    def g2p(self):
        """Create an EnglishG2P instance."""
        return EnglishG2P()

    def test_common_word(self, g2p):
        """Test common word conversion."""
        result = g2p.convert("hello")
        assert "h" in result
        assert len(result) > 0

    def test_cmu_dict_lookup(self, g2p):
        """Test CMU dictionary lookup."""
        result = g2p.convert("the")
        assert len(result) > 0

    def test_fallback_unknown_word(self, g2p):
        """Test fallback for unknown words not in CMU dictionary."""
        result = g2p.convert("xyzzy")
        assert len(result) > 0

    def test_punctuation(self, g2p):
        """Test punctuation handling."""
        result = g2p.convert("Hello, world!")
        assert len(result) > 0

    def test_multiple_words(self, g2p):
        """Test multiple word conversion."""
        result = g2p.convert("hello world")
        assert " " in result or len(result) > 5

    def test_uppercase(self, g2p):
        """Test uppercase word conversion."""
        result = g2p.convert("HELLO")
        assert "h" in result

    def test_mixed_case(self, g2p):
        """Test mixed case word conversion."""
        result = g2p.convert("HeLLo")
        assert "h" in result

    def test_contraction(self, g2p):
        """Test contraction handling."""
        result = g2p.convert("don't")
        assert len(result) > 0

    def test_empty_string(self, g2p):
        """Test empty string handling."""
        result = g2p.convert("")
        assert result == ""

    def test_th_sound(self, g2p):
        """Test 'th' sound conversion."""
        result = g2p.convert("think")
        assert "θ" in result

    def test_voiced_th(self, g2p):
        """Test voiced 'th' sound conversion."""
        result = g2p.convert("this")
        assert "ð" in result

    def test_sh_sound(self, g2p):
        """Test 'sh' sound conversion."""
        result = g2p.convert("she")
        assert "ʃ" in result

    def test_ch_sound(self, g2p):
        """Test 'ch' sound conversion."""
        result = g2p.convert("church")
        assert "ʧ" in result

    def test_ng_sound(self, g2p):
        """Test 'ng' sound conversion."""
        result = g2p.convert("sing")
        assert "ŋ" in result
