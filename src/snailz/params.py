"""Represent snailz parameters."""


from pydantic import BaseModel, Field

from .grids import GridParams, GridList
from .persons import PersonParams, PersonList


class AllParams(BaseModel):
    """Represent all parameters combined."""

    seed: int = Field(default=7493418, ge=0, description="RNG seed")
    grid: GridParams = Field(
        default=GridParams(), description="parameters for grid generation"
    )
    person: PersonParams = Field(
        default=PersonParams(), description="parameters for people generation"
    )

    model_config = {"extra": "forbid"}


class AllData(BaseModel):
    """Represent all generated data combined."""

    params: AllParams = Field(description="all parameters")
    persons: PersonList = Field(description="all persons")
    grids: GridList = Field(description="all grids")

    model_config = {"extra": "forbid"}
