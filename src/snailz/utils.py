"""Snailz utilities."""

import csv
from datetime import date
import io
import json
import math
import sys
from typing import Callable, Generator

from pydantic import BaseModel


# Floating point precision.
PRECISION = 2

# Maximum tries to generate a unique ID.
UNIQUE_ID_LIMIT = 10_000

# Default survey grid size.
DEFAULT_SURVEY_SIZE = 15

# File paths
ASSAYS_CSV = "assays.csv"
ASSAYS_DIR = "assays"
PERSONS_CSV = "persons.csv"
SPECIMENS_CSV = "specimens.csv"
SURVEYS_DIR = "surveys"


def fail(msg: str) -> None:
    """Report failure and exit.

    Parameters:
        msg: Error message to display
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def json_dump(obj: BaseModel) -> str:
    """Dump as JSON with appropriate settings."""
    return json.dumps(obj, indent=2, default=_serialize_json)


def report(verbose: bool, msg: str) -> None:
    """Report if verbosity turned on.

    Parameters:
        verbose: Is display on or off?
        msg: Message to display
    """
    if verbose:
        print(msg)


def sigmoid(x: float) -> float:
    """Calculate sigmoid curve value for x in 0..1.

    Sigmoid parameters are chosen so that s(0)=0, s(0.5)=0.5, and s(1)=1.

    Parameters:
        x: input value

    Returns:
        Sigmoid curve value.
    """
    a = 16.0
    b = 0.5
    c = -0.0002
    return 1 / (1 + math.exp(-a * (x - b))) + c


def to_csv(rows: list, fields: list, f_make_row: Callable) -> str:
    """Generic converter from list of models to CSV string.

    Parameters:
        rows: List of rows to convert.
        fields: List of names of columns.
        f_make_row: Function that converts a row to text.

    Returns:
        CSV representation of data.
    """

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(fields)
    for r in rows:
        writer.writerow(f_make_row(r))
    return output.getvalue()


def unique_id(
    name: str, func: Callable, limit: int = UNIQUE_ID_LIMIT
) -> Generator[str, tuple | None, None]:
    """Generate unique IDs.

    Parameters:
        name: name of this generator
        func: function to generate next candidate
        limit: how many tries per ID

    Returns:
        Unique ID.
    """
    gen = _make_unique_id_generator(name, func, limit)
    next(gen)  # prime the generator
    return gen


def _make_unique_id_generator(
    name: str, func: Callable, limit: int
) -> Generator[str, tuple | None, None]:
    """Create and prime a unique ID generator.

    Parameters:
        name: name of this generator
        func: function to generate next candidate
        limit: how many tries per ID

    Returns:
        Unique ID.
    """
    seen = set()
    provided = yield ""  # to prime the generator
    while True:
        found = False
        for _ in range(limit):
            if provided is None:
                provided = ()
            temp = func(*provided)
            assert isinstance(temp, str)
            if temp in seen:
                continue
            seen.add(temp)
            found = True
            break
        if not found:
            raise RuntimeError(f"{name} unable to find unique ID")
        provided = yield temp


def _serialize_json(obj: object) -> str | dict:
    """Custom JSON serializer for JSON conversion.

    Parameters:
        obj: The object to serialize

    Returns:
        String representation of date objects or dict for Pydantic models

    Raises:
        TypeError: If the object type is not supported for serialization
    """
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    raise TypeError(f"Type {type(obj)} not serializable")
