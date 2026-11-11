from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from server.domain.projects.schemas import (
    GroupBase,
    ItemBase,
    ItemStatus,
    MoneyType,
)

from .schemas import (
    Group,
    GroupPure,
    Item,
    ItemPure,
    Project,
    ProjectBase,
    ProjectPure,
)

if TYPE_CHECKING:
    from pydantic import AwareDatetime

# ========================
# Aggregate Root: Projects
# ========================


class ProjectCreate(ProjectBase):
    """Модель для создания спецификации."""


class ProjectPut(ProjectBase):
    """Модель для полной замены объекта спецификации."""


class ProjectUpdate(BaseModel):
    """Модель для частичного обновления объекта спецификации."""

    name: Annotated[str, Field(min_length=1, max_length=256)] = ""

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class AdminProjectPure(ProjectPure):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AdminProject(AdminProjectPure, Project):
    pass


# ==========================
# Intermediate entity: Group
# ==========================


class GroupCreate(GroupBase):
    """Модель для создания новой группы."""


class GroupPut(GroupBase):
    """Модель для полного обновления группы."""


class AdminGroupPure(GroupPure):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AdminGroup(AdminGroupPure, Group):
    pass


# ===============
# Tree leaf: Item
# ===============


class ItemCreate(ItemBase):
    """Модель для создания карточки."""


class ItemPut(ItemBase):
    """Модель для полного обновления карточки."""


class ItemUpdate(BaseModel):
    """Модель для частичного обновления карточки."""

    name: Annotated[str, Field(min_length=1, max_length=1024)] = "*"
    count: int = Field(default=1, ge=1, le=256)
    price: MoneyType | None = None

    link: HttpUrl | None = None
    tags: list[str] = Field(default_factory=list[str], max_length=16)

    status: ItemStatus | None = None

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class AdminItemPure(ItemPure):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AdminItem(AdminItemPure, Item):
    pass
