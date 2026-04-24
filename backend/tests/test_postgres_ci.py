import os
import uuid

from sqlalchemy import text

from app.models.user import Base, User
from app.services.database_service import DatabaseService


def test_postgres_engine_and_basic_rw():
    database_url = os.getenv("DATABASE_URL", "")
    assert database_url.startswith("postgresql"), "DATABASE_URL must use PostgreSQL in this CI test"

    # Ensure fresh singleton state for this test process.
    DatabaseService._engine = None
    DatabaseService._session_local = None

    db_service = DatabaseService()
    engine = DatabaseService._engine
    assert engine is not None

    # Connectivity check.
    with db_service.get_session() as session:
        value = session.execute(text("SELECT 1")).scalar_one()
        assert value == 1

    # Minimal schema + read/write check on PostgreSQL.
    Base.metadata.create_all(bind=engine)
    user_id = "pg-ci-{}".format(uuid.uuid4().hex)
    email = "{}@example.com".format(user_id)

    with db_service.get_session() as session:
        session.add(User(id=user_id, email=email, display_name="PG CI User"))
        session.commit()

    with db_service.get_session() as session:
        found = session.query(User).filter(User.id == user_id).first()
        assert found is not None
        assert found.email == email

    engine.dispose()
