"""Japanese G2P using pyopenjtalk-plus."""

import logging
from typing import List, Optional

from .converter import JapanesePhonemeConverter

_LOGGER = logging.getLogger(__name__)

# Try to import pyopenjtalk
try:
    import pyopenjtalk

    HAS_PYOPENJTALK = True
except ImportError:
    HAS_PYOPENJTALK = False
    _LOGGER.warning("pyopenjtalk not available. Install with: uv add pyopenjtalk-plus")


class JapaneseG2P:
    """Japanese text to IPA phoneme converter using pyopenjtalk-plus."""

    def __init__(self):
        if not HAS_PYOPENJTALK:
            raise RuntimeError(
                "pyopenjtalk is required for Japanese G2P. "
                "Install with: uv add pyopenjtalk-plus"
            )
        self.converter = JapanesePhonemeConverter()

    def convert(self, text: str) -> str:
        """Convert Japanese text to IPA phoneme string.

        Args:
            text: Japanese text input

        Returns:
            Space-separated IPA phoneme string
        """
        # Get phonemes from pyopenjtalk
        phoneme_str = pyopenjtalk.g2p(text)
        # Example output: "k o N n i ch i w a"

        # Convert to IPA
        return self.converter.convert_string(phoneme_str)

    def convert_to_list(self, text: str) -> List[str]:
        """Convert Japanese text to IPA phoneme list.

        Args:
            text: Japanese text input

        Returns:
            List of IPA phonemes
        """
        phoneme_str = pyopenjtalk.g2p(text)
        phonemes = phoneme_str.split()
        return self.converter.to_ipa(phonemes)

    def get_full_context_labels(self, text: str) -> List[str]:
        """Get full context labels from pyopenjtalk (for advanced prosody).

        Args:
            text: Japanese text input

        Returns:
            List of full context label strings
        """
        return pyopenjtalk.make_label(pyopenjtalk.run_frontend(text))
