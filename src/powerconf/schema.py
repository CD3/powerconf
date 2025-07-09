from typing import Annotated, List

import numpy
from pydantic import (AfterValidator, AliasChoices, BaseModel, Field,
                      PlainSerializer, WithJsonSchema)

from .units import make_quantity

QuantityWithUnit = lambda U, names=None, desc=None: Annotated[
    str,
    AfterValidator(lambda x: make_quantity(x).to(U)),
    PlainSerializer(lambda x: f"{x:~}" if x is not None else "null", return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
    Field(
        alias=(
            AliasChoices(*names if type(names) is list else names)
            if names is not None
            else None
        ),
        description=desc,
    ),
]
