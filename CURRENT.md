# Current Project Baseline

This file is the authority map for the maintained `caron` project. It records
what is current, what is historical evidence, and which decisions remain open.
Each update is tied to the Git revision containing this record.

## Version ledger

| Concern | Current identifier | Meaning |
|---|---|---|
| Source baseline | This `CURRENT.md` status and its containing Git commit | Reproducible maintained semantic, query, temporal, and viewer source tree |
| Python distribution | `caron` `0.2.0` | Accepted package release identifier; not an ontology version |
| Architecture contract | `0.3` | One-schema runtime and current package-boundary decisions |
| Ontology identity | `caron.career-model` | Stable ontology-family identifier |
| Historical schema | version `4` | Earlier executable predecessor; preserved in documents and Git history, not the runtime package |
| Historical temporal schema | version `0.5` | Earlier temporal predecessor; preserved in documents and Git history, not the runtime package |
| Current ontology | version `5.0` | Accepted normative schema and exact current executable identity |

`4`, Model 4.2, `0.5`, and `5.0` are lineage labels, not numbers to compare
across conceptual and executable histories. Model 4.2 is the conceptual
predecessor; executable versions `4` and `0.5` are historical; and `5.0` is the
integrated ontology target. The `caron` distribution version is independent
from the ontology version.

## Authority map

| Artifact | Status | Authority |
|---|---|---|
| `caron/` | Current executable authority | Runtime types, ontology schemas, validation, queries, views, and internal algebra |
| `caron/data/` | Package-maintained career realisation | One installed selective YAML file; validation and ontology remain authoritative for its semantics |
| `tests/` | Current executable regressions | Accepted behavior and non-inferences |
| `docs/career-model-v0.5-temporal-contract.md` | Normative for v0.5 temporality | Temporal value, validation, and query semantics |
| `docs/career-ontology-package-boundaries.md` | Normative architecture note | Package ownership and public/private boundaries |
| `docs/career-ontology-m1b-semantic-decisions.md` | Accepted M1-B decisions | Normative inputs to the integrated ontology `5.0` specification |
| `docs/career-ontology-v5.0-specification.md` | Accepted M1-C specification | Normative vocabulary, invariants, lineage, migration, and conformance contract for ontology `5.0` |
| `docs/career-ontology-v5.0-implementation-plan.md` | Active implementation plan | Maintained task list, progress, and acceptance gates for `caron` `0.2.0` |
| `career-ontology-package-skeleton.md` | Current implementation overview | Implemented surface, tree, and deliberately deferred work |
| Temporal review and instantiation documents | Supporting evidence | Design review and worked experiment; not separate runtime authorities |
| `examples/` | Executable demonstrations | Semantic, temporal, and renderer behavior from the maintained package |
| Legacy `career-model` prototype | Historical | Evidence for earlier CLI and query behavior; not maintained code |
| Query-algebra archive | Historical experiment | Its accepted operator and witness regressions are ported to `caron/_query_algebra.py` and current tests |

Documents outside this table may explain earlier decisions, but they do not
override the current code, tests, temporal contract, M1-B decisions, or
package-boundary note.

## Active milestone

M1-A, M1-B, and M1-C are complete. The
[M1-A reconciliation](docs/career-ontology-m1a-reconciliation.md) maps every
Model 4.2 entity, relation, invariant, architecture boundary, and competency
question to executable versions `4` and `0.5`. The
[M1-B decision record](docs/career-ontology-m1b-semantic-decisions.md) resolves
the semantic gaps and assigns the new integrated ontology version `5.0` while
keeping the `caron` package version independent. The
[accepted M1-C specification](docs/career-ontology-v5.0-specification.md)
consolidates those decisions into one exact normative schema. Implementation
is tracked in the [maintained task list](docs/career-ontology-v5.0-implementation-plan.md).
Phases 1–10 have delivered the meta-model extensions, the complete exact
catalogue (13 concepts, 31 relation signatures, six cardinalities, and eight
invariant declarations), local record validation, and all realisation-wide
invariants, plus representative fixtures, conformance evidence, and the ported
temporal and private query-algebra behavior. All maintained examples and
viewers now run on that implementation. The legacy `4` and `0.5` builders,
exports, fixtures, and vocabulary have been removed from the runtime. Phase 10
promotes the verified implementation to the public `career_ontology_v5_0()`
factory and exact `caron.career-model` / `5.0` identity. Package version
`0.2.0` remains independent of the ontology version.

All eight declared handlers are implemented, ontology self-validation
succeeds, and conforming exact `5.0` candidates can be validated. The retained
query behaviors run against that accepted schema without changing its positive
assertion set.

An initial read-only YAML adapter now loads a single format `0.1` file for
exact ontology `5.0`. Its explicit value tags bind to the same typed candidate
records used by direct callers, and `validate_candidate` remains the sole
semantic validation boundary. Loader findings carry file locations separately
from the semantic records. One broad career file now ships under `caron/data/`;
the internal loader reads and validates it from the installed package. Small
examples and failure probes live in `tests/`; canonical writing, durable
storage, and migrations remain open decisions.

The YAML files are package-maintained, not interactive documents. The broad
career realisation remains a single installed file; its source comment provides
review context without adding per-assertion provenance to the realisation format.

Validation is staged: record shape, identifiers, required text, typed values,
and reference closure must pass before cardinalities and graph invariants run.
Semantic relation identity, distinct-fact cardinalities, structural acyclicity,
Proposition locality, `bears_on` roles/locality, and transitive temporal
consistency are implemented. The representative conformance suite covers all
13 concepts, all 31 relation kinds, required non-inferences, cardinality
failures, and generative boundaries.
Retained temporal queries preserve direct and inherited witnesses without
materializing derived assertions. The private algebra uses typed
`uses_technology` facts and preserves both `YearMonth` and complete
`TemporalExtent` values through property lookup and ordering. The maintained
schema viewer exposes the complete catalogue, cardinality, and invariant
inventories; all maintained realisation examples and viewers use exact `5.0`.
The runtime contains no executable `4` or `0.5` schema and no compact legacy
vocabulary. The full verification gate passes with 441 tests; details and
evidence mapping are recorded in Phases 3–10 of the implementation plan.

## Pre-1.0 implementation-transition policy

The `caron` package remains experimental before `1.0`. During this period,
implementation work optimizes for learning, semantic clarity, and a coherent
current public surface rather than backward compatibility with every earlier
prototype. Ontology versions remain exact historical artifacts, but a new
`caron` `0.x` release is not required to keep every earlier ontology executable
or to accept its realisations.

The ontology `5.0` implementation temporarily coexisted with executable
versions `4` and `0.5` while useful behavior and tests were ported. That
transition is complete: the earlier builders have been removed without a
compatibility shim, and their schemas remain recoverable from documents and
Git history. `caron` `0.2.0` maintains ontology `5.0` only.

Migration is a separate package capability under section 16.2 of the accepted
`5.0` specification. It is not part of this implementation increment and will
not be advertised by `caron` `0.2.0`. Stable compatibility, deprecation, and
migration guarantees begin no earlier than `caron` `1.0`; no `0.x` release
creates them implicitly.

## Maintained implementation

The one authoritative source tree is this repository:

- `caron/ontology.py` defines immutable schema records and the public exact
  `career_ontology_v5_0()` catalogue; historical versions are not executable;
- `caron/_invariants.py` owns the internal staged registry of invariant handlers
  and the identifier/required-text implementations;
  schema declarations contain identifiers, not callbacks;
- `caron/_career_v5_invariants.py` owns typed semantic relation identity and
  the six realisation-wide ontology `5.0` handlers;
- `caron/entities.py`, `relations.py`, and `realisations.py` own semantic
  records, stable assertion identities, coverage, and validated reads;
- `caron/validation.py` is the only candidate-to-validated boundary;
- `caron/temporal.py` owns month-level temporal values;
- `caron/queries.py` owns the small public typed temporal catalogue;
- `caron/views.py` owns renderer-independent `GraphView`, bindings, and
  witnesses;
- `caron/_query_algebra.py` preserves the accepted witness-carrying join,
  left-join, union, extension, property lookup, projection, and ordering
  behavior as a private execution experiment, including typed `YearMonth` and
  non-flattened `TemporalExtent` property values;
- `examples/cytoscape_html.py` adapts `GraphView` values to renderer JSON and
  never serves as a persistence codec;
- `examples/ontology_schema_html.py` projects an exact `OntologySchema` version
  to an interactive rule graph; it does not represent asserted career facts;
- all maintained examples and both viewer layers target exact ontology `5.0`.

The algebra is intentionally private and unchecked. Publishing a plan AST,
adding schema-aware plan validation, and stabilizing named non-temporal query
contracts belong to M2A, not M0.

## Reproducibility gate

From a fresh checkout with `uv` installed, one command installs the locked
development environment and runs formatting, linting, strict typing, unit and
invariant tests, semantic and temporal examples, all three realisation viewers,
the ontology `5.0` schema viewer, distribution builds, a clean wheel
installation, and an installed-public-API smoke test:

```bash
uv run --locked --all-groups python tools/verify.py
```

Generated HTML is disposable output and is ignored by Git. The verification
gate generates it in a temporary directory from the same checked-out sources.

## Maintained reproducibility record

| Gate | Evidence in this baseline |
|---|---|
| One authoritative source tree | Semantic spine, internal algebra, temporal queries, `GraphView`, and viewer live in this repository |
| One test command | `uv run --locked --all-groups python tools/verify.py` |
| One current version record | This file and its containing Git commit |
| Accepted regressions pass | Current unit/invariant suite includes ported query-algebra cases and is run by the gate |
| Latest viewers come from the same tree | The gate regenerates complete, two-context, temporal-window, and versioned ontology-schema viewers |

## Explicitly unresolved

The following remain unresolved after the `0.2.0` acceptance transition:

- a separately specified migration capability for earlier ontology versions
  and conceptual source material;
- one unified public result contract across binding tables, paths, temporal
  answers, and `GraphView`;
- schema-aware query-plan candidate and validation boundaries;
- canonical semantic serialization, decoding, migrations, and persistence;
- realisation version identifiers beyond the current realisation identity;
- application operations, CLI, period controls, chronological timelines, and
  an authoring workflow.

These are roadmap work. In particular, Cytoscape JSON must not be reused as a
snapshot format, and internal query plans must not be serialized as public
contracts.
