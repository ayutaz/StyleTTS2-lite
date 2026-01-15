"""Unified Japanese-English G2P Pipeline for StyleTTS2-lite."""

import re
from typing import Optional

from .japanese import JapaneseG2P
from .english import EnglishG2P

__all__ = ["G2PPipeline", "JapaneseG2P", "EnglishG2P"]


class G2PPipeline:
    """Unified G2P pipeline supporting Japanese and English.

    Automatically detects language and converts text to IPA phonemes
    compatible with StyleTTS2-lite.

    License: All components are GPL-free.
    - Japanese: pyopenjtalk-plus (MIT/BSD)
    - English: CMU dictionary (Public Domain)
    """

    # Japanese character patterns
    JAPANESE_PATTERN = re.compile(
        r"[\u3040-\u309F"  # Hiragana
        r"\u30A0-\u30FF"  # Katakana
        r"\u4E00-\u9FFF"  # CJK Unified Ideographs (Kanji)
        r"\uFF65-\uFF9F]",  # Halfwidth Katakana
        re.UNICODE,
    )

    # English character pattern
    ENGLISH_PATTERN = re.compile(r"[a-zA-Z]")

    def __init__(self):
        """Initialize G2P pipeline with lazy loading."""
        self._japanese_g2p: Optional[JapaneseG2P] = None
        self._english_g2p: Optional[EnglishG2P] = None

    @property
    def japanese_g2p(self) -> JapaneseG2P:
        """Lazy load Japanese G2P."""
        if self._japanese_g2p is None:
            self._japanese_g2p = JapaneseG2P()
        return self._japanese_g2p

    @property
    def english_g2p(self) -> EnglishG2P:
        """Lazy load English G2P."""
        if self._english_g2p is None:
            self._english_g2p = EnglishG2P()
        return self._english_g2p

    def convert(self, text: str, language: Optional[str] = None) -> str:
        """Convert text to IPA phoneme string.

        Args:
            text: Input text (Japanese, English, or mixed)
            language: Force language ('ja', 'en', or None for auto-detect)

        Returns:
            Space-separated IPA phoneme string
        """
        # Normalize text
        text = self._normalize(text)

        # Detect language if not specified
        if language is None:
            language = self._detect_language(text)

        # Process based on language
        if language == "ja":
            return self.japanese_g2p.convert(text)
        elif language == "en":
            return self.english_g2p.convert(text)
        else:  # mixed
            return self._convert_mixed(text)

    def _normalize(self, text: str) -> str:
        """Normalize text for processing.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Convert full-width punctuation to half-width
        replacements = {
            "。": ".",
            "、": ",",
            "！": "!",
            "？": "?",
            "：": ":",
            "；": ";",
            "「": '"',
            "」": '"',
            "『": '"',
            "』": '"',
        }
        for jp, en in replacements.items():
            text = text.replace(jp, en)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _detect_language(self, text: str) -> str:
        """Detect the dominant language of text.

        Args:
            text: Input text

        Returns:
            'ja' for Japanese, 'en' for English, 'mixed' for both
        """
        has_japanese = bool(self.JAPANESE_PATTERN.search(text))
        has_english = bool(self.ENGLISH_PATTERN.search(text))

        if has_japanese and has_english:
            return "mixed"
        elif has_japanese:
            return "ja"
        else:
            return "en"

    def _convert_mixed(self, text: str) -> str:
        """Convert mixed Japanese-English text.

        Args:
            text: Mixed language text

        Returns:
            Space-separated IPA phoneme string
        """
        result = []
        current_text = ""
        current_lang: Optional[str] = None

        for char in text:
            # Determine character's language
            if self.JAPANESE_PATTERN.match(char):
                char_lang = "ja"
            elif char.isalpha():
                char_lang = "en"
            else:
                # Punctuation/whitespace - add to current segment
                current_text += char
                continue

            # If language changed, process the accumulated text
            if current_lang and char_lang != current_lang:
                if current_text.strip():
                    if current_lang == "ja":
                        result.append(self.japanese_g2p.convert(current_text.strip()))
                    else:
                        result.append(self.english_g2p.convert(current_text.strip()))
                current_text = ""

            current_lang = char_lang
            current_text += char

        # Process remaining text
        if current_text.strip() and current_lang:
            if current_lang == "ja":
                result.append(self.japanese_g2p.convert(current_text.strip()))
            else:
                result.append(self.english_g2p.convert(current_text.strip()))

        return " ".join(result)
