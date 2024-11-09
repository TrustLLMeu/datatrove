import numpy as np

from datatrove.data import Document
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers.disk_base import DiskWriter
from datatrove.utils.text import PUNCTUATION_SET
from datatrove.utils.typeshelper import Languages
from datatrove.utils.word_tokenizers import load_word_tokenizer


STOP_WORDS = ["the", "be", "to", "of", "and", "that", "have", "with"]


class GopherQualityFilter(BaseFilter):
    name = "🥇 Gopher Quality"

    def __init__(
        self,
        min_doc_words: int | None = 50,
        max_doc_words: int | None = 100000,
        min_avg_word_length: int | None = 3,
        max_avg_word_length: int | None = 10,
        max_symbol_word_ratio: float | None = 0.1,
        max_bullet_lines_ratio: float | None = 0.9,
        max_ellipsis_lines_ratio: float | None = 0.3,
        max_non_alpha_words_ratio: float | None = 0.8,
        min_stop_words: int | None = 2,
        stop_words: list[str] | None = None,
        exclusion_writer: DiskWriter = None,
        language: str = Languages.english,
        label_only: bool = False,
    ):
        """
        Filter to apply Gopher's quality heuristic rules.
        Reference: https://arxiv.org/pdf/2112.11446.pdf

        Args:
            min_doc_words:
            max_doc_words:
            min_avg_word_length:
            max_avg_word_length:
            max_symbol_word_ratio:
            max_bullet_lines_ratio:
            max_ellipsis_lines_ratio:
            max_non_alpha_words_ratio:
            min_stop_words:
            stop_words:
            exclusion_writer:
        """
        super().__init__(exclusion_writer)
        self.min_doc_words = min_doc_words
        self.max_doc_words = max_doc_words
        self.min_avg_word_length = min_avg_word_length
        self.max_avg_word_length = max_avg_word_length
        self.max_symbol_word_ratio = max_symbol_word_ratio
        self.max_bullet_lines_ratio = max_bullet_lines_ratio
        self.max_ellipsis_lines_ratio = max_ellipsis_lines_ratio
        self.max_non_alpha_words_ratio = max_non_alpha_words_ratio
        self.min_stop_words = min_stop_words
        self.stop_words = set(STOP_WORDS if stop_words is None else stop_words)
        self.tokenizer = load_word_tokenizer(language)
        self.label_only = label_only

    def filter(self, doc: Document) -> bool | tuple[bool, str]:
        """

        Args:
            doc: Applies the heuristics rules to decide if a document should be REMOVED


        Returns: False if sample.text does not pass any of the the heuristic tests

        """
        text = doc.text
        words = self.tokenizer.word_tokenize(text)
        n_words = len(words)

        non_symbol_words = [w for w in words if any(ch not in PUNCTUATION_SET for ch in w)]
        n_non_symbol_words_words = len(non_symbol_words)

        # words < min_doc_words or words > max_doc_words
        doc.metadata["gopher_n_words"] = n_words
        doc.metadata["gopher_n_non_symbol_words"] = n_non_symbol_words_words
        if not self.label_only and self.min_doc_words and n_non_symbol_words_words < self.min_doc_words:
            return False, "gopher_short_doc"
        if not self.label_only and self.max_doc_words and n_non_symbol_words_words > self.max_doc_words:
            return False, "gopher_long_doc"

        # mean word length is outside the range of 3 to 10 characters
        avg_n_words = np.mean([len(w) for w in non_symbol_words])
        doc.metadata["gopher_avg_word_length"] = avg_n_words
        if not self.label_only and self.min_avg_word_length and avg_n_words < self.min_avg_word_length:
            return False, "gopher_below_avg_threshold"
        if not self.label_only and self.max_avg_word_length and avg_n_words > self.max_avg_word_length:
            return False, "gopher_above_avg_threshold"

        # symbol-to-word ratio greater than 0.1 for either the hash symbol or the ellipsis
        hash_count = text.count("#")
        hash_ratio = hash_count / n_words if n_words > 0 else 0.0
        ellipsis_count = text.count("...") + text.count("…")
        ellipsis_ratio = ellipsis_count / n_words if n_words > 0 else 0.0
        doc.metadata["gopher_hash_count"] = hash_count
        doc.metadata["gopher_hash_ratio"] = hash_ratio
        doc.metadata["gopher_ellipsis_count"] = ellipsis_count
        doc.metadata["gopher_ellipsis_ratio"] = ellipsis_ratio
        if (
            not self.label_only 
            and self.max_symbol_word_ratio 
            and hash_ratio > self.max_symbol_word_ratio
        ):
            return False, "gopher_too_many_hashes"
        if (
            not self.label_only
            and self.max_symbol_word_ratio
            and ellipsis_ratio > self.max_symbol_word_ratio
        ):
            return False, "gopher_too_many_ellipsis"

        # any document with more than 90 % of lines starting with a bullet point,
        # or more than 30 % ending with an ellipsis.
        lines = text.splitlines()
        bullet_lines = sum(s.lstrip().startswith("•") or s.lstrip().startswith("-") for s in lines)
        ellipsis_lines = sum(s.rstrip().endswith("...") or s.rstrip().endswith("…") for s in lines)
        doc.metadata["gopher_bullet_lines"] = bullet_lines
        doc.metadata["gopher_bullet_lines_ratio"] = bullet_lines / len(lines)
        doc.metadata["gopher_ellipsis_lines"] = ellipsis_lines
        doc.metadata["gopher_ellipsis_lines_ratio"] = ellipsis_lines / len(lines)
        if (
            not self.label_only
            and self.max_bullet_lines_ratio
            and bullet_lines / len(lines) > self.max_bullet_lines_ratio
        ):
            return False, "gopher_too_many_bullets"
        if (
            not self.label_only
            and self.max_ellipsis_lines_ratio
            and ellipsis_lines / len(lines) > self.max_ellipsis_lines_ratio
        ):
            return False, "gopher_too_many_end_ellipsis"

        # that 80 % of words in a document contain at least one alphabetic character
        non_alpha_words_count = sum([any((c.isalpha() for c in w)) for w in words])
        doc.metadata["gopher_non_alpha_words"] = non_alpha_words_count
        doc.metadata["gopher_non_alpha_words_ratio"] = non_alpha_words_count / n_words
        if (
            not self.label_only
            and self.max_non_alpha_words_ratio
            and non_alpha_words_count / n_words < self.max_non_alpha_words_ratio
        ):
            return False, "gopher_below_alpha_threshold"

        # stop word filter
        stop_words_count = sum(w in self.stop_words for w in words)
        doc.metadata["gopher_stop_words"] = stop_words_count
        if not self.label_only and self.min_stop_words and stop_words_count < self.min_stop_words:
            return False, "gopher_enough_stop_words"

        return True
