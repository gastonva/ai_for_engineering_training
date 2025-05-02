"""
The idea of the BaseRepository is simply to abstract the CRUD operations,
thus allowing to respect the same flow for all other repositories.

Q: Why not use the ABC module?
A: Because there would be many decorators and the messages they return are not so explicit.
"""

import os
from abc import abstractmethod
from functools import wraps
from typing import Any, Callable, Literal, Optional, cast, no_type_check

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.schemas.types import Model, ModelType


# region Decorators
@no_type_check
def model_required(method: classmethod) -> Any:
    """Check if model is assigned in the inheritance"""

    @wraps(method)
    def wrapper(self=None, *args: Any, **kwargs: Any) -> Any:
        if self is None:
            raise TypeError(f"The '{method.__name__}' is not a class method")
        if not isinstance(self.model, type(Model)):
            raise ValueError(f"The '{self.__name__}' unassigned model's instance")
        return method(self, *args, **kwargs)

    return wrapper


@no_type_check
def only_tests(method_or_func: classmethod | staticmethod | Callable[..., Any]) -> Any:
    """Limits its use, it can only be used in test environments."""

    @wraps(method_or_func)
    def wrapper(self=None, *args: Any, **kwargs: Any) -> Any:
        if str(os.environ.get("PYTEST_RUNNING")).lower() != "true":
            raise NotImplementedError(
                "You cannot use this method outside test environment"
            )
        if self:
            return method_or_func(self, *args, **kwargs)
        return method_or_func(*args, **kwargs)

    return wrapper


# endregion


class ModelRepository:
    model: Any = cast(Model, None)
    field_not_found: Exception = None
    already_exists_error: Exception = None

    def __init__(self, session: Session):
        self.session = session

    @model_required
    def create(self, **kwargs: dict) -> ModelType:
        """
        Creates a model instance in the database.
        """
        instance = self.model(**kwargs)
        return self.save(instance)

    @model_required
    def save(self, instance: ModelType) -> ModelType:
        """
        Saves a model instance in the database.
        IMPORTANT: This method may be overridden.

        :param instance: Model instance
        :returns: an instance of the model
        """
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    @model_required
    def get(self, pk: int | str) -> Optional[ModelType]:
        """
        Gets a record by its primary key or None if it does not exist.

        :param pk: record's primary key.
        :return: an instance of model or None, example: <ModelType 1> | None
        """
        return self.session.query(self.model).get(pk)

    @model_required
    def get_many(self, ids: list[int]) -> list[ModelType]:
        """
        Gets records by their primary keys or None if they do not exist.

        :param ids: List of record's primary key.
        :return: a list of instances of model, example: List[<ModelType 1>]
        """
        return self.session.query(self.model).filter(self.model.id.in_(ids)).all()

    @model_required
    def get_all(self) -> list[ModelType]:
        """
        Gets all records from the table.

        :return: a list of models, example = ["<ModelType 1>", "<ModelType 2>", ...]
        """
        return self.session.query(self.model).all()  # noqa

    def __update(self, instance: ModelType, **new_values: Any) -> ModelType:
        for attribute, new_value in new_values.items():
            setattr(instance, attribute, new_value)

        return self.save(instance)

    @model_required
    def update(self, pk: int | str, **kwargs: Any) -> Optional[ModelType]:
        """
        Updates a record by its primary key.

        :param pk: record's primary key
        :param kwargs: new values for the record
        :return: The updated record as model
        """
        instance = self.get(pk)
        return self.update_instance(instance, **kwargs) if instance else None

    @model_required
    def update_instance(self, instance: ModelType, **kwargs: Any) -> ModelType:
        """
        Updates a record by its instance.

        :param instance: ModelType instance
        :param kwargs:  the new values of record
        :return: The updated model
        """
        return self.__update(instance, **kwargs)

    @model_required
    def delete(self, pk: str | int) -> ModelType | None:
        """
        Deletes a record by its primary key.

        :param pk: record's primary key.
        :returns: a deleted instance.
        """
        instance = self.get(pk)
        if instance:
            return self.delete_instance(instance)
        return None

    @model_required
    def delete_instance(self, instance: ModelType) -> ModelType:
        """
        Deletes a record by its instance.

        :param instance: ModelType instance
        :returns: the deleted instance
        """
        self.session.delete(instance)
        self.session.commit()
        return instance

    @model_required
    def bulk_insert(self, list_instances: list[ModelType]) -> bool:
        """
        Inserts a list of instances in the database.

        :param list_instances: A list of instances to be inserted
        :returns: True if the operation is completed, False if an error generated.
        """
        try:
            self.session.bulk_save_objects(list_instances)
            self.session.commit()
            return True
        except SQLAlchemyError:
            return False

    @model_required
    def count(self) -> int:
        """
        Counts the number of rows in the table.

        Returns: returns the total number of rows in the table
        """
        return self.session.query(self.model).count()

    @model_required
    def filter_count(self, filters: list) -> int:
        """
        Counts the number of rows in the table given a filter

        Returns: returns the total number of rows in the table that complains with the filter
        """
        return self.session.query(self.model).filter(*filters).count()

    @model_required
    def filter(
        self, filters: list, first_only: bool = False
    ) -> list[ModelType] | ModelType | None:
        """Filters based on given params and returns a list of instances

        Args:
            filters: list of filters
            first_only: if True, returns only the first instance or None

        Returns: instance, list of instances or None
        """
        if not filters:
            return None

        query = self.session.query(self.model).filter(*filters)
        return query.first() if first_only else query.all()

    @model_required
    def paginate(
        self,
        filters: list | None = None,
        page: int | None = 1,
        page_size: int | None = 10,
        sort_field: str | None = None,
        sort: Literal["ASC", "DESC"] = "ASC",
    ) -> list[ModelType]:
        """Gets records from the table that matches the filters.

        Args:
            filters: a list of query filters to be applied
            page: page number
            page_size: number of records per page
            sort_field: field to be used for sorting
            sort: sorting order (ASC or DESC)

        Returns: a list of models
        """

        # check if the sort field exists for the used model
        if sort_field and not hasattr(self.model, sort_field):
            raise self.field_not_found

        query = self.session.query(self.model)

        if filters:
            query = query.filter(*filters)

        if order_column := getattr(self.model, sort_field if sort_field else "", None):
            query = query.order_by(
                order_column if sort == "ASC" else order_column.desc()
            )

        offset = self._calc_offset(page, page_size)
        return query.limit(page_size).offset(offset).all()

    @model_required
    def already_exists(self, pk: int | None = None, **kwargs: dict) -> bool:
        """
        Determines whether there are rows in DB for the specified filters or not.

        If pk is provided, it checks if the there are rows different than the specified pk
        for the specified filters.

        Returns: True if at least 1 row exists, False otherwise.
        """
        query = self.session.query(self.model).filter_by(**kwargs)
        if pk:
            query = query.filter(self.model.id != pk)

        return self.session.query(query.exists()).scalar()

    @abstractmethod
    def build_filters(self, params: dict) -> list:
        """Overridden by child class"""
        pass

    @staticmethod
    def _calc_offset(page: int, page_size: int) -> int:
        """Calcules offset given a page and page_size"""
        if page < 1 or page_size < 1:
            raise ValueError("Page and page_size must be greater than 0")
        return page_size * (page - 1)
