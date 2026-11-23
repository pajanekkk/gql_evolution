"""
Testy domény Personalities2 (Contact, ContactType, Employment, EmploymentType).

Běží nad vlastní SQLite v paměti se zapnutými cizími klíči, takže nepotřebují
Docker a nezapisují do žádné sdílené databáze.
"""

from __future__ import annotations

import collections
import datetime
import json
import pathlib
import types
import uuid

import pytest
import pytest_asyncio
import sqlalchemy
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import StaticPool

from src.Dataloaders import LoaderMap
from src.DBDefinitions import (
    BaseDBModel,
    ContactModel,
    ContactTypeModel,
    EmploymentModel,
    EmploymentTypeModel,
)
from src.DBDefinitions.main import CliError, coerce_column_value
from src.DBDefinitions.seed import init_database_data
from src.GraphTypeDefinitions.GraphQLContext import GraphQLContext
from src.GraphTypeDefinitions.SessionCommitExtension import SessionCommitExtension
from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from src.ServiceDefinitions.ServiceContext import ServiceContext

SYSTEMDATA = pathlib.Path(__file__).resolve().parents[2] / "systemdata.json"

SERVICE_CASES = [
    ("ContactService", ContactModel, {"value": "test@example.com"}, "value", "novy@example.com"),
    ("ContactTypeService", ContactTypeModel, {"name": "Test typ"}, "name", "Novy typ"),
    (
        "EmploymentService",
        EmploymentModel,
        {"employer_name": "Test s.r.o.", "started": datetime.datetime(2025, 1, 1)},
        "position",
        "Tester",
    ),
    ("EmploymentTypeService", EmploymentTypeModel, {"name": "Test typ"}, "name", "Novy typ"),
]
TYPE_MODELS = [ContactTypeModel, EmploymentTypeModel]


def enable_foreign_keys(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest_asyncio.fixture
async def session_maker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    event.listen(engine.sync_engine, "connect", enable_foreign_keys)
    async with engine.begin() as connection:
        await connection.run_sync(BaseDBModel.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def service_ctx(session) -> ServiceContext:
    return ServiceContext(loaders=LoaderMap(session), session=session)


def load_systemdata() -> dict:
    return json.loads(SYSTEMDATA.read_text(encoding="utf-8"))


async def count_rows(session, model) -> int:
    return await session.scalar(select(func.count()).select_from(model))


def mutation_extension(session_maker) -> tuple[SessionCommitExtension, GraphQLContext]:
    context = GraphQLContext(
        session_maker_factory=lambda: session_maker,
        loaders_factory=LoaderMap,
    )
    extension = SessionCommitExtension()
    extension.execution_context = types.SimpleNamespace(
        context=context,
        operation=types.SimpleNamespace(operation=types.SimpleNamespace(value="mutation")),
    )
    return extension, context


@pytest.mark.asyncio
@pytest.mark.parametrize("service_name, model, _attrs, _field, _value", SERVICE_CASES)
async def test_service_is_registered_with_matching_loader(session_maker, service_name, model, _attrs, _field, _value):
    async with session_maker() as session:
        ctx = service_ctx(session)
        service = getattr(ctx.Services, service_name)

        loader = await service.getLoader(ctx)

        assert loader is getattr(ctx.loaders, model.__name__)
        assert loader.getModel() is model


@pytest.mark.asyncio
@pytest.mark.parametrize("service_name, model, attrs, field, new_value", SERVICE_CASES)
async def test_service_crud_cycle(session_maker, service_name, model, attrs, field, new_value):
    entity_id = uuid.uuid4()

    async with session_maker() as session:
        ctx = service_ctx(session)
        service = getattr(ctx.Services, service_name)
        created = await service.Create(ctx=ctx, entity=model(id=entity_id, **attrs))
        lastchange = created.lastchange
        await session.commit()

    async with session_maker() as session:
        ctx = service_ctx(session)
        service = getattr(ctx.Services, service_name)
        loaded = await service.ReadById(ctx=ctx, id=entity_id)
        page = await service.ReadPage(ctx=ctx, limit=100)
        assert loaded.id == entity_id
        assert entity_id in {row.id for row in page}

        updated = await service.Update(
            ctx=ctx,
            entity=model(id=entity_id, lastchange=lastchange, **{field: new_value}),
        )
        assert getattr(updated, field) == new_value
        assert updated.lastchange != lastchange
        await session.commit()

    async with session_maker() as session:
        ctx = service_ctx(session)
        service = getattr(ctx.Services, service_name)
        await service.Delete(ctx=ctx, entity=types.SimpleNamespace(id=entity_id))
        await session.commit()

    async with session_maker() as session:
        assert await session.get(model, entity_id) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("service_name, model, attrs, field, new_value", SERVICE_CASES)
async def test_update_with_stale_lastchange_is_rejected(session_maker, service_name, model, attrs, field, new_value):
    entity_id = uuid.uuid4()

    async with session_maker() as session:
        ctx = service_ctx(session)
        service = getattr(ctx.Services, service_name)
        created = await service.Create(ctx=ctx, entity=model(id=entity_id, **attrs))
        original = getattr(created, field)
        stale = created.lastchange - datetime.timedelta(days=1)
        await session.commit()

    async with session_maker() as session:
        ctx = service_ctx(session)
        service = getattr(ctx.Services, service_name)
        result = await service.Update(
            ctx=ctx,
            entity=model(id=entity_id, lastchange=stale, **{field: new_value}),
        )
        await session.commit()

        assert result is None

    async with session_maker() as session:
        row = await session.get(model, entity_id)
        assert getattr(row, field) == original


@pytest.mark.asyncio
@pytest.mark.parametrize("model", TYPE_MODELS)
async def test_type_catalog_is_a_tree(session_maker, model):
    root_id, child_id, leaf_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    async with session_maker() as session:
        session.add(model(id=root_id, name="koren", path=str(root_id)))
        await session.flush()
        session.add(model(id=child_id, name="uzel", parent_id=root_id, path=f"{root_id}/{child_id}"))
        await session.flush()
        session.add(
            model(id=leaf_id, name="list", parent_id=child_id, path=f"{root_id}/{child_id}/{leaf_id}")
        )
        await session.commit()

    async with session_maker() as session:
        rows = await session.scalars(
            select(model)
            .where(model.id.in_([root_id, child_id]))
            .options(selectinload(model.children), selectinload(model.parent))
        )
        by_id = {row.id: row for row in rows}

        assert by_id[root_id].parent is None
        assert [row.id for row in by_id[root_id].children] == [child_id]
        assert by_id[child_id].parent.id == root_id
        assert [row.id for row in by_id[child_id].children] == [leaf_id]

        subtree = await session.scalars(select(model.id).where(model.path.like(f"{root_id}/%")))
        assert set(subtree) == {child_id, leaf_id}


@pytest.mark.asyncio
@pytest.mark.parametrize("model", TYPE_MODELS)
async def test_type_catalog_rejects_unknown_parent(session_maker, model):
    async with session_maker() as session:
        session.add(model(name="sirotek", parent_id=uuid.uuid4()))
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await session.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model, foreign_key",
    [(ContactModel, "contact_type_id"), (EmploymentModel, "employment_type_id")],
)
async def test_entity_rejects_unknown_type(session_maker, model, foreign_key):
    async with session_maker() as session:
        session.add(model(**{foreign_key: uuid.uuid4()}))
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_successful_mutation_is_committed(session_maker):
    entity_id = uuid.uuid4()
    extension, context = mutation_extension(session_maker)

    operation = extension.on_operation()
    await operation.__anext__()
    ctx = context["ServiceCtx"]
    service = ctx.Services.ContactService
    await service.ExecuteServiceMethod(
        service.Create(ctx=ctx, entity=ContactModel(id=entity_id, value="ulozeno")),
        Error=lambda msg, code: {"msg": msg, "code": code},
    )
    with pytest.raises(StopAsyncIteration):
        await operation.__anext__()

    async with session_maker() as session:
        assert (await session.get(ContactModel, entity_id)).value == "ulozeno"


@pytest.mark.asyncio
async def test_failed_service_operation_rolls_back_partial_write(session_maker):
    entity_id = uuid.uuid4()
    extension, context = mutation_extension(session_maker)

    operation = extension.on_operation()
    await operation.__anext__()
    ctx = context["ServiceCtx"]
    service = ctx.Services.EmploymentService

    async def write_then_fail():
        await service.Create(ctx=ctx, entity=EmploymentModel(id=entity_id, employer_name="prvni krok"))
        raise ServiceExceptionWithCode("druhy krok selhal", code="pytest-partial-write")

    result = await service.ExecuteServiceMethod(
        write_then_fail(),
        Error=lambda msg, code: {"msg": msg, "code": code},
    )
    with pytest.raises(StopAsyncIteration):
        await operation.__anext__()

    assert result["code"] == "pytest-partial-write"
    async with session_maker() as session:
        assert await session.get(EmploymentModel, entity_id) is None


@pytest.mark.asyncio
async def test_seed_imports_demo_data_once(session_maker, monkeypatch):
    monkeypatch.setenv("DEMODATA", "True")
    data = load_systemdata()

    async with session_maker() as session:
        await init_database_data(session)
        await init_database_data(session)

        for model in (ContactTypeModel, EmploymentTypeModel, ContactModel, EmploymentModel):
            assert await count_rows(session, model) == len(data[model.__tablename__])

        started = await session.scalar(select(EmploymentModel.started).where(EmploymentModel.started.is_not(None)))
        assert isinstance(started, datetime.datetime)


@pytest.mark.asyncio
async def test_seed_without_demodata_imports_only_catalogs(session_maker, monkeypatch):
    monkeypatch.delenv("DEMODATA", raising=False)
    data = load_systemdata()

    async with session_maker() as session:
        await init_database_data(session)

        assert await count_rows(session, ContactTypeModel) == len(data["contacttypes"])
        assert await count_rows(session, EmploymentTypeModel) == len(data["employmenttypes"])
        assert await count_rows(session, ContactModel) == 0
        assert await count_rows(session, EmploymentModel) == 0


@pytest.mark.parametrize("table", ["contacttypes", "employmenttypes"])
def test_demo_type_paths_match_parent_chain(table):
    rows = {row["id"]: row for row in load_systemdata()[table]}

    for row in rows.values():
        chain = [row["id"]]
        while (parent_id := rows[chain[0]].get("parent_id")) is not None:
            chain.insert(0, parent_id)
        assert row["path"] == "/".join(chain)


@pytest.mark.parametrize(
    "table, type_table, foreign_key",
    [("contacts", "contacttypes", "contact_type_id"), ("employments", "employmenttypes", "employment_type_id")],
)
def test_demo_rows_reference_leaf_types_and_own_rbac(table, type_table, foreign_key):
    data = load_systemdata()
    type_ids = {row["id"] for row in data[type_table]}
    parent_ids = {row.get("parent_id") for row in data[type_table]}

    assert len({row["id"] for row in data[table]}) == len(data[table])
    for row in data[table]:
        assert row[foreign_key] in type_ids
        assert row[foreign_key] not in parent_ids
        assert row["rbacobject_id"] == row["user_id"]


def test_demo_users_have_exactly_one_preferred_contact():
    preferred = collections.Counter()
    contacts = load_systemdata()["contacts"]
    for row in contacts:
        preferred[row["user_id"]] += 1 if row["preferred"] else 0

    assert set(preferred) == {row["user_id"] for row in contacts}
    assert set(preferred.values()) == {1}


def test_demo_employment_does_not_finish_before_start():
    for row in load_systemdata()["employments"]:
        if row.get("finished"):
            assert row["started"] <= row["finished"]


def test_coerce_column_value_converts_by_column_type():
    entity_id = uuid.uuid4()

    assert coerce_column_value(EmploymentModel, "started", "2025-01-02") == datetime.datetime(2025, 1, 2)
    assert coerce_column_value(EmploymentModel, "started", "2025-01-02T03:04:05+01:00") == datetime.datetime(2025, 1, 2, 3, 4, 5)
    assert coerce_column_value(ContactModel, "user_id", str(entity_id)) == entity_id
    assert coerce_column_value(ContactModel, "value", "text") == "text"
    assert coerce_column_value(ContactModel, "preferred", True) is True
    assert coerce_column_value(ContactModel, "user_id", None) is None


@pytest.mark.parametrize("field, value", [("started", "nesmysl"), ("user_id", "neni-uuid")])
def test_coerce_column_value_reports_invalid_value(field, value):
    with pytest.raises(CliError, match=field):
        coerce_column_value(EmploymentModel, field, value)
