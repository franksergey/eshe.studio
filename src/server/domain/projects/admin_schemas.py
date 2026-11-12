from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from server.domain.projects.schemas import (
    GroupBase,
    GroupID,
    ItemBase,
    ProjectID,
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
    """Модель для создания проекта."""


class ProjectPut(ProjectBase):
    """Модель для полной замены объекта проекта."""


class ProjectUpdate(BaseModel):
    """Модель для частичного обновления объекта проекта."""

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

    project_id: ProjectID

    group_id: GroupID | None = None


class GroupPut(GroupCreate):
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

    group_id: int


class ItemPut(ItemCreate):
    """Модель для полного обновления карточки."""


class AdminItemPure(ItemPure):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AdminItem(AdminItemPure, Item):
    pass
