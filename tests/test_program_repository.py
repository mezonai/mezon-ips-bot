from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import database connection setup to register SQLite custom UDF functions (e.g. now())
import app.database.connect  # noqa: F401
from app.database.models.program import Program
from app.database.models.rwmodel import RWModel
from app.database.repositories.program import ProgramRepository


@pytest.fixture
async def program_repository():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(RWModel.metadata.create_all)

    repository = ProgramRepository(session_factory)
    try:
        yield repository
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_program_repository_create_and_get_by_code(
    program_repository,
):
    created = await program_repository.create_program(
        Program(
            program_code="PROJ-001",
            name="Project 1",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
    )

    fetched = await program_repository.get_program_by_code("PROJ-001")

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.start_date == date(2026, 1, 1)
    assert fetched.end_date == date(2026, 12, 31)


@pytest.mark.asyncio
async def test_program_repository_update_persists_start_date(program_repository):
    created = await program_repository.create_program(
        Program(
            program_code="PROJ-002",
            name="Project 2",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 10, 31),
        )
    )

    created.start_date = date(2026, 3, 1)
    updated = await program_repository.update_program(created)

    fetched = await program_repository.get_program_by_id(updated.id)

    assert fetched is not None
    assert fetched.start_date == date(2026, 3, 1)


@pytest.mark.asyncio
async def test_program_repository_delete_hides_program_from_queries(program_repository):
    created = await program_repository.create_program(
        Program(
            program_code="PROJ-003",
            name="Project 3",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
        )
    )

    deleted = await program_repository.delete_program(created.id)
    fetched = await program_repository.get_program_by_code("PROJ-003")
    programs = await program_repository.list_programs()

    assert deleted is True
    assert fetched is None
    assert all(program.id != created.id for program in programs)
