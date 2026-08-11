"""Tests for whoosh-fastapi plugin."""

from __future__ import annotations

import pytest


def test_fastapi_module_structure():
    """Test that whoosh_fastapi module has expected exports."""
    pytest.importorskip("fastapi")

    from whoosh_fastapi import create_app

    assert callable(create_app)


def test_fastapi_websocket_autocomplete():
    """Test that the WebSocket autocomplete endpoint is registered."""
    pytest.importorskip("fastapi")

    from whoosh_fastapi import create_app

    app = create_app(None)  # type: ignore[arg-type]

    routes = [route.path for route in app.routes]
    assert "/api/v1/autocomplete/ws" in routes
