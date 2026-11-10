from typing import TYPE_CHECKING

from server.domain.projects.schemas import Item, ItemPure

from .schemas import Group, GroupPure, Project, ProjectPure

if TYPE_CHECKING:
    from pydantic import AwareDatetime

# ========================
# Aggregate Root: Projects
# ========================


class AdminProjectPure(ProjectPure):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AdminProject(AdminProjectPure, Project):
    pass


# ==========================
# Intermediate entity: Group
# ==========================


class AdminGroupPure(GroupPure):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AdminGroup(AdminGroupPure, Group):
    pass


# ===============
# Tree leaf: Item
# ===============


class AdminItemPure(ItemPure):
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AdminItem(AdminItemPure, Item):
    pass
