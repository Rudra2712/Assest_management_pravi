from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


def paginate(items: list, total: int, page: int, page_size: int) -> dict:
    pages = (total + page_size - 1) // page_size if page_size else 0
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}
