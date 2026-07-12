from __future__ import annotations

import pytest

from whoosh.event_bus import DocumentIndexed, Event, EventBus, event_bus, SearchExecuted


@pytest.fixture(autouse=True)
def isolated_bus() -> None:
    event_bus._listeners.clear()


def test_event_bus_publishes_to_listener() -> None:
    received: list[DocumentIndexed] = []

    @event_bus.subscribe(DocumentIndexed)
    async def listener(event: DocumentIndexed) -> None:
        received.append(event)

    event = DocumentIndexed(document_id="1")
    event_bus.publish(event)
    assert len(received) == 1
    assert received[0].document_id == "1"


def test_multiple_listeners_same_event() -> None:
    count = {"total": 0}

    @event_bus.subscribe(DocumentIndexed)
    async def first(event: DocumentIndexed) -> None:
        count["total"] += 1

    @event_bus.subscribe(DocumentIndexed)
    async def second(event: DocumentIndexed) -> None:
        count["total"] += 10

    event_bus.publish(DocumentIndexed(document_id="x"))
    assert count["total"] == 11


def test_exception_isolation_does_not_stop_others() -> None:
    state = {"ok": False}

    @event_bus.subscribe(DocumentIndexed)
    async def failing_listener(event: DocumentIndexed) -> None:
        raise RuntimeError("fail")

    @event_bus.subscribe(DocumentIndexed)
    async def ok_listener(event: DocumentIndexed) -> None:
        state["ok"] = True

    event_bus.publish(DocumentIndexed(document_id="safe"))
    assert state["ok"] is True


def test_only_listeners_for_specific_event_fire() -> None:
    received = []

    @event_bus.subscribe(SearchExecuted)
    async def searcher(event: SearchExecuted) -> None:
        received.append("search")

    event_bus.publish(DocumentIndexed(document_id="no"))
    assert received == []


def test_clear_listeners() -> None:
    @event_bus.subscribe(DocumentIndexed)
    async def listener(event: DocumentIndexed) -> None:
        pass

    event_bus.clear()
    event_bus.publish(DocumentIndexed(document_id="solo"))
