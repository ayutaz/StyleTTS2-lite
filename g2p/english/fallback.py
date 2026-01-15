"""Rule-based fallback G2P for words not in CMU dictionary."""

from typing import List


class RuleBasedFallback:
    """Simple rule-based English pronunciation prediction.

    Used as fallback when a word is not found in CMU dictionary.
    Returns ARPABET phonemes.
    """

    # Basic letter to ARPABET mapping
    LETTER_TO_PHONEME = {
        "a": ["AE"],
        "b": ["B"],
        "c": ["K"],
        "d": ["D"],
        "e": ["EH"],
        "f": ["F"],
        "g": ["G"],
        "h": ["HH"],
        "i": ["IH"],
        "j": ["JH"],
        "k": ["K"],
        "l": ["L"],
        "m": ["M"],
        "n": ["N"],
        "o": ["AA"],
        "p": ["P"],
        "q": ["K"],
        "r": ["R"],
        "s": ["S"],
        "t": ["T"],
        "u": ["AH"],
        "v": ["V"],
        "w": ["W"],
        "x": ["K", "S"],
        "y": ["Y"],
        "z": ["Z"],
    }

    # Digraph patterns (2-character combinations)
    DIGRAPHS = {
        "ch": ["CH"],
        "sh": ["SH"],
        "th": ["TH"],
        "ph": ["F"],
        "wh": ["W"],
        "ck": ["K"],
        "ng": ["NG"],
        "qu": ["K", "W"],
        # Vowel digraphs
        "ee": ["IY"],
        "oo": ["UW"],
        "ea": ["IY"],
        "ou": ["AW"],
        "oi": ["OY"],
        "ow": ["OW"],
        "ai": ["EY"],
        "ay": ["EY"],
        "ey": ["IY"],
        "ie": ["IY"],
        "oa": ["OW"],
    }

    # Trigraph patterns (3-character combinations)
    TRIGRAPHS = {
        "tch": ["CH"],
        "ght": ["T"],
        "igh": ["AY"],
        "tion": ["SH", "AH", "N"],
        "sion": ["ZH", "AH", "N"],
    }

    def predict(self, word: str) -> List[str]:
        """Predict pronunciation using rules.

        Args:
            word: Word to predict pronunciation for

        Returns:
            List of ARPABET phonemes
        """
        word = word.lower()
        phonemes = []
        i = 0

        while i < len(word):
            # Try trigraphs first
            if i + 2 < len(word):
                trigraph = word[i : i + 3]
                if trigraph in self.TRIGRAPHS:
                    phonemes.extend(self.TRIGRAPHS[trigraph])
                    i += 3
                    continue

            # Try digraphs
            if i + 1 < len(word):
                digraph = word[i : i + 2]
                if digraph in self.DIGRAPHS:
                    phonemes.extend(self.DIGRAPHS[digraph])
                    i += 2
                    continue

            # Single character
            char = word[i]
            if char in self.LETTER_TO_PHONEME:
                phonemes.extend(self.LETTER_TO_PHONEME[char])
            # Skip non-alphabetic characters
            i += 1

        return phonemes
