# caron

A typed career-ontology implementation in Python 3.12, managed with `uv`.

The maintained implementation provides explicit Model 4 and v0.5 ontology schemas, immutable entity and relation records, structured diagnostics, and a validation boundary from `RealisationCandidate` to `Accepted(ValidatedRealisation)` or `Rejected`. The v0.5 slice adds month-level context temporality, derived temporal queries, witnesses, and immutable `GraphView` results. Sources live directly in `caron/`.

[`CURRENT.md`](CURRENT.md) is the authority and version map for the maintained
baseline.

## Getting started

```bash
git clone https://github.com/MttBallu/caron.git
cd caron
uv sync --locked --all-groups
uv run python -m examples.semantic_spine
uv run python -m examples.temporal_queries
```

## Interactive examples

Generate the executable ontology-schema overview:

```bash
uv run python -m examples.ontology_schema_html
uv run python -m examples.ontology_schema_html --version 4
```

These commands render ontology versions `0.5` and `4`, respectively. The
interactive graph shows concept types as nodes and expands every relation rule
into its admissible source/target type pairs. Selecting a concept exposes its
properties and allowed relations; selecting an edge exposes the complete rule
signature, qualifiers, and cardinality requirements. The projection is derived
directly from `OntologySchema`, so it is both an overview and a check of the
actual executable vocabulary.

Generate realisation and query-result views:

```bash
uv run python -m examples.cytoscape_html
uv run python -m examples.cytoscape_html --example two-contexts
uv run python -m examples.cytoscape_html --example temporal-window
```

The first command generates `examples/career_graph.html`. The second generates `examples/two_contexts_graph.html`, where ALICE collision-data analysis during an MSc and synthetic-training-data construction during a PhD both use the same Python entity. Each activity has its own context, inputs, outputs, supporting technologies, and subject matter; no transfer edge is asserted. The third generates `examples/temporal_window_graph.html` from the possible activity matches in 2022. Generated graph files are ignored by Git; regenerate them locally when needed.

Open a generated file in a browser to explore the graph, inspect entities and relations, expand long properties, follow references, and filter entity or relation kinds. The viewer loads Cytoscape.js 3.34.1 from jsDelivr, so an internet connection is required when opening it.

The realisation adapter consumes query-produced `GraphView` values rather than `ValidatedRealisation`. This is distinct from the schema viewer, which consumes `OntologySchema` and displays admissible rules rather than asserted career facts. `select_whole_realisation` supplies the two complete-example views while retaining their explicit coverage, and the temporal example supplies a selected subgraph with typed results and witnesses. `TemporalExtent` values are serialized as structured renderer data, temporal matches are available in the inspector, and possible matches use a dashed visual treatment. Relations with a context qualifier, such as `learns`, are rendered as relation-occurrence nodes connected to their source, target, and context so their n-ary meaning is not hidden.

The temporal example validates the ALICE, PhD synthetic-data, and `jax-geopro` contexts, derives exact and bounded covered-month results, establishes the contextual ordering of three Python activities, and returns possible matches for a 2022 window:

```bash
uv run python -m examples.temporal_queries
```

## Checks

```bash
uv run --locked --all-groups python tools/verify.py
```

This single reproducibility gate runs formatting, linting, strict typing, the
deterministic and Hypothesis suites, both executable examples, all three
realisation-view generations, both ontology-schema versions, and distribution
builds. GitHub Actions runs the same command on pushes to `main` and on pull
requests.

## Scope and next increments

The temporal extension is specified by the [temporal extent contract](docs/career-model-v0.5-temporal-contract.md) and exercised in the [temporal instantiation experiment](docs/career-model-v0.5-temporal-instantiation-experiment.md). The implemented query surface intentionally remains small: `covered_months`, `before`, `overlaps`, `select_activities_in_window`, and the renderer-supporting `select_whole_realisation`.

The proposed [Career Ontology 5.0 specification](docs/career-ontology-v5.0-specification.md)
integrates the complete adopted Model 4.2 vocabulary with those temporal
semantics and the accepted M1-B decisions. It is a specification candidate,
not an executable schema in the current `caron` `0.1.0` package.

The private witness-carrying algebra preserves the accepted join, left-join,
union, extension, property-lookup, projection, and ordering regressions. It is
not a public plan language; schema-aware plan validation and stable named query
contracts remain deferred.

Durable semantic serialization, storage, CLI behavior, activity extents,
temporal relation qualifiers, period controls, chronological timelines, and a
complete interval algebra also remain deferred. The current Cytoscape JSON is
an interaction-layer projection rather than a persistence format or semantic
codec.

See also the [implementation overview](career-ontology-package-skeleton.md), [package boundaries](docs/career-ontology-package-boundaries.md), and [entity representation notes](docs/career-ontology-entity-representation-pseudocode.md).
