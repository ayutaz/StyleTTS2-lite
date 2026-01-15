"""pyopenjtalk output to IPA conversion for StyleTTS2-lite."""

from typing import List


class JapanesePhonemeConverter:
    """Convert pyopenjtalk phonemes to StyleTTS2-lite compatible IPA."""

    # pyopenjtalk -> IPA mapping
    PHONEME_MAP = {
        # Vowels
        "a": "ɑ",
        "i": "i",
        "u": "ɯ",
        "e": "e",
        "o": "o",
        # Consonants
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
        # Compound consonants
        "sh": "ʃ",
        "ch": "ʧ",
        "j": "ʤ",
        "ts": "ts",
        "f": "ɸ",
        "hy": "ç",
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
        # Special phonemes
        "N": "ɴ",  # Syllabic nasal (ん)
        "q": "ʔ",  # Glottal stop (っ)
        "cl": "ʔ",  # Glottal stop (alternate)
        # Pause markers
        "pau": " ",
        "sil": "",
        "sp": " ",
    }

    def to_ipa(self, phonemes: List[str]) -> List[str]:
        """Convert pyopenjtalk phoneme list to IPA.

        Args:
            phonemes: List of pyopenjtalk phonemes (e.g., ["k", "o", "N", "n", "i", "ch", "i", "w", "a"])

        Returns:
            List of IPA characters
        """
        result = []
        for p in phonemes:
            # Handle case sensitivity (N is special)
            p_key = p if p == "N" else p.lower()

            if p_key in self.PHONEME_MAP:
                mapped = self.PHONEME_MAP[p_key]
                if mapped:  # Skip empty strings
                    if isinstance(mapped, list):
                        result.extend(mapped)
                    else:
                        result.append(mapped)
            else:
                # Unknown phoneme - pass through with warning
                print(f"WARNING: Unknown Japanese phoneme: {p}")
                result.append(p)

        return result

    def convert_string(self, phoneme_str: str) -> str:
        """Convert space-separated pyopenjtalk output to IPA string.

        Args:
            phoneme_str: Space-separated phonemes (e.g., "k o N n i ch i w a")

        Returns:
            IPA string (e.g., "k o ɴ n i ʧ i w ɑ")
        """
        phonemes = phoneme_str.split()
        ipa_list = self.to_ipa(phonemes)
        return " ".join(ipa_list)
