from sqlalchemy import create_engine, text

from app.db.database import engine


def test_a_connection_dropped_by_the_database_is_replaced_not_reused():
    # start from an empty pool, so the next checkout can only be the connection we drop
    engine.dispose()
    with engine.connect() as conn:
        pooled_pid = conn.scalar(text("SELECT pg_backend_pid()"))
    # the connection is back in the pool; now the database drops it, the way neon does
    # when it suspends after a few idle minutes
    admin = create_engine(engine.url)
    with admin.connect() as conn:
        conn.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pooled_pid})
    admin.dispose()

    with engine.connect() as conn:
        assert conn.scalar(text("SELECT 1")) == 1
        assert conn.scalar(text("SELECT pg_backend_pid()")) != pooled_pid
