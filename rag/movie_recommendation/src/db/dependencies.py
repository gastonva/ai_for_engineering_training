from typing import Generator

from fastapi import Depends, Request
from sqlalchemy import NullPool
from sqlalchemy.orm import Session, scoped_session

from src.core.auth_manager import AuthManager
from src.db.session import SingletonDB
from src.models.user import User

# Useful for serverless ms
SingletonDB.default_engine_params = {
    "poolclass": NullPool,
    "connect_args": {"connect_timeout": 10},
}


def get_session() -> Generator:
    sess = None
    try:
        sess = scoped_session(SingletonDB.get_db())
        yield sess
    finally:
        if sess:
            sess.close()


def get_ro_session() -> Generator:
    sess = None
    try:
        sess = scoped_session(SingletonDB.get_ro_db())
        # This is actually what makes this session RO.
        sess.flush = lambda: None  # type: ignore
        yield sess
    finally:
        if sess:
            sess.close()


def get_user(request: Request, session: Session = Depends(get_ro_session)) -> User:
    manager = AuthManager()
    return manager(request, session)
