"""Tests for whoosh-fastapi plugin."""

import pytest


def test_fastapi_module_structure():
    """Test that whoosh_fastapi module has expected exports."""
    pytest.importorskip("fastapi")

    from whoosh_fastapi import create_app

    assert callable(create_app)
