"""Regression checks for the renderer experiment."""

from pathlib import Path

from examples.cytoscape_html import (
    render_cytoscape_html,
    validated_realisation_to_cytoscape,
)
from examples.semantic_spine import build_candidate, validate_example


def test_adapter_preserves_long_entity_content() -> None:
    realisation = validate_example(build_candidate())

    graph = validated_realisation_to_cytoscape(realisation)
    nodes = graph["nodes"]
    assert isinstance(nodes, list)
    proposition = next(
        item for item in nodes if item["data"]["id"] == "proposition:rb90-discrepancy"
    )

    assert proposition["data"]["properties"] == [
        {
            "name": "content",
            "value": {
                "type": "text",
                "value": (
                    "The measured cascade intensity differs from evaluated data."
                ),
            },
        },
        {
            "name": "context",
            "value": {
                "type": "entity_reference",
                "entity_id": "context:phd",
                "label": "Nuclear-physics PhD",
                "kind": "Context",
            },
        },
    ]


def test_renderer_injects_data_and_removes_template_token(tmp_path: Path) -> None:
    output = tmp_path / "view.html"

    render_cytoscape_html(
        validate_example(build_candidate()),
        output,
    )

    html = output.read_text(encoding="utf-8")
    assert "__CARON_GRAPH_DATA__" not in html
    assert "proposition:rb90-discrepancy" in html
    assert "cytoscape({" in html
