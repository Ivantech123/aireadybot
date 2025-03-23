import logging
from functools import wraps
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from database.db import get_session

logger = logging.getLogger(__name__)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()

def with_session(func):
    """Decorator to handle session management for handler functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with session_scope() as session:
            return await func(*args, session=session, **kwargs)
    return wrapper
