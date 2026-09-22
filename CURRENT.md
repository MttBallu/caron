# Current Project Baseline

This file is the authority map for the maintained `caron` project. It records
what is current, what is historical evidence, and which decisions remain open.
The M0 baseline is the Git revision containing this record on `main`.

## Version ledger

| Concern | Current identifier | Meaning |
|---|---|---|
| Source baseline | This `CURRENT.md` status and its containing Git commit | Reproducible M0 semantic, query, temporal, and viewer source tree |
| Python distribution | `caron` `0.1.0` | Package release identifier; not an ontology version |
| Architecture contract | `0.2` | Implemented package-boundary decisions |
| Ontology identity | `caron.career-model` | Stable ontology-family identifier |
| Compatibility schema | version `4` | Earlier executable schema retained for regressions and migration work |
| Current temporal schema | version `0.5` | Model 4 vocabulary with the accepted month-level temporal contract |
| Integrated ontology target | version `5.0` | Accepted normative schema completed by M1-C; conformance implementation in progress |
| Development catalogue | version `5.0-dev` | Complete declarations, invariant enforcement, and representative conformance suite; private pending promotion |

`4`, Model 4.2, `0.5`, and `5.0` are lineage labels, not numbers to compare
across conceptual and executable histories. Model 4.2 is the conceptual
predecessor; executable version `4` is the compatibility schema; `0.5` is the
current compact temporal schema; and `5.0` is the integrated ontology target.
The `caron` distribution version is independent: one package release may
support several exact ontology versions and migrations.

## Authority map

| Artifact | Status | Authority |
|---|---|---|
| `caron/` | Current executable authority | Runtime types, ontology schemas, validation, queries, views, and internal algebra |
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
Phases 1–5 have added the meta-model extensions, the complete development
catalogue (13 concepts, 31 relation signatures, six cardinalities, and eight
invariant declarations), local record validation, and all realisation-wide
invariants, plus representative fixtures and conformance evidence. Phase 6
(port retained query behavior) is next.

The private `_career_ontology_v5_0_development()` factory returns version
`5.0-dev`, not the accepted `5.0` identifier. All eight declared handlers are
implemented and ontology self-validation succeeds. Conforming development
candidates can now be validated; this does not claim exact `5.0` conformance.
The public `career_ontology_v5_0()` factory and exact `5.0` identity remain
gated on the query/example ports, legacy removal, release documentation, and
later promotion work. Package version `0.1.0` and existing examples/viewer
commands are unchanged.

Validation is staged: record shape, identifiers, required text, typed values,
and reference closure must pass before cardinalities and graph invariants run.
Semantic relation identity, distinct-fact cardinalities, structural acyclicity,
Proposition locality, `bears_on` roles/locality, and transitive temporal
consistency are implemented. The representative conformance suite covers all
13 concepts, all 31 relation kinds, required non-inferences, cardinality
failures, and generative boundaries.
The full verification gate passes with 435 tests; details and evidence mapping
are recorded in Phases 3–5 of the implementation plan.

## Pre-1.0 implementation-transition policy

The `caron` package remains experimental before `1.0`. During this period,
implementation work optimizes for learning, semantic clarity, and a coherent
current public surface rather than backward compatibility with every earlier
prototype. Ontology versions remain exact historical artifacts, but a new
`caron` `0.x` release is not required to keep every earlier ontology executable
or to accept its realisations.

The ontology `5.0` implementation will temporarily coexist with executable
versions `4` and `0.5` while useful behavior and tests are ported. That
coexistence is a transition technique, not a support commitment. The target
`caron` `0.2.0` release will maintain ontology `5.0` only; earlier executable
schemas remain recoverable from documents and Git history.

Migration is a separate package capability under section 16.2 of the accepted
`5.0` specification. It is not part of this implementation increment and will
not be advertised by `caron` `0.2.0`. Compatibility, deprecation, and migration
guarantees will be defined only when the package and ontology have reached a
sufficiently stable pre-`1.0` boundary.

## Maintained implementation

The one authoritative source tree is this repository:

- `caron/ontology.py` defines immutable schema records and versions `4` and
  `0.5`, plus the private `5.0-dev` catalogue;
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
  behavior as a private execution experiment;
- `examples/cytoscape_html.py` adapts `GraphView` values to renderer JSON and
  never serves as a persistence codec;
- `examples/ontology_schema_html.py` projects an exact `OntologySchema` version
  to an interactive rule graph; it does not represent asserted career facts.

The algebra is intentionally private and unchecked. Publishing a plan AST,
adding schema-aware plan validation, and stabilizing named non-temporal query
contracts belong to M2A, not M0.

## Reproducibility gate

From a fresh checkout with `uv` installed, one command installs the locked
development environment and runs formatting, linting, strict typing, unit and
invariant tests, semantic and temporal examples, all three realisation viewers,
both ontology-schema viewers, and distribution builds:

```bash
uv run --locked --all-groups python tools/verify.py
```

Generated HTML is disposable output and is ignored by Git. The verification
gate generates it in a temporary directory from the same checked-out sources.

## M0 acceptance record

| Gate | Evidence in this baseline |
|---|---|
| One authoritative source tree | Semantic spine, internal algebra, temporal queries, `GraphView`, and viewer live in this repository |
| One test command | `uv run --locked --all-groups python tools/verify.py` |
| One current version record | This file and its containing Git commit |
| Accepted regressions pass | Current unit/invariant suite includes ported query-algebra cases and is run by the gate |
| Latest viewers come from the same tree | The gate regenerates complete, two-context, temporal-window, and versioned ontology-schema viewers |

## Explicitly unresolved

The following remain unresolved after M1-C acceptance:

- implementation and conformance testing of the accepted Career Ontology
  `5.0` schema;
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
