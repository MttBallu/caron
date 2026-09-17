# caron

A typed career-ontology implementation in Python 3.12, managed with `uv`.

The first maintained implementation provides an explicit Model 4 ontology,
immutable entity and relation records, structured diagnostics, and a validation
boundary from `RealisationCandidate` to `Accepted(ValidatedRealisation)` or
`Rejected`. Sources live directly in `caron/`.

## Getting started

```bash
git clone https://github.com/MttBallu/caron.git
cd caron
uv sync --locked --all-groups
uv run python -m examples.semantic_spine
```

## Interactive examples

```bash
uv run python -m examples.cytoscape_html
uv run python -m examples.cytoscape_html --example two-contexts
```

The first command generates `examples/career_graph.html`. The second generates
`examples/two_contexts_graph.html`, where ALICE collision-data analysis during
an MSc and synthetic-training-data construction during a PhD both use the same
Python entity. Each activity has its own context, inputs, outputs, supporting
technologies, and subject matter; no transfer edge is asserted. Generated graph
files are ignored by Git; regenerate them locally when needed.

Open either file in a browser to explore the graph, inspect entities and
relations, expand long properties, follow references, and filter entity or
relation kinds. The viewer loads Cytoscape.js 3.34.1 from jsDelivr, so an
internet connection is required when opening it.

The experimental adapter currently consumes `ValidatedRealisation`. Relations
with a context qualifier, such as `learns`, are rendered as relation-occurrence
nodes connected to their source, target, and context so their n-ary meaning is
not hidden. The adapter lives under `examples/` and will accept `GraphView` once
retrieval is implemented.

## Checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy caron tests examples
uv run pytest
uv run python -m examples.semantic_spine
uv run python -m examples.cytoscape_html
uv run python -m examples.cytoscape_html --example two-contexts
uv build
```

GitHub Actions runs these checks on pushes to `main` and on pull requests.
The tests include deterministic pytest cases and Hypothesis invariant tests.

## Scope and next increment

Retrieval, `GraphView`, serialization, storage, and CLI behavior remain deferred.
The next increment is one typed `ActivitiesInContext` retrieval with bindings,
witnesses, coverage, diagnostics, and an immutable `GraphView`.

See the [implementation overview](career-ontology-package-skeleton.md),
[package boundaries](docs/career-ontology-package-boundaries.md), and
[entity representation notes](docs/career-ontology-entity-representation-pseudocode.md).
