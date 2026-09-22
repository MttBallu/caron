"""Exact catalogue checks against the accepted 5.0 specification.

Expected signatures below are transcribed independently from specification
sections 7–10, not generated from the executable schema. These tests check
schema data; candidate conformance awaits the remaining Phase 4 handlers.
"""

from dataclasses import replace

import pytest

import caron
from caron import (
    COLLECTIVE,
    CREDENTIAL,
    LANGUAGE,
    OntologySchema,
    PropertyDefinition,
    QualifierDefinition,
    Rejected,
    validate_candidate,
    validate_ontology,
)
from caron.ontology import career_ontology_v5_0
from tests.fixtures.v5 import minimal_v5_candidate

type FieldSignature = tuple[str, str, bool, tuple[str, ...]]
type RelationSignature = tuple[
    tuple[str, ...], tuple[str, ...], tuple[FieldSignature, ...]
]

EXPECTED_CONCEPTS = (
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
LABEL: FieldSignature = ("label", "text", True, ())
EXTRA_PROPERTIES: dict[str, tuple[FieldSignature, ...]] = {
    "Context": (("temporal_extent", "temporal_extent", False, ()),),
    "Proposition": (
        ("content", "text", True, ()),
        ("context", "entity_reference", True, ("Context",)),
    ),
    "Credential": (("awarded_in", "year_month", False, ()),),
}
ROLE: FieldSignature = ("role", "text", True, ())
CONTEXT_QUALIFIER: FieldSignature = ("context", "entity_reference", True, ("Context",))
ORGANIZATION_QUALIFIER: FieldSignature = (
    "organization",
    "entity_reference",
    False,
    ("Organization",),
)

# Explicit endpoint unions keep the expected signatures independent of schema
# family constants. Qualifiers omitted by the specification must stay absent.
EXPECTED_RELATIONS: dict[str, RelationSignature] = {
    "part_of": (("Context",), ("Context",), ()),
    "suborganization_of": (("Organization",), ("Organization",), ()),
    "performs": (("Person", "Collective"), ("Activity",), ()),
    "occurs_in": (("Activity",), ("Context",), ()),
    "participates_in": (
        ("Person", "Collective"),
        ("Context",),
        (ROLE, ORGANIZATION_QUALIFIER),
    ),
    "collective_membership": (("Person",), ("Collective",), (CONTEXT_QUALIFIER, ROLE)),
    "organization_association": (("Organization",), ("Context",), (ROLE,)),
    "occurs_at": (("Context",), ("Place",), ()),
    "exposed_to": (
        ("Person",),
        ("Technology", "Method", "Subject", "Language"),
        (CONTEXT_QUALIFIER,),
    ),
    "learns": (
        ("Person",),
        ("Technology", "Method", "Subject", "Language"),
        (CONTEXT_QUALIFIER,),
    ),
    "uses_technology": (("Activity",), ("Technology",), ()),
    "uses_artifact": (("Activity",), ("Artifact",), ()),
    "uses_language": (("Activity",), ("Language",), ()),
    "applies": (("Activity",), ("Method",), ()),
    "draws_on": (("Activity",), ("Method", "Subject"), ()),
    "native_language": (("Person",), ("Language",), ()),
    "takes_input": (("Activity",), ("Artifact",), ()),
    "produces": (("Activity",), ("Artifact",), ()),
    "modifies": (("Activity",), ("Artifact",), ()),
    "awarded_to": (("Credential",), ("Person",), ()),
    "awarded_by": (("Credential",), ("Organization",), ()),
    "obtained_through": (("Credential",), ("Context",), ()),
    "evidenced_by": (("Credential",), ("Artifact",), ()),
    "aims_at": (("Context",), ("Proposition",), ()),
    "addresses": (("Activity",), ("Proposition",), ()),
    "motivates": (("Proposition",), ("Activity", "Context"), ()),
    "results_in": (("Activity",), ("Proposition",), ()),
    "establishes": (("Activity",), ("Proposition",), ()),
    "supports": (("Activity",), ("Proposition",), ()),
    "contradicts": (("Activity",), ("Proposition",), ()),
    "bears_on": (("Proposition",), ("Proposition",), ()),
}

EXPECTED_INVARIANTS = frozenset(
    {
        "record_identifier_lexical",
        "required_text_non_blank",
        "semantic_relation_fact_unique",
        "part_of_acyclic",
        "suborganization_of_acyclic",
        "aims_at_locality",
        "bears_on_roles_and_locality",
        "temporal_consistency",
    }
)


@pytest.fixture
def schema() -> OntologySchema:
    return career_ontology_v5_0()


def _field_signature(
    field: PropertyDefinition | QualifierDefinition,
) -> FieldSignature:
    return (
        field.name,
        field.value_kind.value,
        field.required,
        tuple(sorted(field.allowed_reference_kinds)),
    )


def test_catalogue_has_exact_accepted_identity(schema: OntologySchema) -> None:
    assert schema.id == "caron.career-model"
    assert schema.version == "5.0"
    assert schema == career_ontology_v5_0()


def test_new_concept_constants_and_v5_factory_are_public() -> None:
    assert (COLLECTIVE, LANGUAGE, CREDENTIAL) == (
        "Collective",
        "Language",
        "Credential",
    )
    assert {
        "COLLECTIVE",
        "LANGUAGE",
        "CREDENTIAL",
        "career_ontology_v5_0",
    } <= set(caron.__all__)
    assert caron.career_ontology_v5_0 is career_ontology_v5_0


def test_concept_inventory_is_exact(schema: OntologySchema) -> None:
    assert len(schema.concepts) == 13
    assert {concept.id for concept in schema.concepts} == set(EXPECTED_CONCEPTS)


@pytest.mark.parametrize("kind", EXPECTED_CONCEPTS)
def test_every_property_signature_is_exact(schema: OntologySchema, kind: str) -> None:
    concept = schema.concept(kind)
    assert concept is not None
    expected = (LABEL, *EXTRA_PROPERTIES.get(kind, ()))
    assert len(concept.properties) == len(expected)
    assert {_field_signature(field) for field in concept.properties} == set(expected)


@pytest.mark.parametrize("family", ("Agent", "Learnable", "IntellectualResource"))
def test_endpoint_families_are_not_concepts(
    schema: OntologySchema, family: str
) -> None:
    assert schema.concept(family) is None
    assert all(
        family not in relation.source_kinds | relation.target_kinds
        for relation in schema.relations
    )


def test_relation_inventory_is_exact(schema: OntologySchema) -> None:
    assert len(schema.relations) == 31
    assert {relation.kind for relation in schema.relations} == set(EXPECTED_RELATIONS)


@pytest.mark.parametrize("kind", EXPECTED_RELATIONS)
def test_every_relation_signature_is_exact(schema: OntologySchema, kind: str) -> None:
    relation = schema.relation(kind)
    assert relation is not None
    sources, targets, qualifiers = EXPECTED_RELATIONS[kind]
    assert relation.source_kinds == frozenset(sources)
    assert relation.target_kinds == frozenset(targets)
    assert len(relation.qualifiers) == len(qualifiers)
    assert {_field_signature(field) for field in relation.qualifiers} == set(qualifiers)


def test_expanded_endpoint_pairs_cover_exactly_41_edges(schema: OntologySchema) -> None:
    pairs = {
        (relation.kind, source, target)
        for relation in schema.relations
        for source in relation.source_kinds
        for target in relation.target_kinds
    }
    expected = {
        (kind, source, target)
        for kind, (sources, targets, _) in EXPECTED_RELATIONS.items()
        for source in sources
        for target in targets
    }
    assert len(pairs) == 41
    assert pairs == expected


def test_cardinality_declarations_are_exact(schema: OntologySchema) -> None:
    assert len(schema.requirements) == 6
    assert {
        (
            rule.concept,
            rule.relation_kind,
            rule.endpoint.value,
            rule.minimum,
            rule.maximum,
        )
        for rule in schema.requirements
    } == {
        ("Activity", "performs", "target", 1, None),
        ("Activity", "occurs_in", "source", 1, 1),
        ("Credential", "awarded_to", "source", 1, 1),
        ("Credential", "awarded_by", "source", 1, None),
        ("Credential", "obtained_through", "source", 1, None),
        ("Credential", "evidenced_by", "source", 0, None),
    }


def test_invariant_declarations_are_complete(schema: OntologySchema) -> None:
    assert len(schema.invariants) == 8
    assert {invariant.id for invariant in schema.invariants} == EXPECTED_INVARIANTS


@pytest.mark.parametrize(
    "kind",
    ("uses", "associated_with", "maintains", "before", "overlaps", "covered_months"),
)
def test_legacy_and_derived_relations_are_absent(
    schema: OntologySchema, kind: str
) -> None:
    assert schema.relation(kind) is None


@pytest.mark.parametrize(
    "kind", ("Skill", "Experience", "Ability", "Capability", "Transfer")
)
def test_interpretive_concepts_are_absent(schema: OntologySchema, kind: str) -> None:
    assert schema.concept(kind) is None


def test_complete_schema_passes_self_validation(
    schema: OntologySchema,
) -> None:
    assert validate_ontology(schema) == ()


@pytest.mark.parametrize("version", ("4", "0.5", "5.0-dev", "5.1"))
def test_exact_version_mismatch_prevents_candidate_acceptance(
    schema: OntologySchema, version: str
) -> None:
    candidate = replace(minimal_v5_candidate(), ontology_version=version)
    result = validate_candidate(schema, candidate)

    assert isinstance(result, Rejected)
    assert [item.code for item in result.diagnostics] == [
        "realisation.ontology_version_mismatch"
    ]


def test_conforming_candidate_can_be_accepted(
    schema: OntologySchema,
) -> None:
    assert isinstance(
        validate_candidate(schema, minimal_v5_candidate()), caron.Accepted
    )
