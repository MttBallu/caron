"""Validation boundaries for ontology schemas and their realisations."""

from dataclasses import dataclass

from caron._invariants import INVARIANT_VALIDATORS
from caron.diagnostics import Diagnostic, DiagnosticLayer
from caron.entities import Entity, EntityRef, PropertyValue
from caron.ontology import (
    CONTEXT,
    EndpointPosition,
    OntologySchema,
    ValueKind,
)
from caron.realisations import RealisationCandidate, ValidatedRealisation
from caron.relations import QualifierValue, RelationAssertion
from caron.temporal import KnownEnd, OngoingAsOf, TemporalExtent, UnknownEnd, YearMonth


@dataclass(frozen=True, slots=True)
class Accepted:
    realisation: ValidatedRealisation


@dataclass(frozen=True, slots=True)
class Rejected:
    diagnostics: tuple[Diagnostic, ...]


type ValidationResult = Accepted | Rejected


def _duplicate_values(values: tuple[str, ...]) -> frozenset[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return frozenset(duplicates)


def _value_matches_kind(value: PropertyValue | QualifierValue, kind: ValueKind) -> bool:
    match kind:
        case ValueKind.TEXT:
            return isinstance(value, str)
        case ValueKind.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)
        case ValueKind.ENTITY_REFERENCE:
            return isinstance(value, EntityRef)
        case ValueKind.YEAR_MONTH:
            return isinstance(value, YearMonth)
        case ValueKind.TEMPORAL_EXTENT:
            return isinstance(value, TemporalExtent)


def validate_ontology(ontology: OntologySchema) -> tuple[Diagnostic, ...]:
    """Return every structural diagnostic found in an ontology schema."""

    diagnostics: list[Diagnostic] = []
    concept_ids = tuple(concept.id for concept in ontology.concepts)
    relation_kinds = tuple(relation.kind for relation in ontology.relations)
    concept_id_set = frozenset(concept_ids)
    relation_kind_set = frozenset(relation_kinds)
    invariant_ids = tuple(invariant.id for invariant in ontology.invariants)

    for concept_id in sorted(_duplicate_values(concept_ids)):
        diagnostics.append(
            Diagnostic(
                code="ontology.duplicate_concept",
                layer=DiagnosticLayer.ONTOLOGY,
                message=f"Concept {concept_id!r} is defined more than once.",
                record_id=concept_id,
            )
        )

    for relation_kind in sorted(_duplicate_values(relation_kinds)):
        diagnostics.append(
            Diagnostic(
                code="ontology.duplicate_relation",
                layer=DiagnosticLayer.ONTOLOGY,
                message=f"Relation {relation_kind!r} is defined more than once.",
                record_id=relation_kind,
            )
        )

    for invariant_id in sorted(_duplicate_values(invariant_ids)):
        diagnostics.append(
            Diagnostic(
                code="ontology.duplicate_invariant",
                layer=DiagnosticLayer.ONTOLOGY,
                message=f"Invariant {invariant_id!r} is declared more than once.",
                record_id=invariant_id,
            )
        )

    for invariant_id in sorted(set(invariant_ids) - INVARIANT_VALIDATORS.keys()):
        diagnostics.append(
            Diagnostic(
                code="ontology.unimplemented_invariant",
                layer=DiagnosticLayer.ONTOLOGY,
                message=(
                    f"Invariant {invariant_id!r} has no registered implementation."
                ),
                record_id=invariant_id,
            )
        )

    for concept in ontology.concepts:
        for property_name in sorted(
            _duplicate_values(tuple(item.name for item in concept.properties))
        ):
            diagnostics.append(
                Diagnostic(
                    code="ontology.duplicate_property",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message=(
                        f"Property {property_name!r} is defined more than once on "
                        f"concept {concept.id!r}."
                    ),
                    record_id=concept.id,
                    field=property_name,
                )
            )

        for property_definition in concept.properties:
            diagnostics.extend(
                _reference_definition_diagnostics(
                    owner_id=concept.id,
                    field_name=property_definition.name,
                    value_kind=property_definition.value_kind,
                    allowed_reference_kinds=property_definition.allowed_reference_kinds,
                    known_concepts=concept_id_set,
                )
            )

    for relation in ontology.relations:
        if not relation.source_kinds:
            diagnostics.append(
                Diagnostic(
                    code="ontology.empty_source_kinds",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message=f"Relation {relation.kind!r} has no allowed source kind.",
                    record_id=relation.kind,
                    field="source_kinds",
                )
            )
        if not relation.target_kinds:
            diagnostics.append(
                Diagnostic(
                    code="ontology.empty_target_kinds",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message=f"Relation {relation.kind!r} has no allowed target kind.",
                    record_id=relation.kind,
                    field="target_kinds",
                )
            )

        for endpoint, kinds in (
            ("source_kinds", relation.source_kinds),
            ("target_kinds", relation.target_kinds),
        ):
            for unknown_kind in sorted(kinds - concept_id_set):
                diagnostics.append(
                    Diagnostic(
                        code="ontology.unknown_endpoint_kind",
                        layer=DiagnosticLayer.ONTOLOGY,
                        message=(
                            f"Relation {relation.kind!r} uses unknown concept "
                            f"{unknown_kind!r} in {endpoint}."
                        ),
                        record_id=relation.kind,
                        field=endpoint,
                    )
                )

        for qualifier_name in sorted(
            _duplicate_values(tuple(item.name for item in relation.qualifiers))
        ):
            diagnostics.append(
                Diagnostic(
                    code="ontology.duplicate_qualifier",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message=(
                        f"Qualifier {qualifier_name!r} is defined more than once on "
                        f"relation {relation.kind!r}."
                    ),
                    record_id=relation.kind,
                    field=qualifier_name,
                )
            )

        for qualifier in relation.qualifiers:
            diagnostics.extend(
                _reference_definition_diagnostics(
                    owner_id=relation.kind,
                    field_name=qualifier.name,
                    value_kind=qualifier.value_kind,
                    allowed_reference_kinds=qualifier.allowed_reference_kinds,
                    known_concepts=concept_id_set,
                )
            )

    for requirement in ontology.requirements:
        if requirement.concept not in concept_id_set:
            diagnostics.append(
                Diagnostic(
                    code="ontology.unknown_requirement_concept",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message=(
                        "Requirement refers to unknown concept "
                        f"{requirement.concept!r}."
                    ),
                    record_id=requirement.concept,
                )
            )

        requirement_relation = ontology.relation(requirement.relation_kind)
        if (
            requirement.relation_kind not in relation_kind_set
            or requirement_relation is None
        ):
            diagnostics.append(
                Diagnostic(
                    code="ontology.unknown_requirement_relation",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message=(
                        "Requirement refers to unknown relation "
                        f"{requirement.relation_kind!r}."
                    ),
                    record_id=requirement.relation_kind,
                )
            )
        elif requirement.concept in concept_id_set:
            endpoint_kinds = (
                requirement_relation.source_kinds
                if requirement.endpoint is EndpointPosition.SOURCE
                else requirement_relation.target_kinds
            )
            if requirement.concept not in endpoint_kinds:
                diagnostics.append(
                    Diagnostic(
                        code="ontology.incompatible_requirement_endpoint",
                        layer=DiagnosticLayer.ONTOLOGY,
                        message=(
                            f"Concept {requirement.concept!r} cannot occupy the "
                            f"{requirement.endpoint.value} of relation "
                            f"{requirement.relation_kind!r}."
                        ),
                        record_id=requirement.concept,
                        field=requirement.endpoint.value,
                    )
                )

        if requirement.minimum < 0:
            diagnostics.append(
                Diagnostic(
                    code="ontology.negative_minimum",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message="A relation requirement minimum cannot be negative.",
                    record_id=requirement.concept,
                )
            )
        if (
            requirement.maximum is not None
            and requirement.maximum < requirement.minimum
        ):
            diagnostics.append(
                Diagnostic(
                    code="ontology.invalid_cardinality_range",
                    layer=DiagnosticLayer.ONTOLOGY,
                    message=(
                        "A relation requirement maximum cannot be below its minimum."
                    ),
                    record_id=requirement.concept,
                )
            )

    return tuple(diagnostics)


def _reference_definition_diagnostics(
    *,
    owner_id: str,
    field_name: str,
    value_kind: ValueKind,
    allowed_reference_kinds: frozenset[str],
    known_concepts: frozenset[str],
) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    if value_kind is not ValueKind.ENTITY_REFERENCE and allowed_reference_kinds:
        diagnostics.append(
            Diagnostic(
                code="ontology.references_on_scalar",
                layer=DiagnosticLayer.ONTOLOGY,
                message=(
                    f"Scalar field {field_name!r} cannot constrain entity "
                    "reference kinds."
                ),
                record_id=owner_id,
                field=field_name,
            )
        )
    for unknown_kind in sorted(allowed_reference_kinds - known_concepts):
        diagnostics.append(
            Diagnostic(
                code="ontology.unknown_reference_kind",
                layer=DiagnosticLayer.ONTOLOGY,
                message=(
                    f"Field {field_name!r} allows unknown reference kind "
                    f"{unknown_kind!r}."
                ),
                record_id=owner_id,
                field=field_name,
            )
        )
    return tuple(diagnostics)


def validate_candidate(
    ontology: OntologySchema,
    candidate: RealisationCandidate,
) -> ValidationResult:
    """Validate a candidate and return either diagnostics or an immutable value."""

    diagnostics = list(validate_ontology(ontology))
    if diagnostics:
        return Rejected(tuple(diagnostics))

    if candidate.ontology_id != ontology.id:
        diagnostics.append(
            Diagnostic(
                code="realisation.ontology_id_mismatch",
                layer=DiagnosticLayer.REALISATION,
                message=(
                    f"Candidate targets ontology {candidate.ontology_id!r}, not "
                    f"{ontology.id!r}."
                ),
                record_id=candidate.id,
                field="ontology_id",
            )
        )
    if candidate.ontology_version != ontology.version:
        diagnostics.append(
            Diagnostic(
                code="realisation.ontology_version_mismatch",
                layer=DiagnosticLayer.REALISATION,
                message=(
                    "Candidate targets ontology version "
                    f"{candidate.ontology_version!r}, "
                    f"not {ontology.version!r}."
                ),
                record_id=candidate.id,
                field="ontology_version",
            )
        )

    entity_ids = tuple(entity.id for entity in candidate.entities)
    relation_ids = tuple(relation.id for relation in candidate.relations)
    entity_by_id = {entity.id: entity for entity in candidate.entities}

    for entity_id in sorted(_duplicate_values(entity_ids)):
        diagnostics.append(
            Diagnostic(
                code="realisation.duplicate_entity_id",
                layer=DiagnosticLayer.REALISATION,
                message=f"Entity id {entity_id!r} occurs more than once.",
                record_id=entity_id,
            )
        )
    for relation_id in sorted(_duplicate_values(relation_ids)):
        diagnostics.append(
            Diagnostic(
                code="realisation.duplicate_relation_id",
                layer=DiagnosticLayer.REALISATION,
                message=f"Relation id {relation_id!r} occurs more than once.",
                record_id=relation_id,
            )
        )

    for entity in candidate.entities:
        diagnostics.extend(_validate_entity(ontology, entity, entity_by_id))
    for relation in candidate.relations:
        diagnostics.extend(_validate_relation(ontology, relation, entity_by_id))

    diagnostics.extend(
        _validate_relation_requirements(
            ontology, candidate.entities, candidate.relations
        )
    )
    diagnostics.extend(
        _validate_temporal_containment(candidate.entities, candidate.relations)
    )
    for invariant in ontology.invariants:
        invariant_validator = INVARIANT_VALIDATORS.get(invariant.id)
        if invariant_validator is not None:
            diagnostics.extend(invariant_validator(ontology, candidate))

    if diagnostics:
        return Rejected(tuple(diagnostics))
    return Accepted(ValidatedRealisation._from_candidate(ontology, candidate))


def _validate_entity(
    ontology: OntologySchema,
    entity: Entity,
    entity_by_id: dict[str, Entity],
) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    concept = ontology.concept(entity.kind)
    if concept is None:
        return (
            Diagnostic(
                code="record.unknown_concept",
                layer=DiagnosticLayer.LOCAL_RECORD,
                message=f"Entity uses unknown concept {entity.kind!r}.",
                record_id=entity.id,
                field="kind",
            ),
        )

    duplicate_properties = _duplicate_values(
        tuple(item.name for item in entity.properties)
    )
    for property_name in sorted(duplicate_properties):
        diagnostics.append(
            Diagnostic(
                code="record.duplicate_property",
                layer=DiagnosticLayer.LOCAL_RECORD,
                message=f"Property {property_name!r} occurs more than once.",
                record_id=entity.id,
                field=property_name,
            )
        )

    provided_names = frozenset(item.name for item in entity.properties)
    for definition in concept.properties:
        if definition.required and definition.name not in provided_names:
            diagnostics.append(
                Diagnostic(
                    code="record.missing_required_property",
                    layer=DiagnosticLayer.LOCAL_RECORD,
                    message=f"Required property {definition.name!r} is missing.",
                    record_id=entity.id,
                    field=definition.name,
                )
            )

    for item in entity.properties:
        property_definition = concept.property_definition(item.name)
        if property_definition is None:
            diagnostics.append(
                Diagnostic(
                    code="record.unknown_property",
                    layer=DiagnosticLayer.LOCAL_RECORD,
                    message=(
                        f"Property {item.name!r} is not defined for concept "
                        f"{entity.kind!r}."
                    ),
                    record_id=entity.id,
                    field=item.name,
                )
            )
            continue
        diagnostics.extend(
            _validate_field_value(
                value=item.value,
                value_kind=property_definition.value_kind,
                allowed_reference_kinds=property_definition.allowed_reference_kinds,
                entity_by_id=entity_by_id,
                record_id=entity.id,
                field_name=item.name,
            )
        )
        if isinstance(item.value, TemporalExtent):
            diagnostics.extend(_validate_temporal_extent(entity.id, item.value))
    return tuple(diagnostics)


def _validate_temporal_extent(
    entity_id: str,
    extent: TemporalExtent,
) -> tuple[Diagnostic, ...]:
    match extent.end:
        case KnownEnd(month) if month < extent.start:
            message = "Known temporal end must not be before the start month."
        case OngoingAsOf(month) if month < extent.start:
            message = "Ongoing observation must not be before the start month."
        case KnownEnd() | OngoingAsOf() | UnknownEnd():
            return ()
    return (
        Diagnostic(
            code="record.invalid_temporal_extent",
            layer=DiagnosticLayer.LOCAL_RECORD,
            message=message,
            record_id=entity_id,
            field="temporal_extent",
        ),
    )


def _validate_relation(
    ontology: OntologySchema,
    relation: RelationAssertion,
    entity_by_id: dict[str, Entity],
) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    definition = ontology.relation(relation.kind)
    if definition is None:
        return (
            Diagnostic(
                code="record.unknown_relation",
                layer=DiagnosticLayer.LOCAL_RECORD,
                message=f"Relation uses unknown kind {relation.kind!r}.",
                record_id=relation.id,
                field="kind",
            ),
        )

    source = entity_by_id.get(relation.source.entity_id)
    target = entity_by_id.get(relation.target.entity_id)
    for endpoint_name, endpoint, allowed_kinds in (
        ("source", source, definition.source_kinds),
        ("target", target, definition.target_kinds),
    ):
        reference = relation.source if endpoint_name == "source" else relation.target
        if endpoint is None:
            diagnostics.append(
                Diagnostic(
                    code="record.dangling_endpoint",
                    layer=DiagnosticLayer.LOCAL_RECORD,
                    message=(
                        f"Relation {endpoint_name} refers to missing entity "
                        f"{reference.entity_id!r}."
                    ),
                    record_id=relation.id,
                    field=endpoint_name,
                )
            )
        elif endpoint.kind not in allowed_kinds:
            diagnostics.append(
                Diagnostic(
                    code="record.invalid_endpoint_kind",
                    layer=DiagnosticLayer.LOCAL_RECORD,
                    message=(
                        f"Entity kind {endpoint.kind!r} is not allowed at the "
                        f"{endpoint_name} of relation {relation.kind!r}."
                    ),
                    record_id=relation.id,
                    field=endpoint_name,
                )
            )

    duplicate_qualifiers = _duplicate_values(
        tuple(item.name for item in relation.qualifiers)
    )
    for qualifier_name in sorted(duplicate_qualifiers):
        diagnostics.append(
            Diagnostic(
                code="record.duplicate_qualifier",
                layer=DiagnosticLayer.LOCAL_RECORD,
                message=f"Qualifier {qualifier_name!r} occurs more than once.",
                record_id=relation.id,
                field=qualifier_name,
            )
        )

    provided_names = frozenset(item.name for item in relation.qualifiers)
    for qualifier_definition in definition.qualifiers:
        if (
            qualifier_definition.required
            and qualifier_definition.name not in provided_names
        ):
            diagnostics.append(
                Diagnostic(
                    code="record.missing_required_qualifier",
                    layer=DiagnosticLayer.LOCAL_RECORD,
                    message=(
                        f"Required qualifier {qualifier_definition.name!r} is missing."
                    ),
                    record_id=relation.id,
                    field=qualifier_definition.name,
                )
            )

    for qualifier in relation.qualifiers:
        provided_qualifier_definition = definition.qualifier_definition(qualifier.name)
        if provided_qualifier_definition is None:
            diagnostics.append(
                Diagnostic(
                    code="record.unknown_qualifier",
                    layer=DiagnosticLayer.LOCAL_RECORD,
                    message=(
                        f"Qualifier {qualifier.name!r} is not defined for relation "
                        f"{relation.kind!r}."
                    ),
                    record_id=relation.id,
                    field=qualifier.name,
                )
            )
            continue
        diagnostics.extend(
            _validate_field_value(
                value=qualifier.value,
                value_kind=provided_qualifier_definition.value_kind,
                allowed_reference_kinds=(
                    provided_qualifier_definition.allowed_reference_kinds
                ),
                entity_by_id=entity_by_id,
                record_id=relation.id,
                field_name=qualifier.name,
            )
        )
    return tuple(diagnostics)


def _validate_field_value(
    *,
    value: PropertyValue | QualifierValue,
    value_kind: ValueKind,
    allowed_reference_kinds: frozenset[str],
    entity_by_id: dict[str, Entity],
    record_id: str,
    field_name: str,
) -> tuple[Diagnostic, ...]:
    if not _value_matches_kind(value, value_kind):
        return (
            Diagnostic(
                code="record.invalid_value_kind",
                layer=DiagnosticLayer.LOCAL_RECORD,
                message=(
                    f"Field {field_name!r} must contain a {value_kind.value} value."
                ),
                record_id=record_id,
                field=field_name,
            ),
        )
    if not isinstance(value, EntityRef):
        return ()

    referenced = entity_by_id.get(value.entity_id)
    if referenced is None:
        return (
            Diagnostic(
                code="record.dangling_reference",
                layer=DiagnosticLayer.LOCAL_RECORD,
                message=(
                    f"Field {field_name!r} refers to missing entity "
                    f"{value.entity_id!r}."
                ),
                record_id=record_id,
                field=field_name,
            ),
        )
    if allowed_reference_kinds and referenced.kind not in allowed_reference_kinds:
        return (
            Diagnostic(
                code="record.invalid_reference_kind",
                layer=DiagnosticLayer.LOCAL_RECORD,
                message=(
                    f"Field {field_name!r} cannot refer to concept {referenced.kind!r}."
                ),
                record_id=record_id,
                field=field_name,
            ),
        )
    return ()


def _validate_relation_requirements(
    ontology: OntologySchema,
    entities: tuple[Entity, ...],
    relations: tuple[RelationAssertion, ...],
) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    for requirement in ontology.requirements:
        for entity in (item for item in entities if item.kind == requirement.concept):
            count = sum(
                relation.kind == requirement.relation_kind
                and (
                    relation.source.entity_id == entity.id
                    if requirement.endpoint is EndpointPosition.SOURCE
                    else relation.target.entity_id == entity.id
                )
                for relation in relations
            )
            if count < requirement.minimum:
                diagnostics.append(
                    Diagnostic(
                        code="realisation.relation_requirement_below_minimum",
                        layer=DiagnosticLayer.REALISATION,
                        message=(
                            f"Entity requires at least {requirement.minimum} "
                            f"{requirement.relation_kind!r} relation(s) at its "
                            f"{requirement.endpoint.value} endpoint; found {count}."
                        ),
                        record_id=entity.id,
                        field=requirement.relation_kind,
                    )
                )
            if requirement.maximum is not None and count > requirement.maximum:
                diagnostics.append(
                    Diagnostic(
                        code="realisation.relation_requirement_above_maximum",
                        layer=DiagnosticLayer.REALISATION,
                        message=(
                            f"Entity allows at most {requirement.maximum} "
                            f"{requirement.relation_kind!r} relation(s) at its "
                            f"{requirement.endpoint.value} endpoint; found {count}."
                        ),
                        record_id=entity.id,
                        field=requirement.relation_kind,
                    )
                )
    return tuple(diagnostics)


def _validate_temporal_containment(
    entities: tuple[Entity, ...],
    relations: tuple[RelationAssertion, ...],
) -> tuple[Diagnostic, ...]:
    """Reject context occurrences that cannot fit in dated ancestors."""

    context_by_id = {entity.id: entity for entity in entities if entity.kind == CONTEXT}
    parent_edges: dict[str, list[tuple[str, str]]] = {}
    for relation in relations:
        if relation.kind != "part_of":
            continue
        if (
            relation.source.entity_id not in context_by_id
            or relation.target.entity_id not in context_by_id
        ):
            continue
        parent_edges.setdefault(relation.source.entity_id, []).append(
            (relation.target.entity_id, relation.id)
        )

    diagnostics: list[Diagnostic] = []
    for child in context_by_id.values():
        ancestors = _ancestor_paths(child.id, parent_edges)
        dated_ancestors = tuple(
            (ancestor_id, relation_path, ancestor_extent)
            for ancestor_id, relation_path in ancestors
            if isinstance(
                ancestor_extent := context_by_id[ancestor_id].property(
                    "temporal_extent"
                ),
                TemporalExtent,
            )
        )
        lower_bound = max(
            (extent.start for _, _, extent in dated_ancestors),
            default=None,
        )
        upper_bound = min(
            (
                extent.end.month
                for _, _, extent in dated_ancestors
                if isinstance(extent.end, KnownEnd)
            ),
            default=None,
        )
        if (
            lower_bound is not None
            and upper_bound is not None
            and lower_bound > upper_bound
        ):
            diagnostics.append(
                Diagnostic(
                    code="realisation.temporal_containment_impossible",
                    layer=DiagnosticLayer.REALISATION,
                    message=(
                        f"Dated ancestors of context {child.id!r} have no common "
                        "month in which its nonempty occurrence can fit."
                    ),
                    record_id=child.id,
                    field="temporal_extent",
                )
            )
            continue

        child_extent = child.property("temporal_extent")
        if not isinstance(child_extent, TemporalExtent):
            continue
        for ancestor_id, relation_path, ancestor_extent in dated_ancestors:
            if _can_be_contained(child_extent, ancestor_extent):
                continue
            diagnostics.append(
                Diagnostic(
                    code="realisation.temporal_containment_impossible",
                    layer=DiagnosticLayer.REALISATION,
                    message=(
                        f"Context {child.id!r} cannot occur within dated ancestor "
                        f"{ancestor_id!r} along relations {relation_path!r}."
                    ),
                    record_id=child.id,
                    field="temporal_extent",
                )
            )
    return tuple(diagnostics)


def _ancestor_paths(
    child_id: str,
    parent_edges: dict[str, list[tuple[str, str]]],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    discovered: list[tuple[str, tuple[str, ...]]] = []
    pending: list[tuple[str, tuple[str, ...]]] = [(child_id, ())]
    visited = {child_id}
    while pending:
        current_id, path = pending.pop()
        for parent_id, relation_id in parent_edges.get(current_id, []):
            if parent_id in visited:
                continue
            visited.add(parent_id)
            parent_path = (*path, relation_id)
            discovered.append((parent_id, parent_path))
            pending.append((parent_id, parent_path))
    return tuple(discovered)


def _can_be_contained(child: TemporalExtent, parent: TemporalExtent) -> bool:
    if child.start < parent.start:
        return False
    if not isinstance(parent.end, KnownEnd):
        return True
    match child.end:
        case KnownEnd(month) | OngoingAsOf(month):
            child_minimum_end = month
        case UnknownEnd():
            child_minimum_end = child.start
    return child_minimum_end <= parent.end.month
