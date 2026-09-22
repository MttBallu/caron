"""Deterministic tests for ontology self-validation."""

from dataclasses import replace

import caron
import caron.ontology as ontology_module
from caron import ConceptDefinition, career_ontology_v5_0, validate_ontology

EXPECTED_ROOT_PUBLIC_API = frozenset(
    {
        "ACTIVITY",
        "ARTIFACT",
        "COLLECTIVE",
        "CONTEXT",
        "CREDENTIAL",
        "LANGUAGE",
        "METHOD",
        "ORGANIZATION",
        "PERSON",
        "PLACE",
        "PROPOSITION",
        "SUBJECT",
        "TECHNOLOGY",
        "Accepted",
        "ConceptDefinition",
        "CoveredMonthKind",
        "CoveredMonthResult",
        "Coverage",
        "CoverageStatus",
        "Diagnostic",
        "DiagnosticLayer",
        "EndpointPosition",
        "Entity",
        "EntityRef",
        "GraphView",
        "InvariantDefinition",
        "KnownEnd",
        "OntologySchema",
        "OngoingAsOf",
        "Property",
        "PropertyDefinition",
        "Qualifier",
        "QualifierDefinition",
        "QueryBinding",
        "QueryWitness",
        "RealisationCandidate",
        "Rejected",
        "RelationAssertion",
        "RelationDefinition",
        "RelationRequirement",
        "Severity",
        "TemporalClassification",
        "TemporalEnd",
        "TemporalExtent",
        "TemporalMatch",
        "TemporalMatchMode",
        "TemporalPredicateResult",
        "TemporalWindow",
        "UnknownEnd",
        "ValidatedRealisation",
        "ValidationResult",
        "ValueKind",
        "YearMonth",
        "before",
        "career_ontology_v5_0",
        "covered_months",
        "overlaps",
        "select_activities_in_window",
        "select_whole_realisation",
        "validate_candidate",
        "validate_ontology",
    }
)


def test_maintained_ontology_is_structurally_valid() -> None:
    assert validate_ontology(career_ontology_v5_0()) == ()


def test_duplicate_concept_definition_is_diagnosed() -> None:
    ontology = career_ontology_v5_0()
    malformed = replace(
        ontology,
        concepts=ontology.concepts + (ConceptDefinition(ontology.concepts[0].id),),
    )

    diagnostics = validate_ontology(malformed)

    assert "ontology.duplicate_concept" in {item.code for item in diagnostics}


def test_legacy_executable_schema_surface_is_absent() -> None:
    for name in ("model4_ontology", "model_v0_5_ontology", "ALL_CONCEPTS"):
        assert not hasattr(caron, name)
        assert not hasattr(ontology_module, name)

    assert not hasattr(ontology_module, "_career_ontology_v5_0_development")


def test_root_public_api_is_the_reviewed_semantic_surface() -> None:
    assert len(caron.__all__) == len(set(caron.__all__))
    assert set(caron.__all__) == EXPECTED_ROOT_PUBLIC_API
    assert caron.career_ontology_v5_0 is career_ontology_v5_0
