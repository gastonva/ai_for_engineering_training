from datetime import datetime, timezone

from humps import decamelize
from sqlalchemy import func, MetaData
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# meta = MetaData()


# @as_declarative(metadata=meta)
class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return decamelize(cls.__name__)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=datetime.now(timezone.utc)
    )
