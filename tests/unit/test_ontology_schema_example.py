"""Regression checks for the executable ontology-schema viewer."""

from pathlib import Path
from typing import Any

from caron import OntologySchema
from caron.ontology import career_ontology_v5_0
from examples.ontology_schema_html import (
    ontology_schema_to_cytoscape,
    render_ontology_schema_html,
)


def _ontology() -> OntologySchema:
    return career_ontology_v5_0()


def _graph_edges(ontology: OntologySchema) -> list[Any]:
    edges = ontology_schema_to_cytoscape(ontology)["edges"]
    assert isinstance(edges, list)
    return edges


def test_projection_contains_complete_v5_catalogue() -> None:
    ontology = _ontology()
    graph = ontology_schema_to_cytoscape(ontology)
    nodes = graph["nodes"]
    edges = graph["edges"]
    metadata = graph["metadata"]
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    assert isinstance(metadata, dict)

    assert {node["data"]["id"] for node in nodes} == {
        concept.id for concept in ontology.concepts
    }
    assert {
        (
            edge["data"]["kind"],
            edge["data"]["source"],
            edge["data"]["target"],
        )
        for edge in edges
    } == {
        (relation.kind, source_kind, target_kind)
        for relation in ontology.relations
        for source_kind in relation.source_kinds
        for target_kind in relation.target_kinds
    }
    assert metadata["concept_count"] == len(nodes) == 13
    assert metadata["relation_rule_count"] == len(ontology.relations) == 31
    assert metadata["expanded_edge_count"] == len(edges) == 41


def test_projection_assigns_appearances_to_new_concepts() -> None:
    graph = ontology_schema_to_cytoscape(_ontology())
    nodes = graph["nodes"]
    assert isinstance(nodes, list)
    appearances = {
        node["data"]["id"]: (node["data"]["color"], node["data"]["shape"])
        for node in nodes
        if node["data"]["id"] in {"Collective", "Language", "Credential"}
    }

    assert appearances == {
        "Collective": ("#a21caf", "ellipse"),
        "Language": ("#0891b2", "hexagon"),
        "Credential": ("#ca8a04", "diamond"),
    }


def test_projection_preserves_properties_qualifiers_and_requirements() -> None:
    ontology = _ontology()
    graph = ontology_schema_to_cytoscape(ontology)
    nodes = graph["nodes"]
    assert isinstance(nodes, list)

    context = next(node for node in nodes if node["data"]["id"] == "Context")
    assert context["data"]["properties"] == [
        {
            "name": "label",
            "value_kind": "text",
            "required": True,
            "allowed_reference_kinds": [],
        },
        {
            "name": "temporal_extent",
            "value_kind": "temporal_extent",
            "required": False,
            "allowed_reference_kinds": [],
        },
    ]

    credential = next(node for node in nodes if node["data"]["id"] == "Credential")
    assert credential["data"]["properties"][-1] == {
        "name": "awarded_in",
        "value_kind": "year_month",
        "required": False,
        "allowed_reference_kinds": [],
    }

    learns_language = next(
        edge
        for edge in _graph_edges(ontology)
        if edge["data"]["kind"] == "learns" and edge["data"]["target"] == "Language"
    )
    assert learns_language["data"]["source_kinds"] == ["Person"]
    assert learns_language["data"]["target_kinds"] == [
        "Language",
        "Method",
        "Subject",
        "Technology",
    ]
    assert learns_language["data"]["qualifiers"] == [
        {
            "name": "context",
            "value_kind": "entity_reference",
            "required": True,
            "allowed_reference_kinds": ["Context"],
        }
    ]

    performs = next(
        edge
        for edge in _graph_edges(ontology)
        if edge["data"]["kind"] == "performs" and edge["data"]["source"] == "Person"
    )
    assert performs["data"]["has_requirement"] is True
    assert performs["data"]["requirements"] == [
        {
            "concept": "Activity",
            "relation_kind": "performs",
            "endpoint": "target",
            "minimum": 1,
            "maximum": None,
            "display": "1..*",
        }
    ]

    requirements = graph["requirements"]
    assert isinstance(requirements, list)
    assert len(requirements) == 6
    evidenced_by = next(
        item for item in requirements if item["relation_kind"] == "evidenced_by"
    )
    assert evidenced_by["display"] == "0..*"


def test_projection_exposes_complete_global_invariant_inventory() -> None:
    graph = ontology_schema_to_cytoscape(_ontology())

    assert graph["invariants"] == [
        {"id": "record_identifier_lexical"},
        {"id": "required_text_non_blank"},
        {"id": "semantic_relation_fact_unique"},
        {"id": "part_of_acyclic"},
        {"id": "suborganization_of_acyclic"},
        {"id": "aims_at_locality"},
        {"id": "bears_on_roles_and_locality"},
        {"id": "temporal_consistency"},
    ]
    metadata = graph["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["requirement_count"] == 6
    assert metadata["invariant_count"] == 8


def test_renderer_displays_v5_schema_inventories_and_escapes_script_content(
    tmp_path: Path,
) -> None:
    output = tmp_path / "ontology.html"

    render_ontology_schema_html(
        _ontology(),
        output,
        title="Schema </script><script>alert(1)</script>",
    )

    html = output.read_text(encoding="utf-8")
    assert "__CARON_ONTOLOGY_DATA__" not in html
    assert '"projection":"executable_ontology_schema"' in html
    assert '"ontology_version":"5.0"' in html
    assert '"concept_count":13' in html
    assert '"relation_rule_count":31' in html
    assert '"expanded_edge_count":41' in html
    assert '"requirement_count":6' in html
    assert '"invariant_count":8' in html
    assert 'id="requirement-inventory"' in html
    assert 'id="invariant-inventory"' in html
    assert 'populateInventory("invariant-inventory"' in html
    assert "record_identifier_lexical" in html
    assert "\\u003c/script\\u003e" in html
    assert "cytoscape({" in html
