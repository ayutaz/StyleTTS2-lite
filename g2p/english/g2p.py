"""English G2P using CMU dictionary with rule-based fallback."""

import re
from typing import List, Union

from .cmu_dict import CMUDict
from .fallback import RuleBasedFallback


class EnglishG2P:
    """English text to IPA phoneme converter.

    Uses CMU Pronouncing Dictionary (Public Domain) with rule-based fallback.
    """

    # ARPABET to IPA conversion table
    ARPABET_TO_IPA = {
        # Vowels
        "AA": "ɑ",
        "AE": "æ",
        "AH": "ʌ",
        "AO": "ɔ",
        "AW": ["ɑ", "ʊ"],
        "AY": ["ɑ", "ɪ"],
        "EH": "ɛ",
        "ER": "ɚ",
        "EY": ["e", "ɪ"],
        "IH": "ɪ",
        "IY": "i",
        "OW": ["o", "ʊ"],
        "OY": ["ɔ", "ɪ"],
        "UH": "ʊ",
        "UW": "u",
        # Consonants
        "B": "b",
        "CH": "ʧ",
        "D": "d",
        "DH": "ð",
        "F": "f",
        "G": "ɡ",
        "HH": "h",
        "JH": "ʤ",
        "K": "k",
        "L": "l",
        "M": "m",
        "N": "n",
        "NG": "ŋ",
        "P": "p",
        "R": "ɹ",
        "S": "s",
        "SH": "ʃ",
        "T": "t",
        "TH": "θ",
        "V": "v",
        "W": "w",
        "Y": "j",
        "Z": "z",
        "ZH": "ʒ",
    }

    # Punctuation to keep
    PUNCTUATION = set(".,!?;:'\"")

    def __init__(self):
        self.cmu_dict = CMUDict()
        self.fallback = RuleBasedFallback()

    def convert(self, text: str) -> str:
        """Convert English text to IPA phoneme string.

        Args:
            text: English text input

        Returns:
            Space-separated IPA phoneme string
        """
        words = self._tokenize(text)
        all_phonemes = []

        for word in words:
            if not word.strip():
                continue

            # Keep punctuation as-is
            if word in self.PUNCTUATION:
                all_phonemes.append(word)
                continue

            # Convert word to phonemes
            phonemes = self._convert_word(word)
            all_phonemes.extend(phonemes)
            all_phonemes.append(" ")  # Word separator

        # Clean up and return
        result = "".join(all_phonemes).strip()
        # Normalize multiple spaces
        result = re.sub(r" +", " ", result)
        return result

    def convert_to_list(self, text: str) -> List[str]:
        """Convert English text to IPA phoneme list.

        Args:
            text: English text input

        Returns:
            List of IPA phonemes
        """
        words = self._tokenize(text)
        all_phonemes = []

        for word in words:
            if not word.strip():
                continue

            if word in self.PUNCTUATION:
                all_phonemes.append(word)
                continue

            phonemes = self._convert_word(word)
            all_phonemes.extend(phonemes)

        return all_phonemes

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words and punctuation.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        # Split on whitespace and punctuation, keeping punctuation
        tokens = re.findall(r"[\w']+|[.,!?;:'\"]", text)
        return tokens

    def _convert_word(self, word: str) -> List[str]:
        """Convert a single word to IPA phonemes.

        Args:
            word: Single word

        Returns:
            List of IPA phonemes
        """
        # Look up in CMU dictionary
        arpabet = self.cmu_dict.lookup(word)

        if arpabet is None:
            # Use fallback for unknown words
            arpabet = self.fallback.predict(word)

        # Convert ARPABET to IPA
        return self._arpabet_to_ipa(arpabet)

    def _arpabet_to_ipa(self, arpabet: List[str]) -> List[str]:
        """Convert ARPABET phonemes to IPA.

        Args:
            arpabet: List of ARPABET phonemes

        Returns:
            List of IPA phonemes
        """
        ipa = []
        for phone in arpabet:
            # Remove stress markers (0, 1, 2)
            base_phone = phone.rstrip("012")
            mapped = self.ARPABET_TO_IPA.get(base_phone)

            if isinstance(mapped, list):
                ipa.extend(mapped)
            elif mapped:
                ipa.append(mapped)
            # Skip unknown phonemes

        return ipa
