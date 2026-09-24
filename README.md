# caron

A typed career-ontology implementation in Python 3.12, managed with `uv`.
Package version `0.2.0` implements the accepted exact ontology identity
`caron.career-model` / `5.0`.

The maintained implementation provides the public `career_ontology_v5_0()`
schema factory, immutable entity and relation records, structured diagnostics,
and a validation boundary from `RealisationCandidate` to
`Accepted(ValidatedRealisation)` or `Rejected`. It includes month-level context
temporality, derived temporal queries, witnesses, and immutable `GraphView`
results. Earlier executable versions `4` and `0.5` have been removed after
their retained behavior was ported; they remain available through the design
documents and Git history. Sources live directly in `caron/`.

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

## Read an internal realisation fixture

`caron.yaml_reader` reads one package-maintained UTF-8 YAML file in format `"0.1"` against the exact executable ontology `5.0`. A small test-only example is in
[`tests/fixtures/geant4-learning-and-activity-v0.1.yaml`](tests/fixtures/geant4-learning-and-activity-v0.1.yaml).

```python
from caron import career_ontology_v5_0
from caron.yaml_reader import LoadAccepted, load_realisation_yaml

result = load_realisation_yaml(
    "tests/fixtures/geant4-learning-and-activity-v0.1.yaml",
    ontology=career_ontology_v5_0(),
)
if isinstance(result, LoadAccepted):
    graph = result.realisation
else:
    for finding in result.findings:
        print(finding.code, finding.location, finding.message)
```

The reader checks file access and YAML structure, binds explicit value tags,
then calls the existing `validate_candidate` function. It returns a validated
graph only on acceptance. Rejections keep the validator's semantic codes and
add source locations when possible. `source_state_id` is a SHA-256 hash of the
exact bytes read; it is separate from the authored realisation ID. The root
semantic API and direct in-memory validation do not depend on YAML. This is a
read-only internal file profile; no writer or canonical storage format is defined.

The [larger career realisation](caron/data/career-across-contexts-v0.1.yaml) ships inside the package. Internal code can load it without knowing the installation path:

```python
from caron._bundled_realisation import load_bundled_career_realisation
from caron.yaml_reader import LoadAccepted

result = load_bundled_career_realisation()
if isinstance(result, LoadAccepted):
    graph = result.realisation
```

This file exercises shared Python and GEANT4 identities, an internship with two parent contexts, PhD research strands, propositions, a credential, and a later software project. Its `selective` coverage records that this is a broad test of loading and querying, not an exhaustive claim about the career. It is package-maintained data, not an interactive editing format. A header comment names the working career reference and maintained examples that informed the file; it is a review aid, not per-assertion provenance. Git records edits, while semantic validation checks the graph. Neither replaces a later source-truth policy if the project needs one.

Unquoted scalars have a controlled grammar: lowercase `true`, `false`, `null`,
base-ten integers, and decimal or scientific-notation floats are decoded as
their respective types; other unquoted scalars are text, except timestamps and
non-finite numbers, which are rejected. Quote strings that resemble numbers or
Booleans.

## Interactive examples

Generate the executable ontology-schema overview:

```bash
uv run python -m examples.ontology_schema_html
```

This command renders exact ontology `5.0`. The
interactive graph shows its 13 concept types as nodes and expands all 31
relation rules into 41 admissible source/target type pairs. Selecting a concept
exposes its properties and allowed relations; selecting an edge exposes the
complete rule signature and qualifiers. The sidebar inventories all six
cardinality requirements and eight global invariants. The projection is
derived directly from `OntologySchema`, so it is both an overview and a check
of the actual executable vocabulary.

Generate realisation and query-result views:

```bash
uv run python -m examples.cytoscape_html
uv run python -m examples.cytoscape_html --example two-contexts
uv run python -m examples.cytoscape_html --example temporal-window
```

The first command generates `examples/career_graph.html`. The second generates `examples/two_contexts_graph.html`, where ALICE collision-data analysis during an MSc and synthetic-training-data construction during a PhD both use the same Python entity. Each activity has its own context, inputs, outputs, supporting technologies, and subject matter; no transfer edge is asserted. The third generates `examples/temporal_window_graph.html` from the possible activity matches in 2022. Generated graph files are ignored by Git; regenerate them locally when needed.

Open a generated file in a browser to explore the graph, inspect entities and
relations, expand long properties, follow references, and filter entity or
relation kinds. The representative career graph includes Collective, Language,
and Credential entities, including a typed award month. The viewer loads
Cytoscape.js 3.34.1 from jsDelivr, so an internet connection is required when
opening it.

The realisation adapter consumes query-produced `GraphView` values rather than
`ValidatedRealisation`. This is distinct from the schema viewer, which consumes
`OntologySchema` and displays admissible rules rather than asserted career
facts. `select_whole_realisation` supplies the two complete-example views while
retaining their explicit coverage, and the temporal example supplies a
selected subgraph with typed results and witnesses. `YearMonth` and
`TemporalExtent` values are serialized as structured renderer data, temporal
matches and their witnesses are available in the inspector, and possible
matches use a dashed visual treatment. Relations with a context qualifier,
such as `learns`, are rendered as relation-occurrence nodes connected to their
source, target, and context so their n-ary meaning is not hidden. Other
reference-valued qualifiers remain navigable in the relation inspector.

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
realisation-view generations, the ontology `5.0` schema viewer, distribution
builds, a clean wheel installation, and an installed-public-API smoke test.
GitHub Actions runs the same command on pushes to `main` and on pull requests.

## Scope and next increments

The temporal extension is specified by the [temporal extent contract](docs/career-model-v0.5-temporal-contract.md) and exercised in the [temporal instantiation experiment](docs/career-model-v0.5-temporal-instantiation-experiment.md). The implemented query surface intentionally remains small: `covered_months`, `before`, `overlaps`, `select_activities_in_window`, and the renderer-supporting `select_whole_realisation`.

The accepted [Career Ontology 5.0 specification](docs/career-ontology-v5.0-specification.md)
integrates the complete adopted Model 4.2 vocabulary with those temporal
semantics and the M1-B decisions. Its complete implementation currently uses
the exact public `5.0` identity exposed by `caron` `0.2.0`. Ontology versions
`4` and `0.5` are historical executable predecessors rather than supported
runtime schemas.

The private witness-carrying algebra preserves the accepted join, left-join,
union, extension, property-lookup, projection, and ordering regressions. It is
not a public plan language; schema-aware plan validation and stable named query
contracts remain deferred.

Durable semantic serialization, storage, CLI behavior, activity extents,
temporal relation qualifiers, period controls, chronological timelines, and a
complete interval algebra also remain deferred. The current Cytoscape JSON is
an interaction-layer projection rather than a persistence format or semantic
codec.

The `0.x` package line is experimental and may break compatibility; stable
compatibility guarantees begin no earlier than `caron` `1.0`. No migration API
is included in `0.2.0`, and legacy realisations are never silently relabelled as
ontology `5.0`.

See also the [implementation overview](career-ontology-package-skeleton.md), [package boundaries](docs/career-ontology-package-boundaries.md), and [entity representation notes](docs/career-ontology-entity-representation-pseudocode.md).
