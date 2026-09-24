"""Read one authored YAML realisation through the existing validation boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Never

import yaml
from yaml.events import (
    AliasEvent,
    DocumentStartEvent,
    MappingStartEvent,
    ScalarEvent,
    SequenceStartEvent,
)
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from caron.diagnostics import Diagnostic, Severity
from caron.entities import Entity, EntityRef, Property, PropertyValue
from caron.ontology import OntologySchema
from caron.realisations import (
    Coverage,
    CoverageStatus,
    RealisationCandidate,
    ValidatedRealisation,
)
from caron.relations import Qualifier, RelationAssertion
from caron.temporal import TemporalExtent, YearMonth
from caron.validation import Accepted, Rejected, validate_candidate


@dataclass(frozen=True, slots=True)
class SourceLocation:
    path: Path
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class LoadFinding:
    code: str
    layer: str
    message: str
    record_id: str | None = None
    field: str | None = None
    location: SourceLocation | None = None
    severity: Severity = Severity.ERROR


@dataclass(frozen=True, slots=True)
class LoadAccepted:
    realisation: ValidatedRealisation
    source_path: Path
    source_state_id: str


@dataclass(frozen=True, slots=True)
class LoadRejected:
    findings: tuple[LoadFinding, ...]
    source_path: Path
    source_state_id: str | None = None


type LoadResult = LoadAccepted | LoadRejected
type _NodePath = tuple[str | int, ...]
type _RecordPaths = dict[tuple[str, str], list[_NodePath]]


class _Failure(Exception):
    def __init__(self, finding: LoadFinding):
        self.finding = finding
        super().__init__(finding.message)


def _location(path: Path, mark: yaml.error.Mark) -> SourceLocation:
    return SourceLocation(path, mark.line + 1, mark.column + 1)


def _fail(
    code: str,
    layer: str,
    message: str,
    *,
    location: SourceLocation | None = None,
    record_id: str | None = None,
    field: str | None = None,
) -> Never:
    raise _Failure(LoadFinding(code, layer, message, record_id, field, location))


_INTEGER = re.compile(r"[+-]?(?:0|[1-9][0-9]*)\Z")
_FLOAT = re.compile(
    r"[+-]?(?:(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)\Z"
)
_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt \t]+[0-9]{1,2}:[0-9]{2}:[0-9]{2}.*)?\Z"
)


def _scalar(node: ScalarNode, path: Path) -> object:
    # BaseLoader leaves implicit scalars as text; apply only this profile's
    # small, stable grammar instead of YAML-version-dependent coercions.
    value = node.value
    if node.style is not None:
        return value
    if _TIMESTAMP.fullmatch(value) or value.lower() in {
        ".nan",
        "-.nan",
        "+.nan",
        ".inf",
        "-.inf",
        "+.inf",
    }:
        _fail(
            "codec.invalid_yaml",
            "codec",
            "Implicit timestamps and non-finite numbers are unsupported.",
            location=_location(path, node.start_mark),
        )
    if value == "true":
        return True
    if value == "false":
        return False
    if value in {"null", "~", ""}:
        return None
    if _INTEGER.fullmatch(value):
        return int(value)
    if _FLOAT.fullmatch(value):
        return float(value)
    return value


def _decode_node(
    node: Node,
    path: Path,
    node_path: _NodePath,
    locations: dict[_NodePath, SourceLocation],
) -> object:
    locations[node_path] = _location(path, node.start_mark)
    if isinstance(node, ScalarNode):
        return _scalar(node, path)
    if isinstance(node, SequenceNode):
        return [
            _decode_node(item, path, (*node_path, index), locations)
            for index, item in enumerate(node.value)
        ]
    if isinstance(node, MappingNode):
        result: dict[str, object] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode):
                _fail(
                    "codec.invalid_record_layout",
                    "codec",
                    "Mapping keys must be strings.",
                    location=_location(path, key_node.start_mark),
                )
            key = _scalar(key_node, path)
            if not isinstance(key, str) or key == "<<":
                _fail(
                    "codec.invalid_record_layout",
                    "codec",
                    "Mapping keys must be strings; merge keys are unsupported.",
                    location=_location(path, key_node.start_mark),
                )
            if key in result:
                _fail(
                    "codec.duplicate_mapping_key",
                    "codec",
                    f"Duplicate mapping key {key!r}.",
                    location=_location(path, key_node.start_mark),
                )
            result[key] = _decode_node(value_node, path, (*node_path, key), locations)
        return result
    _fail(
        "codec.invalid_yaml",
        "codec",
        "Unsupported YAML node.",
        location=_location(path, node.start_mark),
    )


def _decode_yaml(
    text: str, path: Path
) -> tuple[object, dict[_NodePath, SourceLocation]]:
    try:
        count = 0
        for event in yaml.parse(text, Loader=yaml.BaseLoader):
            if isinstance(event, DocumentStartEvent):
                count += 1
            if isinstance(event, AliasEvent) or (
                isinstance(event, ScalarEvent | SequenceStartEvent | MappingStartEvent)
                and (event.anchor is not None or event.tag is not None)
            ):
                _fail(
                    "codec.invalid_yaml",
                    "codec",
                    "YAML aliases, anchors, and explicit tags are unsupported.",
                    location=(
                        _location(path, event.start_mark)
                        if isinstance(event.start_mark, yaml.error.Mark)
                        else None
                    ),
                )
        if count != 1:
            _fail(
                "codec.invalid_yaml",
                "codec",
                "Expected exactly one YAML document.",
                location=SourceLocation(path, 1, 1),
            )
        node = yaml.compose(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        _fail(
            "codec.invalid_yaml",
            "codec",
            str(exc),
            location=_location(path, mark) if mark is not None else None,
        )
    if node is None:
        _fail(
            "codec.invalid_yaml",
            "codec",
            "Expected one nonempty YAML document.",
            location=SourceLocation(path, 1, 1),
        )
    locations: dict[_NodePath, SourceLocation] = {}
    return _decode_node(node, path, (), locations), locations


def _mapping(
    value: object,
    required: set[str],
    optional: set[str],
    at: _NodePath,
    locations: dict[_NodePath, SourceLocation],
) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        _fail(
            "codec.invalid_record_layout",
            "codec",
            "Expected a mapping with string keys.",
            location=locations.get(at),
        )
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing or extra:
        _fail(
            "codec.invalid_record_layout",
            "codec",
            f"Invalid mapping keys: missing {sorted(missing)}, extra {sorted(extra)}.",
            location=locations.get(at),
        )
    return value


def _string(
    value: object, at: _NodePath, locations: dict[_NodePath, SourceLocation]
) -> str:
    if not isinstance(value, str):
        _fail(
            "codec.invalid_record_layout",
            "codec",
            "Expected a string.",
            location=locations.get(at),
        )
    return value


def _records(
    value: object, at: _NodePath, locations: dict[_NodePath, SourceLocation]
) -> list[object]:
    if not isinstance(value, list):
        _fail(
            "codec.invalid_record_layout",
            "codec",
            "Expected a sequence of records.",
            location=locations.get(at),
        )
    return value


def _fields(
    value: object, at: _NodePath, locations: dict[_NodePath, SourceLocation]
) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail(
            "codec.invalid_record_layout",
            "codec",
            "Expected a mapping of fields.",
            location=locations.get(at),
        )
    return value


def _bind_value(
    value: object,
    *,
    record_id: str,
    field: str,
    at: _NodePath,
    locations: dict[_NodePath, SourceLocation],
) -> PropertyValue:
    def fail(code: str, message: str) -> Never:
        _fail(
            code,
            "typed_binding",
            message,
            record_id=record_id,
            field=field,
            location=locations.get(at),
        )

    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if not isinstance(value, dict):
        fail(
            "binding.invalid_value_form",
            "Expected text, an integer, or a tagged value.",
        )
    tag = value.get("type")
    if tag == "entity_ref":
        if value.keys() == {"type", "id"} and isinstance(value["id"], str):
            return EntityRef(value["id"])
        fail("binding.invalid_value_form", "An entity reference requires a string id.")
    if tag == "year_month":
        if value.keys() != {"type", "value"} or not isinstance(value["value"], str):
            fail(
                "binding.invalid_value_form", "A year_month requires one string value."
            )
        try:
            return YearMonth.parse(value["value"])
        except ValueError:
            fail(
                "binding.invalid_year_month",
                "YearMonth must use a valid YYYY-MM value.",
            )
    if tag == "temporal_extent":
        if (
            value.keys() != {"type", "start", "end"}
            or not isinstance(value["start"], str)
            or not isinstance(value["end"], dict)
        ):
            fail(
                "binding.invalid_temporal_extent",
                "A temporal extent requires start and one end state.",
            )
        end = value["end"]
        if len(end) != 1 or ("unknown" in end and end != {"unknown": True}):
            fail(
                "binding.invalid_temporal_extent",
                "A temporal extent must have exactly one valid end state.",
            )
        end_kind, end_value = next(iter(end.items()))
        if end_kind not in {"known", "ongoing_as_of", "unknown"} or (
            end_kind != "unknown" and not isinstance(end_value, str)
        ):
            fail(
                "binding.invalid_temporal_extent",
                "A temporal extent must have exactly one valid end state.",
            )
        try:
            if end_kind == "known":
                return TemporalExtent.closed(value["start"], end_value)
            if end_kind == "ongoing_as_of":
                return TemporalExtent.ongoing(value["start"], as_of=end_value)
            return TemporalExtent.unknown_end(value["start"])
        except ValueError:
            fail(
                "binding.invalid_year_month",
                "Temporal boundaries must use valid YYYY-MM values.",
            )
    fail("binding.invalid_value_form", "Unknown tagged value form.")


@dataclass(frozen=True, slots=True)
class _EntityRecord:
    id: str
    kind: str
    properties: dict[str, object]
    path: _NodePath


@dataclass(frozen=True, slots=True)
class _RelationRecord:
    id: str
    kind: str
    source: str
    target: str
    qualifiers: dict[str, object]
    path: _NodePath


@dataclass(frozen=True, slots=True)
class _DecodedDocument:
    ontology_id: str
    ontology_version: str
    realisation_id: str
    coverage_status: str
    coverage_scope: str
    entities: tuple[_EntityRecord, ...]
    relations: tuple[_RelationRecord, ...]


def _decode_record_layout(
    value: object, locations: dict[_NodePath, SourceLocation]
) -> _DecodedDocument:
    """Check all structural fields before ontology selection or typed binding."""
    doc = _mapping(
        value,
        {"format_version", "ontology", "realisation", "entities", "relations"},
        set(),
        (),
        locations,
    )
    version = _string(doc["format_version"], ("format_version",), locations)
    if version != "0.1":
        _fail(
            "codec.unsupported_format_version",
            "codec",
            f"Unsupported format version {version!r}.",
            location=locations.get(("format_version",)),
        )
    declared = _mapping(
        doc["ontology"], {"id", "version"}, set(), ("ontology",), locations
    )
    ontology_id = _string(declared["id"], ("ontology", "id"), locations)
    ontology_version = _string(declared["version"], ("ontology", "version"), locations)
    realised = _mapping(
        doc["realisation"], {"id", "coverage"}, set(), ("realisation",), locations
    )
    realisation_id = _string(realised["id"], ("realisation", "id"), locations)
    cover = _mapping(
        realised["coverage"],
        {"status", "scope"},
        set(),
        ("realisation", "coverage"),
        locations,
    )
    scope = _string(cover["scope"], ("realisation", "coverage", "scope"), locations)
    status = _string(cover["status"], ("realisation", "coverage", "status"), locations)
    entities: list[_EntityRecord] = []
    for index, raw in enumerate(_records(doc["entities"], ("entities",), locations)):
        at: _NodePath = ("entities", index)
        item = _mapping(raw, {"id", "kind"}, {"properties"}, at, locations)
        entity_id = _string(item["id"], (*at, "id"), locations)
        kind = _string(item["kind"], (*at, "kind"), locations)
        properties = _fields(item.get("properties", {}), (*at, "properties"), locations)
        entities.append(_EntityRecord(entity_id, kind, properties, at))

    relations: list[_RelationRecord] = []
    for index, raw in enumerate(_records(doc["relations"], ("relations",), locations)):
        at = ("relations", index)
        item = _mapping(
            raw, {"id", "kind", "source", "target"}, {"qualifiers"}, at, locations
        )
        relation_id = _string(item["id"], (*at, "id"), locations)
        kind = _string(item["kind"], (*at, "kind"), locations)
        source = _string(item["source"], (*at, "source"), locations)
        target = _string(item["target"], (*at, "target"), locations)
        qualifiers = _fields(item.get("qualifiers", {}), (*at, "qualifiers"), locations)
        relations.append(
            _RelationRecord(relation_id, kind, source, target, qualifiers, at)
        )

    return _DecodedDocument(
        ontology_id,
        ontology_version,
        realisation_id,
        status,
        scope,
        tuple(entities),
        tuple(relations),
    )


def _select_ontology(
    document: _DecodedDocument,
    ontology: OntologySchema,
    locations: dict[_NodePath, SourceLocation],
) -> None:
    if (document.ontology_id, document.ontology_version) != (
        ontology.id,
        ontology.version,
    ):
        _fail(
            "load.unsupported_ontology",
            "ontology_selection",
            "The file declares an unsupported ontology identity or version.",
            location=locations.get(("ontology",)),
        )


def _bind_candidate(
    document: _DecodedDocument, locations: dict[_NodePath, SourceLocation]
) -> tuple[RealisationCandidate, _RecordPaths]:
    """Construct typed records without inspecting ontology field definitions."""
    try:
        coverage = Coverage(
            CoverageStatus(document.coverage_status), document.coverage_scope
        )
    except ValueError:
        _fail(
            "binding.invalid_coverage_status",
            "typed_binding",
            f"Unsupported coverage status {document.coverage_status!r}.",
            location=locations.get(("realisation", "coverage", "status")),
        )

    record_paths: _RecordPaths = {}
    entities: list[Entity] = []
    for entity_record in document.entities:
        record_paths.setdefault(("entity", entity_record.id), []).append(
            entity_record.path
        )
        entities.append(
            Entity(
                entity_record.id,
                entity_record.kind,
                tuple(
                    Property(
                        name,
                        _bind_value(
                            prop,
                            record_id=entity_record.id,
                            field=f"properties.{name}",
                            at=(*entity_record.path, "properties", name),
                            locations=locations,
                        ),
                    )
                    for name, prop in entity_record.properties.items()
                ),
            )
        )

    relations: list[RelationAssertion] = []
    for relation_record in document.relations:
        record_paths.setdefault(("relation", relation_record.id), []).append(
            relation_record.path
        )
        relations.append(
            RelationAssertion(
                relation_record.id,
                relation_record.kind,
                EntityRef(relation_record.source),
                EntityRef(relation_record.target),
                tuple(
                    Qualifier(
                        name,
                        _bind_value(
                            q,
                            record_id=relation_record.id,
                            field=f"qualifiers.{name}",
                            at=(*relation_record.path, "qualifiers", name),
                            locations=locations,
                        ),
                    )
                    for name, q in relation_record.qualifiers.items()
                ),
            )
        )

    return RealisationCandidate(
        document.realisation_id,
        document.ontology_id,
        document.ontology_version,
        tuple(entities),
        tuple(relations),
        coverage,
    ), record_paths


def _semantic_finding(
    diagnostic: Diagnostic,
    record_paths: _RecordPaths,
    locations: dict[_NodePath, SourceLocation],
) -> LoadFinding:
    record_id = diagnostic.record_id or ""
    entity_paths = record_paths.get(("entity", record_id), [])
    relation_paths = record_paths.get(("relation", record_id), [])
    if diagnostic.code == "realisation.duplicate_entity_id":
        paths = entity_paths
    elif diagnostic.code == "realisation.duplicate_relation_id":
        paths = relation_paths
    elif entity_paths and relation_paths:
        paths = []  # The ID alone does not locate a unique record namespace.
    else:
        paths = entity_paths or relation_paths
    location = None
    if paths:
        # For duplicate IDs, point to the second occurrence of the record.
        path = paths[1] if len(paths) > 1 else paths[0]
        if diagnostic.field is not None:
            if path[0] == "entities":
                location = locations.get((*path, "properties", diagnostic.field))
            else:
                location = locations.get((*path, "qualifiers", diagnostic.field))
            location = location or locations.get((*path, diagnostic.field))
        location = location or locations.get(path)
    return LoadFinding(
        diagnostic.code,
        diagnostic.layer.value,
        diagnostic.message,
        diagnostic.record_id,
        diagnostic.field,
        location,
        diagnostic.severity,
    )


def load_realisation_yaml(path: str | Path, *, ontology: OntologySchema) -> LoadResult:
    """Read, bind, and validate one v0.1 YAML candidate against an exact ontology."""
    source_path = Path(path)
    try:
        data = source_path.read_bytes()
    except FileNotFoundError:
        return LoadRejected(
            (LoadFinding("reader.not_found", "file_reader", "File not found."),),
            source_path,
        )
    except OSError as exc:
        return LoadRejected(
            (LoadFinding("reader.unreadable", "file_reader", str(exc)),), source_path
        )
    source_state_id = sha256(data).hexdigest()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return LoadRejected(
            (
                LoadFinding(
                    "codec.invalid_encoding",
                    "codec",
                    str(exc),
                    location=SourceLocation(source_path, 1, 1),
                ),
            ),
            source_path,
            source_state_id,
        )
    try:
        decoded, locations = _decode_yaml(text, source_path)
        document = _decode_record_layout(decoded, locations)
        _select_ontology(document, ontology, locations)
        candidate, record_paths = _bind_candidate(document, locations)
    except _Failure as exc:
        return LoadRejected((exc.finding,), source_path, source_state_id)
    validated = validate_candidate(ontology, candidate)
    if isinstance(validated, Rejected):
        return LoadRejected(
            tuple(
                _semantic_finding(item, record_paths, locations)
                for item in validated.diagnostics
            ),
            source_path,
            source_state_id,
        )
    assert isinstance(validated, Accepted)
    return LoadAccepted(validated.realisation, source_path, source_state_id)
