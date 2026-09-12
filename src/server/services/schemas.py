from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CurrencyCode(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class SpecificationItem(BaseModel):
    name: str
    count: int

    link: HttpUrl | None = None
    tags: list[str]

    price: Annotated[Decimal, Field(ge=Decimal(0))]
    price_currency: CurrencyCode

    model_config = ConfigDict(use_enum_values=True)
