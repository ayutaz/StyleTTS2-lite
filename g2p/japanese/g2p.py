"""Japanese G2P using pyopenjtalk-plus with full-context label support.

This implementation is based on piper-plus's approach, using full-context labels
from OpenJTalk for better phoneme extraction including:
- Unvoiced vowels (A, I, U, E, O)
- Context-dependent N variants
- Prosody marks (optional)
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .converter import JapanesePhonemeConverter

_LOGGER = logging.getLogger(__name__)

# Try to import pyopenjtalk
try:
    import pyopenjtalk

    HAS_PYOPENJTALK = True
except ImportError:
    HAS_PYOPENJTALK = False
    _LOGGER.warning("pyopenjtalk not available. Install with: uv add pyopenjtalk-plus")


# Regular expressions for full-context label parsing
_RE_PHONEME = re.compile(r"-([^+]+)\+")
_RE_A1 = re.compile(r"/A:([\d-]+)\+")
_RE_A2 = re.compile(r"\+([0-9]+)\+")
_RE_A3 = re.compile(r"\+([0-9]+)/")


@dataclass
class ProsodyInfo:
    """Prosody information extracted from OpenJTalk labels.

    Attributes:
        a1: Relative position from accent nucleus (-4, -3, ..., 0, 1, ...)
        a2: Position of current mora in the accent phrase (1-based)
        a3: Total number of morae in the current accent phrase
    """

    a1: int
    a2: int
    a3: int


# Tokens to skip when looking for next phoneme (for N variant rules)
_SKIP_TOKENS = frozenset(("_", "#", "[", "]", "^", "$", "?", "?!", "?.", "?~", "pau", "sil"))


class JapaneseG2P:
    """Japanese text to IPA phoneme converter using pyopenjtalk-plus.

    Features (based on piper-plus implementation):
    - Full-context label parsing for accurate phoneme extraction
    - Unvoiced vowel support (A, I, U, E, O)
    - Context-dependent N phoneme variants
    - Optional prosody mark extraction
    """

    def __init__(self, use_prosody: bool = False, use_n_variants: bool = True):
        """Initialize Japanese G2P.

        Args:
            use_prosody: If True, include prosody marks (^, $, #, [, ])
            use_n_variants: If True, use context-dependent N variants
        """
        if not HAS_PYOPENJTALK:
            raise RuntimeError(
                "pyopenjtalk is required for Japanese G2P. "
                "Install with: uv add pyopenjtalk-plus"
            )
        self.converter = JapanesePhonemeConverter()
        self.use_prosody = use_prosody
        self.use_n_variants = use_n_variants

    def convert(self, text: str) -> str:
        """Convert Japanese text to IPA phoneme string.

        Args:
            text: Japanese text input

        Returns:
            Space-separated IPA phoneme string
        """
        if not text or not text.strip():
            return ""

        phonemes = self._extract_phonemes_from_labels(text)

        if self.use_n_variants:
            phonemes = self._apply_n_phoneme_rules(phonemes)

        # Convert to IPA
        ipa_list = self.converter.to_ipa(phonemes)
        return " ".join(ipa_list)

    def convert_to_list(self, text: str) -> List[str]:
        """Convert Japanese text to IPA phoneme list.

        Args:
            text: Japanese text input

        Returns:
            List of IPA phonemes
        """
        if not text or not text.strip():
            return []

        phonemes = self._extract_phonemes_from_labels(text)

        if self.use_n_variants:
            phonemes = self._apply_n_phoneme_rules(phonemes)

        return self.converter.to_ipa(phonemes)

    def convert_with_prosody(self, text: str) -> Tuple[List[str], List[Optional[ProsodyInfo]]]:
        """Convert Japanese text to IPA with prosody information.

        Args:
            text: Japanese text input

        Returns:
            Tuple of (IPA phoneme list, prosody info list)
        """
        if not text or not text.strip():
            return [], []

        phonemes, prosody_info = self._extract_phonemes_with_prosody(text)

        if self.use_n_variants:
            phonemes = self._apply_n_phoneme_rules(phonemes)

        ipa_list = self.converter.to_ipa(phonemes)
        return ipa_list, prosody_info

    def _extract_phonemes_from_labels(self, text: str) -> List[str]:
        """Extract phonemes from full-context labels.

        Uses pyopenjtalk.extract_fullcontext() for accurate phoneme extraction
        including unvoiced vowels.
        """
        labels = pyopenjtalk.extract_fullcontext(text)
        phonemes: List[str] = []

        for idx, label in enumerate(labels):
            m_ph = _RE_PHONEME.search(label)
            if not m_ph:
                continue

            phoneme = m_ph.group(1)

            # Handle silence markers
            if phoneme == "sil":
                if self.use_prosody:
                    if idx == 0:
                        phonemes.append("^")
                    elif idx == len(labels) - 1:
                        phonemes.append(self._get_question_type(text))
                continue

            # Handle pause
            if phoneme == "pau":
                if self.use_prosody:
                    phonemes.append("_")
                continue

            # Keep phoneme (including unvoiced vowels as uppercase)
            phonemes.append(phoneme)

            # Add prosody marks if enabled
            if self.use_prosody:
                self._add_prosody_marks(phonemes, labels, idx, label)

        return phonemes

    def _extract_phonemes_with_prosody(
        self, text: str
    ) -> Tuple[List[str], List[Optional[ProsodyInfo]]]:
        """Extract phonemes with prosody information."""
        labels = pyopenjtalk.extract_fullcontext(text)
        phonemes: List[str] = []
        prosody_info: List[Optional[ProsodyInfo]] = []

        for idx, label in enumerate(labels):
            m_ph = _RE_PHONEME.search(label)
            if not m_ph:
                continue

            phoneme = m_ph.group(1)

            if phoneme == "sil":
                if idx == 0:
                    phonemes.append("^")
                    prosody_info.append(None)
                elif idx == len(labels) - 1:
                    phonemes.append(self._get_question_type(text))
                    prosody_info.append(None)
                continue

            if phoneme == "pau":
                phonemes.append("_")
                prosody_info.append(None)
                continue

            phonemes.append(phoneme)

            # Extract A1/A2/A3 values
            m_a1 = _RE_A1.search(label)
            m_a2 = _RE_A2.search(label)
            m_a3 = _RE_A3.search(label)

            if m_a1 and m_a2 and m_a3:
                a1 = int(m_a1.group(1))
                a2 = int(m_a2.group(1))
                a3 = int(m_a3.group(1))
                prosody_info.append(ProsodyInfo(a1=a1, a2=a2, a3=a3))
            else:
                prosody_info.append(None)

        return phonemes, prosody_info

    def _add_prosody_marks(
        self, phonemes: List[str], labels: List[str], idx: int, label: str
    ) -> None:
        """Add prosody marks based on accent information."""
        m_a1 = _RE_A1.search(label)
        m_a2 = _RE_A2.search(label)
        m_a3 = _RE_A3.search(label)

        if not (m_a1 and m_a2 and m_a3):
            return

        a1 = int(m_a1.group(1))
        a2 = int(m_a2.group(1))
        a3 = int(m_a3.group(1))

        # Look-ahead for next label
        if idx < len(labels) - 1:
            m_a2_next = _RE_A2.search(labels[idx + 1])
            a2_next = int(m_a2_next.group(1)) if m_a2_next else -1
        else:
            a2_next = -1

        # Accent nucleus mark "]"
        if (a1 == 0) and (a2_next == a2 + 1):
            phonemes.append("]")

        # Accent phrase boundary "#"
        if (a2 == a3) and (a2_next == 1):
            phonemes.append("#")

        # Rising mark "["
        if (a2 == 1) and (a2_next == 2):
            phonemes.append("[")

    def _apply_n_phoneme_rules(self, phonemes: List[str]) -> List[str]:
        """Apply context-dependent rules to replace 'N' with specific variants.

        Japanese 'ん' (N) has different pronunciations:
        - N_m: before m/b/p (bilabial assimilation)
        - N_n: before n/t/d/ts/ch (alveolar assimilation)
        - N_ng: before k/g (velar assimilation)
        - N_uvular: at phrase end or before vowels/other consonants
        """
        result = []
        for i, phoneme in enumerate(phonemes):
            if phoneme != "N":
                result.append(phoneme)
                continue

            # Look ahead to find next actual phoneme
            next_phoneme = None
            for j in range(i + 1, len(phonemes)):
                if phonemes[j] not in _SKIP_TOKENS:
                    next_phoneme = phonemes[j]
                    break

            # Determine N variant based on next phoneme
            if next_phoneme is None:
                result.append("N_uvular")
            elif next_phoneme in ("m", "my", "b", "by", "p", "py"):
                result.append("N_m")
            elif next_phoneme in ("n", "ny", "t", "ty", "d", "dy", "ts", "ch"):
                result.append("N_n")
            elif next_phoneme in ("k", "ky", "kw", "g", "gy", "gw"):
                result.append("N_ng")
            else:
                result.append("N_uvular")

        return result

    def _get_question_type(self, text: str) -> str:
        """Return question marker based on text ending."""
        stripped = text.strip()

        if stripped.endswith("?!") or stripped.endswith("！？") or stripped.endswith("？！"):
            return "?!"
        if stripped.endswith("?.") or stripped.endswith("。？") or stripped.endswith("？。"):
            return "?."
        if stripped.endswith("?~") or stripped.endswith("～？") or stripped.endswith("？～"):
            return "?~"
        if stripped.endswith("?") or stripped.endswith("？"):
            return "?"
        return "$"

    def get_full_context_labels(self, text: str) -> List[str]:
        """Get full context labels from pyopenjtalk (for advanced prosody).

        Args:
            text: Japanese text input

        Returns:
            List of full context label strings
        """
        return pyopenjtalk.extract_fullcontext(text)
