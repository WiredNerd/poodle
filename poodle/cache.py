import logging
import os
from functools import wraps

from pony.orm import (Database, PrimaryKey, Required, Optional, Set, composite_index, OperationalError, db_session)

logger = logging.Logger(__name__)

db_filename = os.path.join(os.getcwd(), '.poodle-cache')
db = Database()


class TestCase(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    call_duration = Optional(float)
    setup_duration = Optional(float)
    teardown_duration = Optional(float)
    lines = Set('FileLine')


class FileLine(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    line_number = Required(int)
    composite_index(name, line_number)
    test_cases = Set(TestCase)


def init_db(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not db.provider:
            db.bind(provider='sqlite', filename=db_filename, create_db=True)

            try:
                db.generate_mapping(create_tables=True)
            except OperationalError as oe:
                logger.warning(oe)
                pass

        return f(*args, **kwargs)

    return wrapper


@init_db
@db_session
def get_schema():
    return db.schema


print(get_schema())

# db.generate_mapping(create_tables=True)
