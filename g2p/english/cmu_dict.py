"""CMU Pronouncing Dictionary loader using NLTK."""

import logging
from typing import Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


class CMUDict:
    """CMU Pronouncing Dictionary wrapper.

    Uses NLTK's CMU dictionary (Public Domain license).
    """

    def __init__(self):
        self._dict: Dict[str, List[List[str]]] = {}
        self._loaded = False

    def _ensure_loaded(self):
        """Lazy load the CMU dictionary."""
        if self._loaded:
            return

        try:
            import nltk

            # Download CMU dictionary if not available
            try:
                nltk.data.find("corpora/cmudict")
            except LookupError:
                _LOGGER.info("Downloading CMU dictionary...")
                nltk.download("cmudict", quiet=True)

            from nltk.corpus import cmudict

            self._dict = cmudict.dict()
            self._loaded = True
            _LOGGER.info(f"CMU dictionary loaded: {len(self._dict)} words")

        except ImportError:
            _LOGGER.error("NLTK is required for CMU dictionary. Install with: pip install nltk")
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to load CMU dictionary: {e}")
            raise

    def lookup(self, word: str) -> Optional[List[str]]:
        """Look up a word's pronunciation.

        Args:
            word: English word to look up

        Returns:
            List of ARPABET phonemes, or None if not found
        """
        self._ensure_loaded()

        word_lower = word.lower()
        pronunciations = self._dict.get(word_lower)

        if pronunciations:
            # Return first pronunciation
            return pronunciations[0]
        return None

    def lookup_all(self, word: str) -> Optional[List[List[str]]]:
        """Look up all pronunciations of a word.

        Args:
            word: English word to look up

        Returns:
            List of all pronunciations (each is a list of ARPABET phonemes)
        """
        self._ensure_loaded()
        return self._dict.get(word.lower())

    def has_word(self, word: str) -> bool:
        """Check if a word exists in the dictionary.

        Args:
            word: Word to check

        Returns:
            True if word is in dictionary
        """
        self._ensure_loaded()
        return word.lower() in self._dict

    @property
    def size(self) -> int:
        """Get the number of words in the dictionary."""
        self._ensure_loaded()
        return len(self._dict)
