"""pyopenjtalk output to IPA conversion for StyleTTS2-lite.

Based on piper-plus implementation with support for:
- Unvoiced vowels (A, I, U, E, O)
- Context-dependent N variants (N_m, N_n, N_ng, N_uvular)
- Long vowels
- Palatalized consonants
"""

import logging
from typing import List

_LOGGER = logging.getLogger(__name__)


class JapanesePhonemeConverter:
    """Convert pyopenjtalk phonemes to StyleTTS2-lite compatible IPA.

    Features:
    - Unvoiced vowels mapped to distinct IPA (or same as voiced for compatibility)
    - N variants mapped to appropriate nasal IPA sounds
    - Long vowels with length marker
    - Full palatalized consonant support
    """

    # pyopenjtalk -> IPA mapping
    PHONEME_MAP = {
        # Voiced vowels (lowercase from OpenJTalk)
        "a": "ɑ",
        "i": "i",
        "u": "ɯ",
        "e": "e",
        "o": "o",
        # Unvoiced vowels (uppercase from OpenJTalk full-context labels)
        # These are devoiced versions of the vowels
        # For StyleTTS2-lite, we map them to the same IPA but could add markers
        "A": "ɑ̥",  # or just "ɑ" for compatibility
        "I": "i̥",  # or just "i" for compatibility
        "U": "ɯ̥",  # or just "ɯ" for compatibility
        "E": "e̥",  # or just "e" for compatibility
        "O": "o̥",  # or just "o" for compatibility
        # Long vowels
        "a:": "ɑː",
        "i:": "iː",
        "u:": "ɯː",
        "e:": "eː",
        "o:": "oː",
        # Basic consonants
        "k": "k",
        "g": "ɡ",  # U+0261 (LATIN SMALL LETTER SCRIPT G)
        "s": "s",
        "z": "z",
        "t": "t",
        "d": "d",
        "n": "n",
        "h": "h",
        "b": "b",
        "p": "p",
        "m": "m",
        "y": "j",
        "r": "ɾ",
        "w": "w",
        "v": "v",
        # Compound consonants / Affricates
        "sh": "ʃ",
        "ch": "ʧ",
        "j": "ʤ",
        "ts": "ts",
        "f": "ɸ",
        "hy": "ç",
        "zy": "ʑ",  # Voiced alveolo-palatal fricative
        # Palatalized consonants
        "ky": ["k", "j"],
        "gy": ["ɡ", "j"],
        "ny": "ɲ",
        "by": ["b", "j"],
        "py": ["p", "j"],
        "my": ["m", "j"],
        "ry": ["ɾ", "j"],
        "ty": ["t", "j"],
        "dy": ["d", "j"],
        # Historical/rare consonants
        "kw": ["k", "w"],
        "gw": ["ɡ", "w"],
        # Special phonemes - basic N (fallback)
        "N": "ɴ",  # Syllabic nasal (ん) - uvular nasal as default
        # N phoneme variants (context-dependent)
        "N_m": "m",  # Before bilabials (m, b, p) - bilabial nasal
        "N_n": "n",  # Before alveolars (n, t, d, ts, ch) - alveolar nasal
        "N_ng": "ŋ",  # Before velars (k, g) - velar nasal
        "N_uvular": "ɴ",  # At end or before vowels - uvular nasal
        # Glottal stop (促音 っ)
        "q": "ʔ",
        "cl": "ʔ",
        # Pause markers
        "pau": " ",
        "sil": "",
        "sp": " ",
        # Prosody markers (if use_prosody is enabled)
        "^": "",  # Beginning of sentence - skip in IPA output
        "$": "",  # End of sentence
        "?": "",  # Question
        "?!": "",  # Emphatic question
        "?.": "",  # Neutral question
        "?~": "",  # Tag question
        "_": " ",  # Short pause
        "#": "",  # Accent phrase boundary
        "[": "",  # Rising pitch mark
        "]": "",  # Falling pitch mark
    }

    def __init__(self, keep_unvoiced_markers: bool = False):
        """Initialize the converter.

        Args:
            keep_unvoiced_markers: If True, keep diacritics for unvoiced vowels.
                                   If False, map unvoiced vowels to same as voiced.
        """
        self.keep_unvoiced_markers = keep_unvoiced_markers

        # Create a copy of the phoneme map
        self._phoneme_map = dict(self.PHONEME_MAP)

        # Optionally simplify unvoiced vowels
        if not keep_unvoiced_markers:
            self._phoneme_map["A"] = "ɑ"
            self._phoneme_map["I"] = "i"
            self._phoneme_map["U"] = "ɯ"
            self._phoneme_map["E"] = "e"
            self._phoneme_map["O"] = "o"

    def to_ipa(self, phonemes: List[str]) -> List[str]:
        """Convert pyopenjtalk phoneme list to IPA.

        Args:
            phonemes: List of pyopenjtalk phonemes

        Returns:
            List of IPA characters
        """
        result = []
        for p in phonemes:
            # Handle case sensitivity
            # N and N_* variants are special (uppercase)
            # Unvoiced vowels are uppercase (A, I, U, E, O)
            if p.startswith("N") or p in ("A", "I", "U", "E", "O"):
                p_key = p
            else:
                p_key = p.lower() if p not in self._phoneme_map else p

            if p_key in self._phoneme_map:
                mapped = self._phoneme_map[p_key]
                if mapped:  # Skip empty strings
                    if isinstance(mapped, list):
                        result.extend(mapped)
                    else:
                        result.append(mapped)
            else:
                # Unknown phoneme - log warning and pass through
                _LOGGER.warning(f"Unknown Japanese phoneme: {p}")
                result.append(p)

        return result

    def convert_string(self, phoneme_str: str) -> str:
        """Convert space-separated pyopenjtalk output to IPA string.

        Args:
            phoneme_str: Space-separated phonemes (e.g., "k o N n i ch i w a")

        Returns:
            IPA string (e.g., "k o ɴ n i ʧ i w ɑ")
        """
        if not phoneme_str or not phoneme_str.strip():
            return ""
        phonemes = phoneme_str.split()
        ipa_list = self.to_ipa(phonemes)
        return " ".join(ipa_list)
