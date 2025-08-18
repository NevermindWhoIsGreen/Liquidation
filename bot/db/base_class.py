from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def __repr__(self):
        cls_name = self.__class__.__name__
        obj_id = self.__dict__.get("id")
        if obj_id:
            return f"<{cls_name}: ({cls_name} object ({obj_id})>"
        return super().__repr__()

    def __model_name__(self):
        return self.__class__.__name__


metadata = Base.metadata
