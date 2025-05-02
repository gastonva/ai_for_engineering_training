from typing import Any, Dict

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.settings.settings import settings


class SingletonDB:
    _session_instance: sessionmaker[Session] | None = None
    _session_ro_instance: sessionmaker[Session] | None = None

    default_engine_params: Dict = {}

    @staticmethod
    def get_conn_str() -> str:
        db_connection = settings.DBConnection
        if not db_connection:
            raise ValueError("Invalid DB connection settings")

        return db_connection

    @classmethod
    def get_engine(cls, **kwargs: Any) -> Engine:
        return create_engine(cls.get_conn_str(), **(cls.default_engine_params | kwargs))

    @classmethod
    def get_db(cls) -> sessionmaker[Session]:
        if cls._session_instance:
            return cls._session_instance

        engine = cls.get_engine()
        cls._session_instance = sessionmaker(
            bind=engine, class_=Session, expire_on_commit=False
        )
        return cls._session_instance

    @classmethod
    def get_ro_db(cls) -> sessionmaker[Session]:
        if cls._session_ro_instance:
            return cls._session_ro_instance

        engine = cls.get_engine(isolation_level="READ UNCOMMITTED")
        cls._session_ro_instance = sessionmaker(
            bind=engine, class_=Session, expire_on_commit=False
        )
        return cls._session_ro_instance
