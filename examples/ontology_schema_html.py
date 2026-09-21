"""Generate an interactive graph of executable ontology schema rules.

This viewer is deliberately separate from the realisation-level ``GraphView``
renderer. It projects an ``OntologySchema``: concept nodes show admissible
properties, and relation edges show every allowed source/target kind pair.

Run from the project root with::

    uv run python -m examples.ontology_schema_html
    uv run python -m examples.ontology_schema_html --version 4
"""

import argparse
import json
from pathlib import Path

from caron import (
    OntologySchema,
    PropertyDefinition,
    QualifierDefinition,
    RelationRequirement,
    model4_ontology,
    model_v0_5_ontology,
)

_TEMPLATE_TOKEN = "__CARON_ONTOLOGY_DATA__"
_DEFAULT_TEMPLATE = Path(__file__).with_name("ontology_schema_template.html")

_CONCEPT_APPEARANCE: dict[str, tuple[str, str]] = {
    "Person": ("#7c3aed", "ellipse"),
    "Context": ("#0369a1", "round-rectangle"),
    "Activity": ("#047857", "round-rectangle"),
    "Technology": ("#b45309", "hexagon"),
    "Method": ("#be123c", "diamond"),
    "Subject": ("#6d28d9", "tag"),
    "Artifact": ("#475569", "rectangle"),
    "Proposition": ("#c2410c", "diamond"),
    "Organization": ("#0f766e", "round-rectangle"),
    "Place": ("#4338ca", "ellipse"),
}


def _field_definition(
    field: PropertyDefinition | QualifierDefinition,
) -> dict[str, object]:
    return {
        "name": field.name,
        "value_kind": field.value_kind.value,
        "required": field.required,
        "allowed_reference_kinds": sorted(field.allowed_reference_kinds),
    }


def _requirement_data(requirement: RelationRequirement) -> dict[str, object]:
    maximum = requirement.maximum
    return {
        "concept": requirement.concept,
        "relation_kind": requirement.relation_kind,
        "endpoint": requirement.endpoint.value,
        "minimum": requirement.minimum,
        "maximum": maximum,
        "display": f"{requirement.minimum}..{'*' if maximum is None else maximum}",
    }


def ontology_schema_to_cytoscape(
    ontology: OntologySchema,
    *,
    title: str | None = None,
) -> dict[str, object]:
    """Project executable schema rules to renderer-specific Cytoscape data.

    One edge is emitted for every admissible source-kind/target-kind pair. The
    edge retains the complete relation signature so that a union endpoint is
    visible as one rule expanded into several graph edges, rather than being
    mistaken for several ontology relations.
    """

    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    for concept in ontology.concepts:
        color, shape = _CONCEPT_APPEARANCE.get(
            concept.id, ("#64748b", "round-rectangle")
        )
        nodes.append(
            {
                "data": {
                    "id": concept.id,
                    "kind": concept.id,
                    "label": concept.id,
                    "color": color,
                    "shape": shape,
                    "properties": [
                        _field_definition(property_definition)
                        for property_definition in concept.properties
                    ],
                }
            }
        )

    for relation in ontology.relations:
        source_kinds = sorted(relation.source_kinds)
        target_kinds = sorted(relation.target_kinds)
        expanded_pairs = [
            (source_kind, target_kind)
            for source_kind in source_kinds
            for target_kind in target_kinds
        ]
        for pair_index, (source_kind, target_kind) in enumerate(
            expanded_pairs, start=1
        ):
            requirements = [
                _requirement_data(requirement)
                for requirement in ontology.requirements
                if requirement.relation_kind == relation.kind
                and (
                    (
                        requirement.endpoint.value == "source"
                        and requirement.concept == source_kind
                    )
                    or (
                        requirement.endpoint.value == "target"
                        and requirement.concept == target_kind
                    )
                )
            ]
            edges.append(
                {
                    "data": {
                        "id": (f"rule:{relation.kind}:{source_kind}:{target_kind}"),
                        "kind": relation.kind,
                        "label": relation.kind,
                        "source": source_kind,
                        "target": target_kind,
                        "source_kinds": source_kinds,
                        "target_kinds": target_kinds,
                        "qualifiers": [
                            _field_definition(qualifier)
                            for qualifier in relation.qualifiers
                        ],
                        "requirements": requirements,
                        "has_requirement": bool(requirements),
                        "expansion_index": pair_index,
                        "expansion_count": len(expanded_pairs),
                    }
                }
            )

    return {
        "metadata": {
            "title": title or f"Caron ontology {ontology.version}",
            "ontology_id": ontology.id,
            "ontology_version": ontology.version,
            "concept_count": len(ontology.concepts),
            "relation_rule_count": len(ontology.relations),
            "expanded_edge_count": len(edges),
            "requirement_count": len(ontology.requirements),
            "projection": "executable_ontology_schema",
        },
        "nodes": nodes,
        "edges": edges,
        "requirements": [
            _requirement_data(requirement) for requirement in ontology.requirements
        ],
    }


def _script_safe_json(value: object) -> str:
    """Serialize JSON without allowing data to terminate the script element."""

    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_ontology_schema_html(
    ontology: OntologySchema,
    output: Path,
    *,
    template: Path = _DEFAULT_TEMPLATE,
    title: str | None = None,
) -> None:
    """Render an interactive schema viewer from one executable ontology."""

    template_text = template.read_text(encoding="utf-8")
    if template_text.count(_TEMPLATE_TOKEN) != 1:
        raise ValueError(f"Template must contain {_TEMPLATE_TOKEN!r} exactly once")
    graph_data = ontology_schema_to_cytoscape(ontology, title=title)
    rendered = template_text.replace(_TEMPLATE_TOKEN, _script_safe_json(graph_data))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def _ontology_for_version(version: str) -> OntologySchema:
    if version == "4":
        return model4_ontology()
    if version == "0.5":
        return model_v0_5_ontology()
    raise ValueError(f"Unsupported ontology version: {version}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an interactive graph of executable ontology rules."
    )
    parser.add_argument(
        "--version",
        choices=("4", "0.5"),
        default="0.5",
        help="Executable ontology version to render (default: 0.5)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="HTML destination (default: examples/ontology_<version>_graph.html)",
    )
    arguments = parser.parse_args()

    ontology = _ontology_for_version(arguments.version)
    safe_version = ontology.version.replace(".", "_")
    output = arguments.output or Path(__file__).with_name(
        f"ontology_{safe_version}_graph.html"
    )
    render_ontology_schema_html(ontology, output)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
