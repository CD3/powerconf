from typing import Annotated

from pydantic import (AfterValidator, AliasChoices, Field,
                      PlainSerializer, WithJsonSchema)

from .units import make_quantity

def QuantityWithUnit(U, names=None, desc=None):
    return Annotated[
        str,
        AfterValidator(lambda x: make_quantity(x).to(U)),
        PlainSerializer(lambda x: f"{x:~}" if x is not None else "null", return_type=str),
        WithJsonSchema({"type": "string"}, mode="serialization"),
        Field(
            alias=(
                AliasChoices(*names if isinstance(names, list) else [names])
                if names is not None
                else None
            ),
            description=desc,
        ),
    ]
