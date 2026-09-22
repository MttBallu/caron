"""Diagnostic-only record checks against the complete 5.0-dev catalogue.

These deliberately do not remove pending declarations or claim acceptance of
a partial implementation. Full candidate conformance belongs to later phases.
"""

from dataclasses import replace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from caron import (
    Coverage,
    CoverageStatus,
    Diagnostic,
    DiagnosticLayer,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    RelationAssertion,
    Severity,
    TemporalExtent,
    YearMonth,
)
from caron.entities import PropertyValue
from caron.ontology import _career_ontology_v5_0_development
from caron.validation import _validate_local_records

KINDS = (
    "Person",
    "Collective",
    "Context",
    "Activity",
    "Technology",
    "Method",
    "Subject",
    "Language",
    "Artifact",
    "Proposition",
    "Organization",
    "Place",
    "Credential",
)
BLANKS = ("", " \t\n", "\u00a0\u2003")


def _entity(kind: str, identifier: str | None = None) -> Entity:
    properties: tuple[Property, ...] = (Property("label", "Shared label"),)
    if kind == "Proposition":
        properties += (
            Property("content", "Substantive content"),
            Property("context", EntityRef("context")),
        )
    return Entity(kind.lower() if identifier is None else identifier, kind, properties)


def _candidate(
    *entities: Entity, relations: tuple[RelationAssertion, ...] = ()
) -> RealisationCandidate:
    return RealisationCandidate(
        id="local-record-test",
        ontology_id="caron.career-model",
        ontology_version="5.0-dev",
        entities=entities,
        relations=relations,
        coverage=Coverage(CoverageStatus.SELECTIVE, "Local record checks only"),
    )


def _local(candidate: RealisationCandidate) -> tuple[Diagnostic, ...]:
    return _validate_local_records(_career_ontology_v5_0_development(), candidate)


def _assert_issue(
    candidate: RealisationCandidate,
    code: str,
    record_id: str,
    field: str | None,
    layer: DiagnosticLayer = DiagnosticLayer.LOCAL_RECORD,
) -> None:
    diagnostics = _local(candidate)
    assert [
        (d.code, d.layer, d.record_id, d.field, d.severity) for d in diagnostics
    ] == [(code, layer, record_id, field, Severity.ERROR)]
    assert diagnostics[0].message


def _participates(identifier: str = "relation") -> RelationAssertion:
    return RelationAssertion(
        identifier,
        "participates_in",
        EntityRef("person"),
        EntityRef("context"),
        (Qualifier("role", "Contributor"),),
    )


@pytest.mark.parametrize("record_type", ("entity", "relation"))
@pytest.mark.parametrize(
    "identifier",
    (
        *BLANKS,
        " leading",
        "trailing ",
        "\tbefore",
        "after\n",
        "\u00a0before",
        "after\u2003",
    ),
)
def test_invalid_identifiers(record_type: str, identifier: str) -> None:
    candidate = (
        _candidate(_entity("Person", identifier))
        if record_type == "entity"
        else _candidate(
            _entity("Person"),
            _entity("Context"),
            relations=(_participates(identifier),),
        )
    )
    _assert_issue(candidate, "record.invalid_identifier", identifier, "id")


@pytest.mark.parametrize(
    "identifier",
    ("x", "context:misleading", "no prefix", "a\tb", "a\nb", "é/東京", "A:B:C"),
)
def test_identifiers_are_opaque_and_namespaces_are_separate(identifier: str) -> None:
    # A Person and a relation may share any valid identifier, even one that
    # resembles a different concept's prefix. Resolve the complete identifier.
    person = _entity("Person", identifier)
    relation = replace(_participates(identifier), source=EntityRef(identifier))
    assert _local(_candidate(person, _entity("Context"), relations=(relation,))) == ()


def test_identifier_case_is_significant() -> None:
    assert _local(_candidate(_entity("Person", "Id"), _entity("Person", "id"))) == ()
    candidate = _candidate(
        _entity("Person", "PERSON"), _entity("Context"), relations=(_participates(),)
    )
    _assert_issue(candidate, "record.dangling_endpoint", "relation", "source")


@pytest.mark.parametrize("record_type", ("entity", "relation"))
def test_duplicate_identifiers_within_each_namespace(record_type: str) -> None:
    if record_type == "entity":
        candidate = _candidate(_entity("Person", "shared"), _entity("Place", "shared"))
        code = "realisation.duplicate_entity_id"
    else:
        # Different roles are different facts, but still cannot share an id.
        relation = _participates("shared")
        candidate = _candidate(
            _entity("Person"),
            _entity("Context"),
            relations=(
                relation,
                replace(relation, qualifiers=(Qualifier("role", "Lead"),)),
            ),
        )
        code = "realisation.duplicate_relation_id"
    _assert_issue(candidate, code, "shared", None, DiagnosticLayer.REALISATION)


@given(st.text())
def test_identifier_lexical_rule_for_arbitrary_unicode(identifier: str) -> None:
    diagnostics = _local(_candidate(_entity("Person", identifier)))
    valid = (
        bool(identifier)
        and not identifier[0].isspace()
        and not identifier[-1].isspace()
    )
    assert (diagnostics == ()) is valid
    if not valid:
        assert [item.code for item in diagnostics] == ["record.invalid_identifier"]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("blank", BLANKS)
def test_every_concept_requires_nonblank_label(kind: str, blank: str) -> None:
    entity = _entity(kind, "subject")
    entity = replace(
        entity, properties=(Property("label", blank), *entity.properties[1:])
    )
    _assert_issue(
        _candidate(entity, _entity("Context")),
        "record.blank_required_text",
        "subject",
        "label",
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("missing", (True, False))
def test_missing_and_wrong_type_labels_have_distinct_diagnostics(
    kind: str, missing: bool
) -> None:
    entity = _entity(kind, "subject")
    label = () if missing else (Property("label", 42),)
    entity = replace(entity, properties=label + entity.properties[1:])
    code = (
        "record.missing_required_property" if missing else "record.invalid_value_kind"
    )
    _assert_issue(_candidate(entity, _entity("Context")), code, "subject", "label")


@pytest.mark.parametrize("value", (*BLANKS, 42, None))
def test_proposition_content_is_required_independently_of_label(
    value: PropertyValue | None,
) -> None:
    properties: tuple[Property, ...] = (
        Property("label", "Not a content substitute"),
        Property("context", EntityRef("context")),
    )
    if value is not None:
        properties += (Property("content", value),)
    candidate = _candidate(
        Entity("proposition", "Proposition", properties), _entity("Context")
    )
    code = (
        "record.missing_required_property"
        if value is None
        else "record.invalid_value_kind"
        if isinstance(value, int)
        else "record.blank_required_text"
    )
    _assert_issue(candidate, code, "proposition", "content")


ROLE_RELATIONS = (
    ("participates_in", "person", "context"),
    ("collective_membership", "person", "collective"),
    ("organization_association", "organization", "context"),
)


@pytest.mark.parametrize(("kind", "source", "target"), ROLE_RELATIONS)
@pytest.mark.parametrize("value", (*BLANKS, 42, None))
def test_roles_are_required_nonblank_text(
    kind: str, source: str, target: str, value: PropertyValue | None
) -> None:
    qualifiers: tuple[Qualifier, ...] = (
        () if value is None else (Qualifier("role", value),)
    )
    if kind == "collective_membership":
        qualifiers += (Qualifier("context", EntityRef("context")),)
    relation = RelationAssertion(
        "relation", kind, EntityRef(source), EntityRef(target), qualifiers
    )
    candidate = _candidate(*(_entity(k) for k in KINDS), relations=(relation,))
    code = (
        "record.missing_required_qualifier"
        if value is None
        else "record.invalid_value_kind"
        if isinstance(value, int)
        else "record.blank_required_text"
    )
    _assert_issue(candidate, code, "relation", "role")


def test_labels_content_and_open_roles_are_not_normalized() -> None:
    text = " \tIndependent role / libre — 新しい\n"
    entities = tuple(
        replace(
            _entity(kind),
            properties=(
                Property("label", text),
                *(
                    (
                        Property("content", text),
                        Property("context", EntityRef("context")),
                    )
                    if kind == "Proposition"
                    else ()
                ),
            ),
        )
        for kind in KINDS
    )
    relations = tuple(
        RelationAssertion(
            kind,
            kind,
            EntityRef(source),
            EntityRef(target),
            (Qualifier("role", text),)
            + (
                (Qualifier("context", EntityRef("context")),)
                if kind == "collective_membership"
                else ()
            ),
        )
        for kind, source, target in ROLE_RELATIONS
    )
    candidate = _candidate(*entities, relations=relations)
    before = repr(candidate)
    assert _local(candidate) == ()
    assert repr(candidate) == before
    assert all(entity.property("label") == text for entity in candidate.entities)


@pytest.mark.parametrize(
    "value", (None, YearMonth(1, 1), YearMonth(2026, 9), YearMonth(9999, 12))
)
def test_credential_award_month_is_optional(value: YearMonth | None) -> None:
    credential = _entity("Credential")
    if value is not None:
        credential = replace(
            credential,
            properties=(*credential.properties, Property("awarded_in", value)),
        )
    assert _local(_candidate(credential)) == ()


@pytest.mark.parametrize(
    "value",
    (
        "2026-09",
        "2026",
        "2026-09-22",
        "2026-09-22T00:00Z",
        2026,
        True,
        EntityRef("context"),
        TemporalExtent.unknown_end("2026-09"),
    ),
)
def test_award_month_does_not_coerce_other_value_domains(value: PropertyValue) -> None:
    credential = _entity("Credential")
    credential = replace(
        credential, properties=(*credential.properties, Property("awarded_in", value))
    )
    _assert_issue(
        _candidate(credential, _entity("Context")),
        "record.invalid_value_kind",
        "credential",
        "awarded_in",
    )


@pytest.mark.parametrize(
    ("kind", "name", "value"),
    (
        ("Context", "status", "planned"),
        ("Context", "start", YearMonth(2026, 1)),
        ("Context", "end", YearMonth(2026, 9)),
        ("Activity", "temporal_extent", TemporalExtent.unknown_end("2026-09")),
        ("Credential", "temporal_extent", TemporalExtent.unknown_end("2026-09")),
        ("Credential", "awarded_at", "2026-09-22"),
        ("Person", "Label", "wrong case"),
    ),
)
def test_unknown_properties(kind: str, name: str, value: PropertyValue) -> None:
    entity = _entity(kind)
    entity = replace(entity, properties=(*entity.properties, Property(name, value)))
    _assert_issue(_candidate(entity), "record.unknown_property", entity.id, name)


@pytest.mark.parametrize(
    "kind",
    (
        "Agent",
        "Learnable",
        "IntellectualResource",
        "ActivityOutcomeRelation",
        "person",
        "Unknown",
    ),
)
def test_unknown_concepts_and_family_names_are_not_entity_kinds(kind: str) -> None:
    _assert_issue(
        _candidate(_entity(kind, "entity")), "record.unknown_concept", "entity", "kind"
    )


@pytest.mark.parametrize("kind", ("Participates_in", "located_at", "unknown"))
def test_unknown_relation_kinds(kind: str) -> None:
    relation = replace(_participates(), kind=kind)
    _assert_issue(
        _candidate(_entity("Person"), _entity("Context"), relations=(relation,)),
        "record.unknown_relation",
        "relation",
        "kind",
    )


@pytest.mark.parametrize("field", ("source", "target"))
@pytest.mark.parametrize(
    ("reference", "code"),
    (
        ("missing", "record.dangling_endpoint"),
        ("place", "record.invalid_endpoint_kind"),
    ),
)
def test_endpoint_closure_and_kind(field: str, reference: str, code: str) -> None:
    relation = (
        replace(_participates(), source=EntityRef(reference))
        if field == "source"
        else replace(_participates(), target=EntityRef(reference))
    )
    _assert_issue(
        _candidate(*(_entity(k) for k in KINDS), relations=(relation,)),
        code,
        "relation",
        field,
    )


@pytest.mark.parametrize(
    ("value", "code"),
    (
        (None, "record.missing_required_property"),
        ("context", "record.invalid_value_kind"),
        (EntityRef("missing"), "record.dangling_reference"),
        (EntityRef("CONTEXT"), "record.dangling_reference"),
        (EntityRef("person"), "record.invalid_reference_kind"),
    ),
)
def test_proposition_context_reference(value: PropertyValue | None, code: str) -> None:
    entity = _entity("Proposition")
    properties = entity.properties[:2] + (
        () if value is None else (Property("context", value),)
    )
    _assert_issue(
        _candidate(
            replace(entity, properties=properties),
            _entity("Context"),
            _entity("Person"),
        ),
        code,
        "proposition",
        "context",
    )


REFERENCE_QUALIFIERS = (
    ("participates_in", "person", "context", "organization", "organization", False),
    ("collective_membership", "person", "collective", "context", "context", True),
    ("exposed_to", "person", "technology", "context", "context", True),
    ("learns", "person", "language", "context", "context", True),
)


@pytest.mark.parametrize(
    ("kind", "source", "target", "field", "valid_id", "required"), REFERENCE_QUALIFIERS
)
@pytest.mark.parametrize(
    "case", ("valid", "absent", "scalar", "dangling", "wrong_kind")
)
def test_qualifier_references(
    kind: str,
    source: str,
    target: str,
    field: str,
    valid_id: str,
    required: bool,
    case: str,
) -> None:
    values: dict[str, PropertyValue] = {
        "valid": EntityRef(valid_id),
        "scalar": valid_id,
        "dangling": EntityRef("missing"),
        "wrong_kind": EntityRef("person"),
    }
    qualifiers: tuple[Qualifier, ...] = (
        () if case == "absent" else (Qualifier(field, values[case]),)
    )
    if kind in {"participates_in", "collective_membership"}:
        qualifiers += (Qualifier("role", "Contributor"),)
    relation = RelationAssertion(
        "relation", kind, EntityRef(source), EntityRef(target), qualifiers
    )
    candidate = _candidate(*(_entity(k) for k in KINDS), relations=(relation,))
    if case == "valid" or (case == "absent" and not required):
        assert _local(candidate) == ()
    else:
        code = {
            "absent": "record.missing_required_qualifier",
            "scalar": "record.invalid_value_kind",
            "dangling": "record.dangling_reference",
            "wrong_kind": "record.invalid_reference_kind",
        }[case]
        _assert_issue(candidate, code, "relation", field)


@pytest.mark.parametrize("field", ("Role", "context", "timestamp"))
def test_unknown_qualifiers(field: str) -> None:
    relation = _participates()
    relation = replace(
        relation, qualifiers=(*relation.qualifiers, Qualifier(field, "unexpected"))
    )
    _assert_issue(
        _candidate(_entity("Person"), _entity("Context"), relations=(relation,)),
        "record.unknown_qualifier",
        "relation",
        field,
    )


@pytest.mark.parametrize("same_value", (True, False))
def test_duplicate_property_names(same_value: bool) -> None:
    entity = _entity("Person")
    value = "Shared label" if same_value else "Different label"
    entity = replace(entity, properties=(*entity.properties, Property("label", value)))
    _assert_issue(_candidate(entity), "record.duplicate_property", "person", "label")


@pytest.mark.parametrize("same_value", (True, False))
def test_duplicate_qualifier_names(same_value: bool) -> None:
    relation = _participates()
    value = "Contributor" if same_value else "Lead"
    relation = replace(
        relation, qualifiers=(*relation.qualifiers, Qualifier("role", value))
    )
    _assert_issue(
        _candidate(_entity("Person"), _entity("Context"), relations=(relation,)),
        "record.duplicate_qualifier",
        "relation",
        "role",
    )


def test_reference_cannot_resolve_to_a_relation_record() -> None:
    proposition = _entity("Proposition")
    proposition = replace(
        proposition,
        properties=(
            *proposition.properties[:2],
            Property("context", EntityRef("relation")),
        ),
    )
    _assert_issue(
        _candidate(
            proposition,
            _entity("Person"),
            _entity("Context"),
            relations=(_participates(),),
        ),
        "record.dangling_reference",
        "proposition",
        "context",
    )


def test_invalid_records_are_not_repaired_or_reordered() -> None:
    candidate = _candidate(_entity("Person", " invalid "), relations=(_participates(),))
    before = repr(candidate)
    assert _local(candidate)
    assert repr(candidate) == before


@given(st.text())
def test_required_text_rule_for_arbitrary_unicode(value: str) -> None:
    entity = replace(_entity("Person"), properties=(Property("label", value),))
    diagnostics = _local(_candidate(entity))
    assert (diagnostics == ()) is any(not character.isspace() for character in value)
    if diagnostics:
        assert [item.code for item in diagnostics] == ["record.blank_required_text"]


@pytest.mark.parametrize("name", ("label", "content", "context"))
def test_duplicate_proposition_property_names(name: str) -> None:
    proposition = _entity("Proposition")
    item = next(item for item in proposition.properties if item.name == name)
    proposition = replace(proposition, properties=(*proposition.properties, item))
    _assert_issue(
        _candidate(proposition, _entity("Context")),
        "record.duplicate_property",
        "proposition",
        name,
    )


def test_duplicate_award_month_is_not_a_second_award() -> None:
    credential = _entity("Credential")
    item = Property("awarded_in", YearMonth(2026, 9))
    credential = replace(credential, properties=(*credential.properties, item, item))
    _assert_issue(
        _candidate(credential), "record.duplicate_property", "credential", "awarded_in"
    )


def test_duplicate_reference_qualifier_is_rejected() -> None:
    relation = _participates()
    item = Qualifier("organization", EntityRef("organization"))
    relation = replace(relation, qualifiers=(*relation.qualifiers, item, item))
    _assert_issue(
        _candidate(
            _entity("Person"),
            _entity("Context"),
            _entity("Organization"),
            relations=(relation,),
        ),
        "record.duplicate_qualifier",
        "relation",
        "organization",
    )
