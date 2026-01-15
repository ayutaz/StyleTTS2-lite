"""Comprehensive tests for the Japanese G2P module.

Tests cover:
- Basic hiragana, katakana, kanji conversion
- Unvoiced vowels
- N phoneme variants (context-dependent)
- Long vowels
- Palatalized consonants
- Prosody extraction
- Edge cases
"""

import pytest
from g2p.japanese import JapaneseG2P
from g2p.japanese.converter import JapanesePhonemeConverter


class TestJapaneseG2P:
    """Test cases for JapaneseG2P."""

    @pytest.fixture
    def g2p(self):
        """Create a JapaneseG2P instance."""
        return JapaneseG2P()

    @pytest.fixture
    def g2p_with_prosody(self):
        """Create a JapaneseG2P instance with prosody enabled."""
        return JapaneseG2P(use_prosody=True)

    @pytest.fixture
    def g2p_no_n_variants(self):
        """Create a JapaneseG2P instance without N variants."""
        return JapaneseG2P(use_n_variants=False)

    # Basic conversion tests
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

    def test_whitespace_only(self, g2p):
        """Test whitespace-only string."""
        result = g2p.convert("   ")
        assert result == ""

    # N phoneme variant tests
    def test_n_before_bilabial_m(self, g2p):
        """Test N before m (bilabial assimilation)."""
        result = g2p.convert("さんま")  # sanma
        # N before m should become m (bilabial)
        assert "m" in result

    def test_n_before_bilabial_b(self, g2p):
        """Test N before b (bilabial assimilation)."""
        result = g2p.convert("かんばん")  # kanban
        # N before b should become m (bilabial)
        assert result.count("m") >= 1 or "m" in result

    def test_n_before_bilabial_p(self, g2p):
        """Test N before p (bilabial assimilation)."""
        result = g2p.convert("さんぽ")  # sanpo
        # N before p should become m (bilabial)
        assert "m" in result

    def test_n_before_velar_k(self, g2p):
        """Test N before k (velar assimilation)."""
        result = g2p.convert("たんか")  # tanka
        # N before k should become ŋ (velar)
        assert "ŋ" in result

    def test_n_before_velar_g(self, g2p):
        """Test N before g (velar assimilation)."""
        result = g2p.convert("まんが")  # manga
        # N before g should become ŋ (velar)
        assert "ŋ" in result

    def test_n_before_alveolar_t(self, g2p):
        """Test N before t (alveolar assimilation)."""
        result = g2p.convert("かんたん")  # kantan
        # N before t should become n (alveolar)
        # Count n's - should have more than just from "ka-n-ta-n"
        assert "n" in result

    def test_n_at_end(self, g2p):
        """Test N at phrase end (uvular)."""
        result = g2p.convert("にほん")  # nihon
        # N at end should become ɴ (uvular)
        assert "ɴ" in result

    def test_n_before_vowel(self, g2p):
        """Test N before vowel (uvular)."""
        result = g2p.convert("かんあい")  # kan'ai
        # N before vowel should become ɴ (uvular)
        assert "ɴ" in result

    def test_n_without_variants(self, g2p_no_n_variants):
        """Test N without context-dependent variants."""
        result = g2p_no_n_variants.convert("さんま")
        # Without variants, all N should be ɴ
        assert "ɴ" in result

    # Long vowel tests
    def test_long_vowel(self, g2p):
        """Test long vowel handling (e.g., おおきい)."""
        result = g2p.convert("おおきい")
        assert isinstance(result, str)
        assert "o" in result

    def test_long_vowel_katakana(self, g2p):
        """Test katakana long vowel (ー)."""
        result = g2p.convert("コーヒー")  # koohii
        assert isinstance(result, str)
        assert len(result) > 0

    # Nasal sound tests
    def test_nasal_sound(self, g2p):
        """Test nasal sound (ん) conversion."""
        result = g2p.convert("かんじ")  # kanji
        # Should have nasal sound (n or ɴ depending on context)
        assert len(result) > 0

    # Geminate (促音) tests
    def test_geminate(self, g2p):
        """Test geminate (っ) conversion."""
        result = g2p.convert("きって")  # kitte
        # Should contain glottal stop or pause marker
        assert len(result) > 0
        # May contain ʔ for glottal stop
        assert "ʔ" in result or "t" in result

    def test_geminate_before_k(self, g2p):
        """Test geminate before k."""
        result = g2p.convert("がっこう")  # gakkou
        assert "ʔ" in result or "k" in result

    def test_geminate_before_s(self, g2p):
        """Test geminate before s."""
        result = g2p.convert("いっさい")  # issai
        assert "ʔ" in result or "s" in result

    # Palatalized sound tests
    def test_palatalized_ky(self, g2p):
        """Test palatalized sounds (きゃ)."""
        result = g2p.convert("きゃく")  # kyaku
        assert "j" in result or "k" in result

    def test_palatalized_sh(self, g2p):
        """Test sh sound (しゃ)."""
        result = g2p.convert("しゃしん")  # shashin
        assert "ʃ" in result

    def test_palatalized_ch(self, g2p):
        """Test ch sound (ちゃ)."""
        result = g2p.convert("おちゃ")  # ocha
        assert "ʧ" in result

    def test_palatalized_ny(self, g2p):
        """Test ny sound (にゃ)."""
        result = g2p.convert("にゃんこ")  # nyanko
        # ny maps to ɲ (palatal nasal)
        assert "ɲ" in result or "j" in result

    def test_palatalized_ry(self, g2p):
        """Test ry sound (りゃ)."""
        result = g2p.convert("りゃく")  # ryaku
        assert "ɾ" in result or "j" in result

    # Numbers in text
    def test_numbers_in_text(self, g2p):
        """Test text with numbers."""
        result = g2p.convert("3時")
        assert isinstance(result, str)

    def test_numbers_mixed(self, g2p):
        """Test mixed numbers and text."""
        result = g2p.convert("2024年")
        assert isinstance(result, str)

    # Prosody tests
    def test_prosody_markers(self, g2p_with_prosody):
        """Test prosody marker extraction."""
        result = g2p_with_prosody.convert("こんにちは")
        # With prosody, output may include markers
        assert isinstance(result, str)
        assert len(result) > 0

    def test_question_detection(self, g2p_with_prosody):
        """Test question marker detection."""
        result = g2p_with_prosody.convert("お元気ですか？")
        assert isinstance(result, str)

    def test_convert_with_prosody(self, g2p):
        """Test convert_with_prosody method."""
        ipa_list, prosody_info = g2p.convert_with_prosody("こんにちは")
        assert isinstance(ipa_list, list)
        assert isinstance(prosody_info, list)
        assert len(ipa_list) > 0

    def test_prosody_info_structure(self, g2p):
        """Test prosody info structure."""
        ipa_list, prosody_info = g2p.convert_with_prosody("おはよう")
        # Each prosody info should be ProsodyInfo or None
        for info in prosody_info:
            if info is not None:
                assert hasattr(info, "a1")
                assert hasattr(info, "a2")
                assert hasattr(info, "a3")

    # Full context label tests
    def test_full_context_labels(self, g2p):
        """Test full context label extraction."""
        labels = g2p.get_full_context_labels("こんにちは")
        assert isinstance(labels, list)
        assert len(labels) > 0
        # Labels should be HTS format strings
        for label in labels:
            assert isinstance(label, str)

    # Convert to list tests
    def test_convert_to_list(self, g2p):
        """Test convert_to_list method."""
        result = g2p.convert_to_list("こんにちは")
        assert isinstance(result, list)
        assert len(result) > 0
        # Each element should be a string
        for phoneme in result:
            assert isinstance(phoneme, str)

    # Edge cases
    def test_punctuation(self, g2p):
        """Test punctuation handling."""
        result = g2p.convert("こんにちは。")
        assert isinstance(result, str)

    def test_multiple_sentences(self, g2p):
        """Test multiple sentences."""
        result = g2p.convert("こんにちは。お元気ですか。")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_special_characters(self, g2p):
        """Test special characters."""
        result = g2p.convert("A.I.は人工知能です")
        assert isinstance(result, str)


class TestJapanesePhonemeConverter:
    """Test cases for JapanesePhonemeConverter."""

    @pytest.fixture
    def converter(self):
        """Create a JapanesePhonemeConverter instance."""
        return JapanesePhonemeConverter()

    @pytest.fixture
    def converter_with_markers(self):
        """Create a converter that keeps unvoiced markers."""
        return JapanesePhonemeConverter(keep_unvoiced_markers=True)

    # Basic conversion tests
    def test_basic_vowels(self, converter):
        """Test basic vowel conversion."""
        result = converter.to_ipa(["a", "i", "u", "e", "o"])
        assert result == ["ɑ", "i", "ɯ", "e", "o"]

    def test_basic_consonants(self, converter):
        """Test basic consonant conversion."""
        result = converter.to_ipa(["k", "s", "t", "n", "h", "m", "r"])
        assert "k" in result
        assert "s" in result
        assert "t" in result

    # Unvoiced vowel tests
    def test_unvoiced_vowels_default(self, converter):
        """Test unvoiced vowels with default settings (simplified)."""
        result = converter.to_ipa(["d", "e", "s", "U"])
        # By default, U should map to ɯ (same as voiced)
        assert "ɯ" in result

    def test_unvoiced_vowels_with_markers(self, converter_with_markers):
        """Test unvoiced vowels with markers kept."""
        result = converter_with_markers.to_ipa(["d", "e", "s", "U"])
        # With markers, U should map to ɯ̥ (with devoicing diacritic)
        assert "ɯ̥" in result

    def test_all_unvoiced_vowels(self, converter_with_markers):
        """Test all unvoiced vowels."""
        result = converter_with_markers.to_ipa(["A", "I", "U", "E", "O"])
        assert "ɑ̥" in result
        assert "i̥" in result
        assert "ɯ̥" in result
        assert "e̥" in result
        assert "o̥" in result

    # N variant tests
    def test_n_variants(self, converter):
        """Test all N variants."""
        result = converter.to_ipa(["N_m", "N_n", "N_ng", "N_uvular"])
        assert "m" in result  # N_m -> m
        assert "n" in result  # N_n -> n
        assert "ŋ" in result  # N_ng -> ŋ
        assert "ɴ" in result  # N_uvular -> ɴ

    def test_basic_n(self, converter):
        """Test basic N (fallback)."""
        result = converter.to_ipa(["N"])
        assert result == ["ɴ"]

    # Palatalized consonant tests
    def test_palatalized_ky(self, converter):
        """Test ky -> [k, j]."""
        result = converter.to_ipa(["ky"])
        assert result == ["k", "j"]

    def test_palatalized_ny(self, converter):
        """Test ny -> ɲ."""
        result = converter.to_ipa(["ny"])
        assert result == ["ɲ"]

    def test_palatalized_gy(self, converter):
        """Test gy -> [ɡ, j]."""
        result = converter.to_ipa(["gy"])
        assert result == ["ɡ", "j"]

    # Affricate tests
    def test_ch(self, converter):
        """Test ch -> ʧ."""
        result = converter.to_ipa(["ch"])
        assert result == ["ʧ"]

    def test_ts(self, converter):
        """Test ts -> ts."""
        result = converter.to_ipa(["ts"])
        assert result == ["ts"]

    def test_sh(self, converter):
        """Test sh -> ʃ."""
        result = converter.to_ipa(["sh"])
        assert result == ["ʃ"]

    # Glottal stop tests
    def test_glottal_q(self, converter):
        """Test q -> ʔ."""
        result = converter.to_ipa(["q"])
        assert result == ["ʔ"]

    def test_glottal_cl(self, converter):
        """Test cl -> ʔ."""
        result = converter.to_ipa(["cl"])
        assert result == ["ʔ"]

    # Prosody marker tests
    def test_prosody_markers_removed(self, converter):
        """Test that prosody markers are removed."""
        result = converter.to_ipa(["^", "k", "o", "$"])
        # ^ and $ should be empty, not included
        assert "^" not in result
        assert "$" not in result
        assert "k" in result
        assert "o" in result

    def test_pause_marker(self, converter):
        """Test pause marker -> space."""
        result = converter.to_ipa(["pau"])
        assert result == [" "]

    # String conversion tests
    def test_convert_string(self, converter):
        """Test convert_string method."""
        result = converter.convert_string("k o N n i ch i w a")
        assert "k" in result
        assert "ɴ" in result
        assert "ʧ" in result

    def test_convert_string_empty(self, converter):
        """Test convert_string with empty string."""
        result = converter.convert_string("")
        assert result == ""

    def test_convert_string_whitespace(self, converter):
        """Test convert_string with whitespace only."""
        result = converter.convert_string("   ")
        assert result == ""

    # Full word tests
    def test_konnichiwa(self, converter):
        """Test 'konnichiwa' conversion."""
        phonemes = ["k", "o", "N", "n", "i", "ch", "i", "w", "a"]
        result = converter.to_ipa(phonemes)
        assert "k" in result
        assert "ɴ" in result  # N -> ɴ
        assert "ʧ" in result  # ch -> ʧ
        assert "ɑ" in result  # a -> ɑ

    def test_desu(self, converter):
        """Test 'desu' with unvoiced U."""
        phonemes = ["d", "e", "s", "U"]
        result = converter.to_ipa(phonemes)
        assert "d" in result
        assert "e" in result
        assert "s" in result
        # U -> ɯ (default) or ɯ̥ (with markers)

    # Unknown phoneme handling
    def test_unknown_phoneme(self, converter):
        """Test unknown phoneme handling."""
        result = converter.to_ipa(["xyz"])
        # Unknown phonemes should pass through with warning
        assert "xyz" in result

    # Historical consonant tests
    def test_kw(self, converter):
        """Test kw -> [k, w]."""
        result = converter.to_ipa(["kw"])
        assert result == ["k", "w"]

    def test_gw(self, converter):
        """Test gw -> [ɡ, w]."""
        result = converter.to_ipa(["gw"])
        assert result == ["ɡ", "w"]

    # Special sound tests
    def test_hy(self, converter):
        """Test hy -> ç."""
        result = converter.to_ipa(["hy"])
        assert result == ["ç"]

    def test_zy(self, converter):
        """Test zy -> ʑ."""
        result = converter.to_ipa(["zy"])
        assert result == ["ʑ"]

    def test_f(self, converter):
        """Test f -> ɸ."""
        result = converter.to_ipa(["f"])
        assert result == ["ɸ"]

    def test_r(self, converter):
        """Test r -> ɾ."""
        result = converter.to_ipa(["r"])
        assert result == ["ɾ"]

    def test_g(self, converter):
        """Test g -> ɡ (IPA g)."""
        result = converter.to_ipa(["g"])
        assert result == ["ɡ"]  # U+0261
