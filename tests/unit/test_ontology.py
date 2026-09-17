"""Deterministic tests for ontology self-validation."""

from dataclasses import replace

from caron import ConceptDefinition, model4_ontology, validate_ontology


def test_model4_ontology_is_structurally_valid() -> None:
    assert validate_ontology(model4_ontology()) == ()


def test_duplicate_concept_definition_is_diagnosed() -> None:
    ontology = model4_ontology()
    malformed = replace(
        ontology,
        concepts=ontology.concepts + (ConceptDefinition(ontology.concepts[0].id),),
    )

    diagnostics = validate_ontology(malformed)

    assert "ontology.duplicate_concept" in {item.code for item in diagnostics}
