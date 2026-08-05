"""Unicode regression tests for RegexTokenizer.

Validates that the global compiled regex behaves identically to per-instance regex.
"""

from __future__ import annotations

import pytest

from whoosh.analysis.tokenizers import RegexTokenizer, default_pattern


class TestRegexTokenizerUnicode:
    """Test Unicode handling in RegexTokenizer."""

    @pytest.fixture
    def tokenizer(self):
        """Default RegexTokenizer instance."""
        return RegexTokenizer()

    @pytest.fixture
    def custom_tokenizer(self):
        """Custom RegexTokenizer with explicit pattern."""
        return RegexTokenizer(expression=r"\w+(\.?\w+)*")

    def test_basic_ascii(self, tokenizer):
        """Test basic ASCII tokenization."""
        tokens = [t.copy() for t in tokenizer("hello world")]
        assert [t.text for t in tokens] == ["hello", "world"]

    def test_default_pattern_uses_global(self):
        """Test that default pattern uses global compiled regex."""
        tokenizer = RegexTokenizer()
        assert tokenizer._uses_global is True
        assert tokenizer.expression is default_pattern

    def test_custom_pattern_does_not_use_global(self):
        """Test that custom pattern creates its own compiled regex."""
        tokenizer = RegexTokenizer(expression=r"\w+")
        assert tokenizer._uses_global is False

    def test_unicode_ascii(self, tokenizer):
        """Test Unicode ASCII characters."""
        tokens = [t.copy() for t in tokenizer("café résumé naïve")]
        assert [t.text for t in tokens] == ["café", "résumé", "naïve"]

    def test_unicode_emoji(self, tokenizer):
        """Test Unicode emoji handling."""
        tokens = [t.copy() for t in tokenizer("hello 🌍 world")]
        # Emoji should be skipped by \w pattern
        assert [t.text for t in tokens] == ["hello", "world"]

    def test_unicode_numbers(self, tokenizer):
        """Test Unicode numbers."""
        tokens = [t.copy() for t in tokenizer("test 123 456")]
        assert [t.text for t in tokens] == ["test", "123", "456"]

    def test_unicode_mixed(self, tokenizer):
        """Test mixed Unicode content."""
        text = "The quick brown fox jumps over 2 lazy dogs"
        tokens = [t.copy() for t in tokenizer(text)]
        assert len(tokens) == 9
        assert tokens[0].text == "The"
        assert tokens[4].text == "jumps"

    def test_unicode_accents(self, tokenizer):
        """Test various accent patterns."""
        texts = [
            ("café", ["café"]),
            ("résumé", ["résumé"]),
            ("naïve", ["naïve"]),
            ("Über", ["Über"]),
            ("München", ["München"]),
        ]
        for text, expected in texts:
            tokens = [t.copy() for t in tokenizer(text)]
            assert [t.text for t in tokens] == expected

    def test_unicode_hyphens(self, tokenizer):
        """Test hyphenated words."""
        tokens = [t.copy() for t in tokenizer("well-known")]
        # Hyphens are not word characters, so this splits
        assert "well" in [t.text for t in tokens]
        assert "known" in [t.text for t in tokens]

    def test_unicode_underscores(self, tokenizer):
        """Test underscore-separated words."""
        tokens = [t.copy() for t in tokenizer("under_score")]
        # Underscores are word characters
        assert [t.text for t in tokens] == ["under_score"]

    def test_unicode_dots(self, tokenizer):
        """Test dot-separated patterns."""
        tokens = [t.copy() for t in tokenizer("3.141")]
        assert [t.text for t in tokens] == ["3.141"]

    def test_custom_pattern_equivalence(self, tokenizer, custom_tokenizer):
        """Test that custom pattern with same regex gives same results."""
        text = "hello world 3.14"
        tokens1 = [t.copy() for t in tokenizer(text)]
        tokens2 = [t.copy() for t in custom_tokenizer(text)]
        assert [t.text for t in tokens1] == [t.text for t in tokens2]

    def test_positions_unicode(self, tokenizer):
        """Test position tracking with Unicode."""
        tokens = [t.copy() for t in tokenizer("café résumé", positions=True)]
        assert tokens[0].pos == 0
        assert tokens[1].pos == 1

    def test_chars_unicode(self, tokenizer):
        """Test character offsets with Unicode."""
        tokens = [t.copy() for t in tokenizer("café", chars=True)]
        assert tokens[0].startchar == 0
        assert tokens[0].endchar == 4  # é is 2 bytes in UTF-8, but len("café") = 4

    def test_empty_string(self, tokenizer):
        """Test empty string."""
        tokens = list(tokenizer(""))
        assert tokens == []

    def test_only_spaces(self, tokenizer):
        """Test string with only spaces."""
        tokens = list(tokenizer("   "))
        assert tokens == []

    def test_unicode_whitespace(self, tokenizer):
        """Test various Unicode whitespace."""
        tokens = [t.copy() for t in tokenizer("hello\tworld\n")]
        assert [t.text for t in tokens] == ["hello", "world"]

    def test_gaps_mode_unicode(self):
        """Test gaps mode with Unicode."""
        tokenizer = RegexTokenizer(expression=r"\s+", gaps=True)
        tokens = [t.copy() for t in tokenizer("hello world café")]
        assert [t.text for t in tokens] == ["hello", "world", "café"]

    def test_keeporiginal_unicode(self, tokenizer):
        """Test keeporiginal with Unicode."""
        tokens = [t.copy() for t in tokenizer("café", keeporiginal=True)]
        assert tokens[0].text == "café"
        assert tokens[0].original == "café"

    def test_removestops_unicode(self):
        """Test stop removal with Unicode."""
        from whoosh.analysis.filters import StopFilter
        from whoosh.analysis.tokenizers import RegexTokenizer

        stoplist = ["le", "la", "les"]
        tokenizer = RegexTokenizer() | StopFilter(stoplist=stoplist)
        tokens = [t.copy() for t in tokenizer("le café la résumé")]
        assert "le" not in [t.text for t in tokens]
        assert "la" not in [t.text for t in tokens]
        assert "café" in [t.text for t in tokens]
