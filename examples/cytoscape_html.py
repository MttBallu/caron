"""Generate interactive Cytoscape.js viewers from semantic ``GraphView`` values.

The renderer stays under ``examples`` so that this interaction-layer
experiment does not become part of the public caron API prematurely.

Run from the project root with::

    uv run python -m examples.cytoscape_html
    uv run python -m examples.cytoscape_html --example two-contexts
    uv run python -m examples.cytoscape_html --example temporal-window
"""

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from caron import (
    Accepted,
    CoveredMonthResult,
    Entity,
    EntityRef,
    GraphView,
    KnownEnd,
    OngoingAsOf,
    QueryWitness,
    TemporalExtent,
    TemporalMatch,
    TemporalMatchMode,
    TemporalPredicateResult,
    TemporalWindow,
    UnknownEnd,
    YearMonth,
    select_activities_in_window,
    select_whole_realisation,
    validate_candidate,
)
from caron.entities import PropertyValue
from caron.ontology import career_ontology_v5_0
from examples.semantic_spine import build_candidate as build_semantic_spine_candidate
from examples.semantic_spine import validate_example
from examples.temporal_queries import build_candidate as build_temporal_candidate
from examples.two_contexts import build_candidate as build_two_contexts_candidate

_TEMPLATE_TOKEN = "__CARON_GRAPH_DATA__"
_DEFAULT_TEMPLATE = Path(__file__).with_name("cytoscape_template.html")

_KIND_APPEARANCE: dict[str, tuple[str, str]] = {
    "Person": ("#7c3aed", "ellipse"),
    "Collective": ("#a21caf", "ellipse"),
    "Context": ("#0369a1", "round-rectangle"),
    "Activity": ("#047857", "round-rectangle"),
    "Technology": ("#b45309", "hexagon"),
    "Method": ("#be123c", "diamond"),
    "Subject": ("#6d28d9", "tag"),
    "Language": ("#0891b2", "hexagon"),
    "Artifact": ("#475569", "rectangle"),
    "Proposition": ("#c2410c", "diamond"),
    "Organization": ("#0f766e", "round-rectangle"),
    "Place": ("#4338ca", "ellipse"),
    "Credential": ("#ca8a04", "diamond"),
    "ContextualRelation": ("#2563eb", "diamond"),
}


def _semantic_spine_view() -> GraphView[object]:
    return select_whole_realisation(validate_example(build_semantic_spine_candidate()))


def _two_contexts_view() -> GraphView[object]:
    return select_whole_realisation(validate_example(build_two_contexts_candidate()))


def _temporal_window_view() -> GraphView[object]:
    validation = validate_candidate(career_ontology_v5_0(), build_temporal_candidate())
    if not isinstance(validation, Accepted):
        details = "\n".join(
            f"- {item.code}: {item.message}" for item in validation.diagnostics
        )
        raise RuntimeError(f"The temporal example should be valid:\n{details}")
    return select_activities_in_window(
        validation.realisation,
        TemporalWindow.closed("2022-01", "2022-12"),
        mode=TemporalMatchMode.POSSIBLE,
    )


type ViewFactory = Callable[[], GraphView[object]]

_EXAMPLES: dict[str, tuple[ViewFactory, str, str]] = {
    "semantic-spine": (
        _semantic_spine_view,
        "Caron semantic-spine example",
        "career_graph.html",
    ),
    "two-contexts": (
        _two_contexts_view,
        "Caron Python across contexts example",
        "two_contexts_graph.html",
    ),
    "temporal-window": (
        _temporal_window_view,
        "Caron possible activities in 2022",
        "temporal_window_graph.html",
    ),
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
        case YearMonth() as month:
            return {"type": "year_month", "value": str(month)}
        case TemporalExtent(start=start, end=end):
            match end:
                case KnownEnd(month):
                    end_value: dict[str, object] = {
                        "kind": "known",
                        "month": str(month),
                    }
                    display = f"{start} — {month}"
                case UnknownEnd():
                    end_value = {"kind": "unknown"}
                    display = f"{start} — unknown"
                case OngoingAsOf(month):
                    end_value = {
                        "kind": "ongoing_as_of",
                        "as_of": str(month),
                    }
                    display = f"{start} — ongoing (as of {month})"
            return {
                "type": "temporal_extent",
                "start": str(start),
                "end": end_value,
                "display": display,
            }
    raise TypeError(f"Unsupported validated value: {value!r}")


def _cytoscape_witness(witness: QueryWitness) -> dict[str, object]:
    return {
        "entities": [item.entity_id for item in witness.entities],
        "relations": list(witness.relations),
        "properties": [
            {"entity_id": entity.entity_id, "name": name}
            for entity, name in witness.properties
        ],
    }


def _cytoscape_result(result: object) -> dict[str, object]:
    match result:
        case TemporalMatch(
            entity=entity, classification=classification, witness=witness
        ):
            return {
                "type": "temporal_match",
                "entity_id": entity.entity_id,
                "classification": classification.value,
                "witness": _cytoscape_witness(witness),
            }
        case TemporalPredicateResult(
            predicate=predicate,
            left=left,
            right=right,
            classification=classification,
            witness=witness,
        ):
            return {
                "type": "temporal_predicate",
                "predicate": predicate,
                "left_entity_id": left.entity_id,
                "right_entity_id": right.entity_id,
                "classification": classification.value,
                "witness": _cytoscape_witness(witness),
            }
        case CoveredMonthResult(
            context=context,
            kind=kind,
            minimum=minimum,
            maximum=maximum,
            as_of=as_of,
            witness=witness,
        ):
            return {
                "type": "covered_months",
                "context_id": context.entity_id,
                "kind": kind.value,
                "minimum": minimum,
                "maximum": maximum,
                "as_of": None if as_of is None else str(as_of),
                "witness": _cytoscape_witness(witness),
            }
    raise TypeError(f"Unsupported GraphView result: {result!r}")


def _result_entity_ids(result: object) -> tuple[str, ...]:
    match result:
        case TemporalMatch(entity=entity):
            return (entity.entity_id,)
        case TemporalPredicateResult(left=left, right=right):
            return (left.entity_id, right.entity_id)
        case CoveredMonthResult(context=context):
            return (context.entity_id,)
    return ()


def graph_view_to_cytoscape(
    view: GraphView[object],
    *,
    title: str = "Caron semantic-spine example",
) -> dict[str, object]:
    """Adapt a semantic query view to renderer-specific, JSON-compatible data."""

    entity_by_id = {entity.id: entity for entity in view.entities}
    serialized_results = tuple(_cytoscape_result(item) for item in view.results)
    results_by_entity = {
        entity_id: [
            serialized
            for result, serialized in zip(view.results, serialized_results, strict=True)
            if entity_id in _result_entity_ids(result)
        ]
        for entity_id in entity_by_id
    }
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    for entity in view.entities:
        color, shape = _KIND_APPEARANCE.get(entity.kind, ("#64748b", "ellipse"))
        entity_results = results_by_entity[entity.id]
        nodes.append(
            {
                "data": {
                    "id": entity.id,
                    "kind": entity.kind,
                    "label": _entity_label(entity),
                    "color": color,
                    "shape": shape,
                    "query_results": entity_results,
                    "query_classification": next(
                        (
                            item["classification"]
                            for item in entity_results
                            if item["type"] == "temporal_match"
                        ),
                        None,
                    ),
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

    for relation in view.relations:
        context_qualifier = next(
            (
                qualifier
                for qualifier in relation.qualifiers
                if qualifier.name == "context"
                and isinstance(qualifier.value, EntityRef)
            ),
            None,
        )
        if context_qualifier is not None:
            relation_node_id = f"view:contextual-relation:{relation.id}"
            color, shape = _KIND_APPEARANCE["ContextualRelation"]
            nodes.append(
                {
                    "data": {
                        "id": relation_node_id,
                        "kind": "ContextualRelation",
                        "label": relation.kind,
                        "color": color,
                        "shape": shape,
                        "properties": [
                            {
                                "name": "source",
                                "value": _cytoscape_value(
                                    relation.source,
                                    entity_by_id,
                                ),
                            },
                            {
                                "name": "target",
                                "value": _cytoscape_value(
                                    relation.target,
                                    entity_by_id,
                                ),
                            },
                            *[
                                {
                                    "name": item.name,
                                    "value": _cytoscape_value(
                                        item.value,
                                        entity_by_id,
                                    ),
                                }
                                for item in relation.qualifiers
                            ],
                        ],
                    }
                }
            )
            context_ref = context_qualifier.value
            assert isinstance(context_ref, EntityRef)
            for role, source, target, label in (
                (
                    "source",
                    relation.source.entity_id,
                    relation_node_id,
                    "source",
                ),
                (
                    "target",
                    relation_node_id,
                    relation.target.entity_id,
                    relation.kind,
                ),
                (
                    "context",
                    relation_node_id,
                    context_ref.entity_id,
                    "in context",
                ),
            ):
                edges.append(
                    {
                        "data": {
                            "id": f"{relation.id}:{role}",
                            "kind": relation.kind,
                            "label": label,
                            "source": source,
                            "target": target,
                            "qualifiers": [],
                            "semantic_relation_id": relation.id,
                            "view_role": role,
                        }
                    }
                )
            continue

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
            "realisation_id": view.source_realisation_id,
            "ontology_id": view.ontology.id,
            "ontology_version": view.ontology.version,
            "coverage": {
                "status": view.coverage.status.value,
                "scope": view.coverage.scope,
            },
            "query": {
                "name": view.query_name,
                "bindings": [
                    {
                        "name": binding.name,
                        "entity_id": binding.entity.entity_id,
                    }
                    for binding in view.bindings
                ],
                "results": list(serialized_results),
                "diagnostics": [
                    {
                        "code": item.code,
                        "layer": item.layer.value,
                        "message": item.message,
                        "severity": item.severity.value,
                        "record_id": item.record_id,
                        "field": item.field,
                    }
                    for item in view.diagnostics
                ],
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
    view: GraphView[object],
    output: Path,
    *,
    template: Path = _DEFAULT_TEMPLATE,
    title: str = "Caron semantic-spine example",
) -> None:
    """Render a browser viewer while keeping semantic values unchanged."""

    template_text = template.read_text(encoding="utf-8")
    if template_text.count(_TEMPLATE_TOKEN) != 1:
        raise ValueError(f"Template must contain {_TEMPLATE_TOKEN!r} exactly once")
    graph_data = graph_view_to_cytoscape(view, title=title)
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
        help="Example GraphView to render (default: semantic-spine)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="HTML destination (default: examples/<example>_graph.html)",
    )
    arguments = parser.parse_args()

    view_factory, title, default_filename = _EXAMPLES[arguments.example]
    output = arguments.output or Path(__file__).with_name(default_filename)
    render_cytoscape_html(view_factory(), output, title=title)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
