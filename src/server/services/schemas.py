from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CurrencyCode(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class MoneyType(BaseModel):
    amount: Annotated[Decimal | None, Field(ge=Decimal(0))]
    currency: CurrencyCode | None


class SpecificationItem(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=1024)]
    count: Annotated[int, Field(ge=1, le=256)]

    link: HttpUrl | None = None
    tags: Annotated[list[str], Field(max_length=16)]

    price: MoneyType | None

    model_config = ConfigDict(use_enum_values=True)
