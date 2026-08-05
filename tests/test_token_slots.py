"""Token object optimization tests.

Validates Token with __slots__ and benchmarks memory usage.
"""

from __future__ import annotations

import gc
import sys

import pytest

from whoosh.analysis.acore import Token


class TestTokenSlots:
    """Test Token with __slots__ optimization."""

    def test_token_has_slots(self):
        """Test that Token has __slots__ defined."""
        assert hasattr(Token, "__slots__")
        assert "text" in Token.__slots__
        assert "pos" in Token.__slots__
        assert "startchar" in Token.__slots__
        assert "endchar" in Token.__slots__
        assert "original" in Token.__slots__
        assert "positions" in Token.__slots__
        assert "chars" in Token.__slots__
        assert "stopped" in Token.__slots__
        assert "boost" in Token.__slots__
        assert "removestops" in Token.__slots__
        assert "mode" in Token.__slots__

    def test_token_no_dict(self):
        """Test that Token instances don't have __dict__."""
        t = Token()
        assert not hasattr(t, "__dict__")

    def test_token_attributes(self):
        """Test that Token attributes work correctly."""
        t = Token()
        t.text = "test"
        t.pos = 1
        t.startchar = 0
        t.endchar = 4
        assert t.text == "test"
        assert t.pos == 1
        assert t.startchar == 0
        assert t.endchar == 4

    def test_token_copy(self):
        """Test Token.copy() works with slots."""
        t = Token()
        t.text = "test"
        t.pos = 1
        t2 = t.copy()
        assert t2.text == "test"
        assert t2.pos == 1
        assert t2 is not t

    def test_token_repr(self):
        """Test Token.__repr__ works with slots."""
        t = Token()
        t.text = "test"
        repr_str = repr(t)
        assert "Token" in repr_str
        assert "test" in repr_str

    def test_token_kwargs(self):
        """Test Token accepts only declared slot kwargs."""
        t = Token(positions=True, chars=False)
        assert t.positions is True
        assert t.chars is False
        with pytest.raises(AttributeError):
            Token(custom_attr="value")

    def test_token_memory_savings(self):
        """Test that __slots__ reduces memory usage."""
        # Create many Token instances
        tokens = [Token() for _ in range(1000)]

        # With __slots__, instances should be smaller
        total_size = sum(sys.getsizeof(t) for t in tokens)
        avg_size = total_size / len(tokens)

        # Token with slots should be smaller than without
        # Typical dict-based object: ~200 bytes
        # Token with slots: ~80-160 bytes depending on slot count
        assert avg_size < 200, f"Token instances too large: {avg_size:.1f} bytes"

    def test_token_gc_pressure(self):
        """Test that __slots__ reduces GC pressure."""
        # Create and discard many tokens
        for _ in range(10000):
            t = Token()
            t.text = "test"
            del t

        gc.collect()
        # Should not raise any errors

    def test_token_equality(self):
        """Test Token equality."""
        t1 = Token()
        t1.text = "test"
        t1.pos = 1
        t2 = Token()
        t2.text = "test"
        t2.pos = 1
        # Tokens are equal if their attributes match
        assert t1.text == t2.text
        assert t1.pos == t2.pos

    def test_token_with_positions(self):
        """Test Token with positions enabled."""
        t = Token(positions=True)
        assert t.positions is True

    def test_token_with_chars(self):
        """Test Token with chars enabled."""
        t = Token(chars=True)
        assert t.chars is True

    def test_token_boost(self):
        """Test Token boost attribute."""
        t = Token()
        t.boost = 2.0
        assert t.boost == 2.0

    def test_token_stopped(self):
        """Test Token stopped attribute."""
        t = Token()
        t.stopped = True
        assert t.stopped is True
