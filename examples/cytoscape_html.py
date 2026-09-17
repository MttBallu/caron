"""Generate interactive Cytoscape.js viewers for the maintained examples.

``ValidatedRealisation`` is used as a temporary renderer input because the
query engine and ``GraphView`` do not exist yet. The renderer stays under
``examples`` so that this experiment does not become part of the public caron
API prematurely.

Run from the project root with::

    uv run python -m examples.cytoscape_html
    uv run python -m examples.cytoscape_html --example two-contexts
"""

import argparse
import json
from pathlib import Path

from caron import Entity, EntityRef, ValidatedRealisation
from caron.entities import PropertyValue
from examples.semantic_spine import build_candidate as build_semantic_spine_candidate
from examples.semantic_spine import validate_example
from examples.two_contexts import build_candidate as build_two_contexts_candidate

_TEMPLATE_TOKEN = "__CARON_GRAPH_DATA__"
_DEFAULT_TEMPLATE = Path(__file__).with_name("cytoscape_template.html")

_EXAMPLES = {
    "semantic-spine": (
        build_semantic_spine_candidate,
        "Caron semantic-spine example",
        "career_graph.html",
    ),
    "two-contexts": (
        build_two_contexts_candidate,
        "Caron two-context example",
        "two_contexts_graph.html",
    ),
}

_KIND_APPEARANCE: dict[str, tuple[str, str]] = {
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


def _entity_label(entity: Entity) -> str:
    label = entity.property("label")
    return label if isinstance(label, str) else entity.id


def _cytoscape_value(
    value: PropertyValue,
    entity_by_id: dict[str, Entity],
) -> dict[str, object]:
    match value:
        case EntityRef(entity_id=entity_id):
            referenced = entity_by_id[entity_id]
            return {
                "type": "entity_reference",
                "entity_id": entity_id,
                "label": _entity_label(referenced),
                "kind": referenced.kind,
            }
        case str() as text:
            return {"type": "text", "value": text}
        case int() as integer:
            return {"type": "integer", "value": integer}
    raise TypeError(f"Unsupported validated value: {value!r}")


def validated_realisation_to_cytoscape(
    realisation: ValidatedRealisation,
    *,
    title: str = "Caron semantic-spine example",
) -> dict[str, object]:
    """Adapt a validated value to renderer-specific, JSON-compatible data."""

    entity_by_id = {entity.id: entity for entity in realisation.entities}
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    for entity in realisation.entities:
        color, shape = _KIND_APPEARANCE.get(entity.kind, ("#64748b", "ellipse"))
        nodes.append(
            {
                "data": {
                    "id": entity.id,
                    "kind": entity.kind,
                    "label": _entity_label(entity),
                    "color": color,
                    "shape": shape,
                    "properties": [
                        {
                            "name": item.name,
                            "value": _cytoscape_value(item.value, entity_by_id),
                        }
                        for item in entity.properties
                        if item.name != "label"
                    ],
                }
            }
        )

    for relation in realisation.relations:
        edges.append(
            {
                "data": {
                    "id": relation.id,
                    "kind": relation.kind,
                    "label": relation.kind,
                    "source": relation.source.entity_id,
                    "target": relation.target.entity_id,
                    "qualifiers": [
                        {
                            "name": item.name,
                            "value": _cytoscape_value(item.value, entity_by_id),
                        }
                        for item in relation.qualifiers
                    ],
                }
            }
        )

    return {
        "metadata": {
            "title": title,
            "realisation_id": realisation.id,
            "ontology_id": realisation.ontology.id,
            "ontology_version": realisation.ontology.version,
            "coverage": {
                "status": realisation.coverage.status.value,
                "scope": realisation.coverage.scope,
            },
        },
        "nodes": nodes,
        "edges": edges,
    }


def _script_safe_json(value: object) -> str:
    """Serialize JSON without allowing data to terminate the script element."""

    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_cytoscape_html(
    realisation: ValidatedRealisation,
    output: Path,
    *,
    template: Path = _DEFAULT_TEMPLATE,
    title: str = "Caron semantic-spine example",
) -> None:
    """Render a browser viewer while keeping semantic values unchanged."""

    template_text = template.read_text(encoding="utf-8")
    if template_text.count(_TEMPLATE_TOKEN) != 1:
        raise ValueError(f"Template must contain {_TEMPLATE_TOKEN!r} exactly once")
    graph_data = validated_realisation_to_cytoscape(realisation, title=title)
    rendered = template_text.replace(_TEMPLATE_TOKEN, _script_safe_json(graph_data))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an interactive caron Cytoscape.js example."
    )
    parser.add_argument(
        "--example",
        choices=tuple(_EXAMPLES),
        default="semantic-spine",
        help="Example realisation to render (default: semantic-spine)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="HTML destination (default: examples/<example>_graph.html)",
    )
    arguments = parser.parse_args()

    candidate_factory, title, default_filename = _EXAMPLES[arguments.example]
    output = arguments.output or Path(__file__).with_name(default_filename)
    realisation = validate_example(candidate_factory())
    render_cytoscape_html(realisation, output, title=title)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
