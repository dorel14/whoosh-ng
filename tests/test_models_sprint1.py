from __future__ import annotations

import dataclasses
import datetime
import decimal
import enum

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from whoosh.fields import ID, KEYWORD, NUMERIC, STORED
from whoosh_modern.models import (
    AutoIndexer,
    ModelIndex,
    SearchField,
    SearchOptions,
    TypeMapper,
    register_dataclass_model,
    register_msgspec_model,
    register_pydantic_model,
    register_sqlalchemy_model,
    register_sqlmodel_model,
)


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclasses.dataclass
class Item:
    title: str
    price: float
    tags: list[str]
    created: datetime.datetime
    color: Color
    amount: decimal.Decimal
    data: bytes
    count: int | None = None


def test_typing_list_maps_to_keyword():
    idx = ModelIndex(Item)
    assert isinstance(idx.schema["tags"], KEYWORD)


def test_datetime_maps_to_datetime():
    idx = ModelIndex(Item)
    from whoosh.fields import DATETIME

    assert isinstance(idx.schema["created"], DATETIME)


def test_enum_maps_to_keyword():
    idx = ModelIndex(Item)
    assert isinstance(idx.schema["color"], KEYWORD)


def test_decimal_maps_to_numeric():
    idx = ModelIndex(Item)
    assert isinstance(idx.schema["amount"], NUMERIC)
    assert idx.schema["amount"].decimal_places == 2


def test_bytes_maps_to_keyword():
    idx = ModelIndex(Item)
    assert isinstance(idx.schema["data"], KEYWORD)


def test_optional_field():
    idx = ModelIndex(Item)
    assert "count" in idx.schema


def test_search_options_stored_analyzer():
    class Book:
        title: SearchField = SearchField(fulltext=True, stored=True, analyzer="Simple")

    idx = ModelIndex(Book)
    assert idx.schema["title"].stored is True
    assert idx.schema["title"].analyzer == "Simple"


def test_search_field_descriptor_overrides():
    class Book:
        title: SearchField = SearchField(fulltext=True, stored=True)

    idx = ModelIndex(Book)
    assert idx.schema["title"].stored is True


def test_type_mapper_registers_custom():
    def factory(opt):
        return KEYWORD(stored=opt.stored)

    TypeMapper.register(str, factory)
    opts = SearchOptions(stored=True)
    field = TypeMapper.map(str, opts)
    assert isinstance(field, KEYWORD)
    assert field.stored is True


def test_model_index_dataclass_document():
    item = Item(
        title="T",
        price=10.5,
        tags=["a"],
        created=datetime.datetime(2024, 1, 1),
        color=Color.RED,
        amount=decimal.Decimal("10"),
        data=b"abc",
    )
    idx = ModelIndex(Item)
    doc = idx.to_whoosh_document(item)
    assert doc == {
        "title": "T",
        "price": 10.5,
        "tags": ["a"],
        "created": datetime.datetime(2024, 1, 1),
        "color": "red",
        "amount": decimal.Decimal("10"),
        "data": "616263",
        "count": None,
    }


def test_auto_indexer_register_and_index():
    model_index = ModelIndex(Item)
    from whoosh.filedb.filestore import RamStorage

    storage = RamStorage()
    ix = storage.create_index(model_index.schema)

    auto = AutoIndexer(ix, on_error="log")
    auto.register(Item)

    item = Item(
        title="Hello",
        price=10.0,
        tags=[],
        created=datetime.datetime.now(),
        color=Color.RED,
        amount=decimal.Decimal("10"),
        data=b"abc",
    )
    auto.index(item)


def test_auto_indexer_error_skip():
    from whoosh.fields import Schema
    from whoosh.filedb.filestore import RamStorage

    storage = RamStorage()
    ix = storage.create_index(Schema(x=STORED))

    auto = AutoIndexer(ix, on_error="skip")
    bad_model = type("Bad", (), {"x": str})
    auto.register(bad_model)
    auto.index(bad_model())


def test_auto_indexer_error_raise():
    from whoosh.fields import Schema
    from whoosh.filedb.filestore import RamStorage

    storage = RamStorage()
    ix = storage.create_index(Schema(x=STORED))

    auto = AutoIndexer(ix, on_error="raise")

    class Bad:
        x = 0

        @property  # type: ignore[no-redef]
        def x(self):
            return 1 / 0

    auto.register(Bad)
    with pytest.raises(ZeroDivisionError):
        auto.index(Bad())


@pytest.mark.asyncio
async def test_auto_indexer_async():
    from whoosh.fields import Schema
    from whoosh.filedb.filestore import RamStorage

    storage = RamStorage()
    ix = storage.create_index(Schema(x=STORED, id=ID(stored=True, unique=True)))

    auto = AutoIndexer(ix)

    class D:
        id: str = "1"
        x: str = "y"

    auto.register(D)
    dummy = D()
    await auto.index_async(dummy)
    await auto.remove_async(dummy)


def test_dataclass_integration():
    @dataclasses.dataclass
    class Book:
        id: str
        title: str

    mi = register_dataclass_model(Book)
    assert "id" in mi.schema
    assert "title" in mi.schema


def test_pydantic_integration():
    try:
        from pydantic import BaseModel
    except ImportError:
        pytest.skip("pydantic not installed")

    class Book(BaseModel):
        id: str
        title: str

    mi = register_pydantic_model(Book)
    assert "id" in mi.schema
    assert "title" in mi.schema


def test_msgspec_integration():
    try:
        import msgspec
    except ImportError:
        pytest.skip("msgspec not installed")

    class Book(msgspec.Struct):
        id: str
        title: str

    mi = register_msgspec_model(Book)
    assert "id" in mi.schema
    assert "title" in mi.schema


def test_sqlalchemy_integration():
    engine = create_engine("sqlite:///:memory:")

    class Base(DeclarativeBase):
        __allow_unmapped__ = True

    class Book(Base):
        __tablename__ = "books"
        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str]

    Base.metadata.create_all(engine)

    mi = register_sqlalchemy_model(Book)
    assert "id" in mi.schema
    assert "title" in mi.schema


def test_sqlmodel_integration():
    try:
        from sqlmodel import Field, SQLModel, create_engine
    except ImportError:
        pytest.skip("sqlmodel not installed")

    engine = create_engine("sqlite:///:memory:")

    class Book(SQLModel, table=True):
        id: int = Field(primary_key=True)
        title: str

    SQLModel.metadata.create_all(engine)

    mi = register_sqlmodel_model(Book)
    assert "id" in mi.schema
    assert "title" in mi.schema
