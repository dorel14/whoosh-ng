from __future__ import annotations

from typing import Any

import pytest

from whoosh.hooks import HookImpl, call_hook, hookimpl, register_hook


@pytest.fixture(autouse=True)
def isolated_hooks() -> None:
    from whoosh import hooks as _hooks_mod

    _hooks_mod._hooks.clear()


def test_hookimpl_decorator_returns_hook_impl() -> None:
    async def _impl(x: int) -> int:
        return x

    impl = hookimpl(_impl)
    assert impl.func is _impl


@pytest.mark.asyncio
async def test_register_and_call_hook() -> None:
    from whoosh.hooks import _hooks

    async def transform(data: dict[str, Any]) -> dict[str, Any]:
        return {"transformed": True, **data}

    register_hook("process", hookimpl(transform))
    result = await call_hook("process", {"value": 1})
    assert result[0] == {"transformed": True, "value": 1}


@pytest.mark.asyncio
async def test_hook_exception_isolation() -> None:
    async def bad() -> None:
        raise RuntimeError("oops")

    async def good() -> str:
        return "ok"

    register_hook("sample", hookimpl(bad))
    register_hook("sample", hookimpl(good))

    result = await call_hook("sample")
    assert result[0] == "ok"


@pytest.mark.asyncio
async def test_multiple_hooks_return_list() -> None:
    async def first(x: int) -> int:
        return x + 1

    async def second(x: int) -> int:
        return x + 2

    register_hook("chain", hookimpl(first))
    register_hook("chain", hookimpl(second))

    results = await call_hook("chain", 5)
    assert results == [6, 7]


def test_hookimpl_stores_function() -> None:
    def sync_func() -> str:
        return "sync"

    impl = hookimpl(sync_func)
    assert callable(impl.func)
    assert impl.func() == "sync"
