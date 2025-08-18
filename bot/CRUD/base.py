from collections.abc import Iterable, Sequence

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

from sqlalchemy import select, func, delete
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.base_class import Base


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(
        self,
        db: AsyncSession,
        *,
        id: Any,
        options: Optional[list[Any]] = None,
    ) -> ModelType | None:
        return await db.get(self.model, id, options=options)

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        where_conditions: list[Any],
        join: Optional[list[Any]] = None,
        skip: int | None = 0,
        limit: int | None = 100,
        options: Optional[list[Any]] = None,
        order_by: Optional[list[ColumnElement[Any]]] = None,
    ) -> Sequence[ModelType]:
        stmt = select(self.model).where(*where_conditions).offset(skip).limit(limit)
        if join:
            for join_condition in join:
                stmt = stmt.join(*join_condition)
        if order_by:
            stmt = stmt.order_by(*order_by)
        if options:
            stmt = stmt.options(*options)
        result = await db.scalars(stmt)
        return result.all()

    async def count(self, db: AsyncSession, *, where_conditions: list[Any]) -> int:
        stmt = (
            select(func.count("*"))
            .where(
                *where_conditions,
            )
            .select_from(self.model)
        )
        result = await db.scalar(stmt)
        return result or 0

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType, commit: bool = True
    ) -> ModelType:
        db_obj = self.model(**obj_in.model_dump(context={"db": True}))
        db.add(db_obj)
        await (db.commit() if commit else db.flush())
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        refresh_attribute_names: Optional[Iterable[str]] = None,
        commit: bool = True,
    ) -> ModelType:
        for k, v in obj_in.model_dump(exclude_unset=True, context={"db": True}).items():
            if isinstance(v, dict):
                v = getattr(db_obj, k) | v
            setattr(db_obj, k, v)
        db.add(db_obj)
        await (db.commit() if commit else db.flush())
        await db.refresh(db_obj, attribute_names=refresh_attribute_names)
        return db_obj

    async def delete(
        self, db: AsyncSession, *, id: Any, commit: bool = True
    ) -> ModelType | None:
        db_obj = await db.get(self.model, id)
        await db.delete(db_obj)
        await (db.commit() if commit else db.flush())
        return db_obj

    async def delete_many(
        self, db: AsyncSession, *, ids: list[Any], commit: bool = True
    ) -> int:
        if not hasattr(self.model, "id"):
            raise AttributeError(
                f"Model {self.model.__name__} does not have an 'id' column"
            )

        stmt = delete(self.model).where(getattr(self.model, "id").in_(ids))
        result = await db.execute(stmt)
        await (db.commit() if commit else db.flush())
        return result.rowcount
