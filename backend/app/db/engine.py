from sqlalchemy import Engine, create_engine

# Fly.io and Supabase share a region, so a live server acknowledges what the API sends within
# milliseconds. A connection that stays silent this long is dead, not slow.
DEAD_CONNECTION_TIMEOUT_MS = 3_000


def create_database_engine(database_url: str) -> Engine:
    """The API's engine. It keeps a pool of connections and reuses them across requests.

    Before reusing a connection, the pool checks that it still works (pre-ping) and replaces it if
    not. A connection can die without the server ever answering, when a network drops it or the
    machine is suspended or moved. `tcp_user_timeout` makes the operating system give up on it
    after a few seconds instead of retrying for about 15 minutes. The pool then also replaces
    every connection opened before it, so later requests don't wait.
    """
    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"tcp_user_timeout": DEAD_CONNECTION_TIMEOUT_MS},
    )
