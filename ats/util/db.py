
import aiohttp.web
import aiopg
import contextlib
import textwrap

import psycopg2


# A dictcursor would break the current code.
# A namedtuple does not, but requires all the result
# columns to be named.

cursor_factory = psycopg2.extras.NamedTupleCursor


async def sql(dbhandle, command, *args, **kw):
    """
    Execute a SQL command, either in a transaction (passing a cursor)
    or by creating a new one (from request, dbpool or app)
    """
    if isinstance(dbhandle, aiopg.cursor.Cursor):
        # If cursor, we don't need a context manager
        # to create a new transaction
        manager = None
        cursor = dbhandle
    elif isinstance(dbhandle, aiohttp.web.Request):
        manager = await dbhandle.app.dbpool.cursor(cursor_factory=cursor_factory)
    elif isinstance(dbhandle, aiopg.pool.Pool):
        manager = await dbhandle.cursor(cursor_factory=cursor_factory)
    elif hasattr(dbhandle, 'dbpool'):
        manager = await dbhandle.dbpool.cursor(cursor_factory=cursor_factory)
    else:
        raise Exception('Unsupported dbhandle %s', dbhandle)

    with contextlib.ExitStack() as stack:
        if manager:
            cursor = stack.enter_context(manager)
        await cursor.execute(textwrap.dedent(command.strip()), *args, **kw)

        try:
            rows = []
            async for row in cursor:
                rows.append(row)
            return rows
        except psycopg2.ProgrammingError as exc:
            if exc.args[0] == 'no results to fetch':
                # a command with no return values (INSERT, etc.)
                return None
            raise


def asdicts(rows):
    """
    Converts list of named tuples to list of dicts.
    """
    return [row._asdict() for row in rows]
