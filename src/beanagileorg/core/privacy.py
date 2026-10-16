"""Privacy levels. Every field is tagged; reads are filtered on the server by the viewer's floor.

A viewer with floor PRIVATE sees everything. Presentation mode raises the floor to PRESENTABLE,
and exports or export-only tokens raise it to EXPORTABLE. Untagged fields default to PRIVATE.
"""

from dataclasses import dataclass, field
from enum import IntEnum


class Level(IntEnum):
    PRIVATE = 0
    PRESENTABLE = 1
    EXPORTABLE = 2


# Fields every record exposes at any level, so records can still be linked and counted.
ALWAYS_VISIBLE = frozenset({"id"})
# A record can carry this column to be more private than its fields' tags, never less.
RECORD_CEILING = "privacy_ceiling"

_registry: dict[str, dict[str, Level]] = {}


def register(entity: str, fields: dict[str, Level]) -> None:
    _registry[entity] = {name: Level(level) for name, level in fields.items()}


def field_level(entity: str, name: str) -> Level:
    if name in ALWAYS_VISIBLE:
        return Level.EXPORTABLE
    return _registry.get(entity, {}).get(name, Level.PRIVATE)


def filter_record(entity: str, record: dict, floor: Level) -> dict | None:
    """Return the fields visible at `floor`, or None when the whole record is too private to show."""
    if floor == Level.PRIVATE:
        return dict(record)
    ceiling = Level(record.get(RECORD_CEILING, Level.EXPORTABLE))
    if ceiling < floor:
        return None
    return {
        name: value
        for name, value in record.items()
        if name != RECORD_CEILING and min(field_level(entity, name), ceiling) >= floor
    }


def filter_records(entity: str, records: list[dict], floor: Level) -> list[dict]:
    return [r for r in (filter_record(entity, rec, floor) for rec in records) if r is not None]


# Read floor implied by each token scope. Apps can register more (for example a write scope).
SCOPE_FLOORS: dict[str, Level] = {
    "full": Level.PRIVATE,
    "present:read": Level.PRESENTABLE,
    "export:read": Level.EXPORTABLE,
}


def register_scope(scope: str, read_floor: Level) -> None:
    SCOPE_FLOORS[scope] = Level(read_floor)


@dataclass(frozen=True)
class Viewer:
    floor: Level
    source: str
    scopes: frozenset = field(default_factory=frozenset)
    session_hash: str | None = None
    presentation: bool = False

    @property
    def is_session(self) -> bool:
        return self.session_hash is not None

    def has_scope(self, scope: str) -> bool:
        return "full" in self.scopes or scope in self.scopes


def floor_for_scopes(scopes: list[str] | frozenset) -> Level:
    floors = [SCOPE_FLOORS[s] for s in scopes if s in SCOPE_FLOORS]
    return min(floors) if floors else Level.EXPORTABLE
