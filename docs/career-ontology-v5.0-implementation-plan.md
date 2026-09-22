---
kind: implementation_plan
status: accepted_awaiting_push_and_review
date: 2026-09-22
ontology_id: caron.career-model
ontology_target: "5.0"
package_target: "0.2.0"
architecture_contract_target: "0.3"
current_phase: phase_10_accepted_awaiting_push
---

# Career Ontology 5.0 — Implementation Plan

## 1. Purpose

This document is the maintained task list for implementing the accepted
Career Ontology `5.0` specification in `caron`. It is updated as work is
completed, refined, or deliberately deferred.

The transition rule is:

> Add `5.0`, port useful behavior, verify it, and only then remove the legacy
> executable schemas.

Temporary coexistence during development is a risk-control technique. It does
not create a compatibility promise.

## 2. Accepted implementation policy

- The target distribution is `caron` `0.2.0`.
- The only maintained ontology at the end of this increment is
  `caron.career-model` / `5.0`.
- Ontology versions `4` and `0.5` remain historical milestones in documents
  and Git history, not permanent runtime obligations.
- Breaking package and data-model changes are permitted before `caron` `1.0`.
- This increment does not provide a public data-migration feature.
- Serialization, persistence, a public query language, and new interpretive
  queries remain outside this increment.
- The accepted `5.0` specification remains the semantic authority.

## 3. Progress conventions

- `[ ]` pending
- `[x]` completed and verified
- `[-]` deliberately removed or superseded, with a note explaining why

A phase is complete only when its acceptance gate passes.

## 4. Phase 0 — Transition baseline

- [x] Accept and publish the normative ontology `5.0` specification.
- [x] Create branch `ontology-5.0-implementation`.
- [x] Confirm the pre-change unit and invariant baseline: 72 tests pass.
- [x] Run the complete pre-change verification gate.
- [x] Record the pre-`1.0` compatibility policy in `CURRENT.md`.
- [x] Record that migration support is outside this increment.
- [x] Classify legacy tests while porting them as retained, superseded, or
      historical.
- [x] Keep legacy schema builders temporarily available during the port.

Acceptance gate: the transition starts from a green baseline and its scope is
explicit.

## 5. Phase 1 — Meta-model and value domains

### 5.1 `YearMonth` property values

- [x] Add `ValueKind.YEAR_MONTH`.
- [x] Add `YearMonth` to `PropertyValue`.
- [x] Validate `YearMonth` values at the record boundary.
- [x] Test acceptance of a `YearMonth` property value.
- [x] Test rejection of incorrect runtime values for a `YearMonth` property.
- [x] Review every exhaustive property-value adapter for the new variant.

### 5.2 Inspectable global invariants

- [x] Add an immutable `InvariantDefinition` record with a stable identifier.
- [x] Add invariant declarations to `OntologySchema`.
- [x] Keep executable callbacks outside schema records.
- [x] Diagnose duplicate invariant declarations.
- [x] Diagnose invariant declarations without a registered implementation.
- [x] Add a validator registry for implemented invariant identifiers.
- [x] Preserve deterministic ontology diagnostics.
- [x] Add schema-viewer projection data for declared invariants.

Planned ontology `5.0` invariant identifiers:

- `record_identifier_lexical`
- `required_text_non_blank`
- `semantic_relation_fact_unique`
- `part_of_acyclic`
- `suborganization_of_acyclic`
- `aims_at_locality`
- `bears_on_roles_and_locality`
- `temporal_consistency`

Acceptance gate: the meta-model can declare every category of `5.0` validity
rule without introducing a general constraint language.

## 6. Phase 2 — Exact ontology `5.0` schema

### 6.1 Concepts and properties

- [x] Add `Collective`, `Language`, and `Credential` concept constants.
- [x] Define all 13 exact concept kinds.
- [x] Require `label: Text` on every concept.
- [x] Define optional `Context.temporal_extent: TemporalExtent`.
- [x] Define required `Proposition.content: Text`.
- [x] Define required `Proposition.context: EntityReference[Context]`.
- [x] Define optional `Credential.awarded_in: YearMonth`.
- [x] Exclude generic Context status and standalone start/end properties.

### 6.2 Endpoint families

- [x] Define internal `Agent` endpoint kinds.
- [x] Define internal `Learnable` endpoint kinds.
- [x] Define internal `IntellectualResource` endpoint kinds.
- [x] Ensure family names cannot be used as entity kinds.

### 6.3 Relations and qualifiers

- [x] Define all 31 exact relation kinds.
- [x] Define every source- and target-kind set.
- [x] Define every required and optional qualifier.
- [x] Require the `participates_in.role` qualifier.
- [x] Add optional `participates_in.organization`.
- [x] Require `collective_membership.context` and `.role`.
- [x] Require `organization_association.role`.
- [x] Split compact `uses` into `uses_technology` and `uses_artifact`.
- [x] Add `uses_language` and `native_language`.
- [x] Add `modifies`.
- [x] Add all four credential relations.
- [x] Add `addresses` and `bears_on`.

### 6.4 Cardinalities

- [x] Require one or more performers for each Activity.
- [x] Require exactly one `occurs_in` for each Activity.
- [x] Require exactly one `awarded_to` for each Credential.
- [x] Require one or more `awarded_by` for each Credential.
- [x] Require one or more `obtained_through` for each Credential.
- [x] Declare zero or more `evidenced_by` for each Credential.

### 6.5 Exactness tests

- [x] Assert exact development identity `caron.career-model` / `5.0-dev`.
- [x] Assert the exact 13-concept inventory and property signatures.
- [x] Assert the exact 31-relation inventory, endpoints, and qualifiers.
- [x] Assert all six cardinality declarations.
- [x] Assert all global-invariant declarations.
- [x] Assert that schema self-validation reports only the eight pending
      invariant handlers, with no structural diagnostics.
- [x] Assert that missing handlers prevent candidate acceptance.
- [x] Keep the development factory private and omit the accepted `5.0` factory
      from the public API.

Catalogue gate passed: concept/property and relation/qualifier signatures,
endpoint families, cardinality declarations, and invariant declarations match
sections 5–11 of the accepted specification. Their complete enforcement is not
claimed by Phase 2.

### 6.6 Development boundary and verification record

At the Phase 2 checkpoint, the private
`caron.ontology._career_ontology_v5_0_development()` factory returns
`caron.career-model` / `5.0-dev`. The eight invariant identifiers are declared
but have no registered handlers; `validate_ontology()` reports
`ontology.unimplemented_invariant` for each, and `validate_candidate()`
refuses acceptance. No no-op handlers are registered and no declarations are
removed to bypass this boundary.

This corrects a sequencing dependency in the original checklist: a fully
successful schema self-validation belongs after the Phase 3–4 implementations.
That task is retained in Phase 4 below. Promotion to the accepted identifier
`5.0` and public `career_ontology_v5_0()` factory additionally requires the
section 16.1 conformance gate; the specification explicitly prohibits an
incomplete implementation claiming `5.0`.

`tests/unit/test_ontology_v5.py` independently enumerates all 13 concept
signatures, 31 relation signatures, 41 expanded endpoint pairs, six
cardinalities, and eight invariant declarations. It adds 70 tests including
checks that families, legacy relations, and derived constructs do not become
schema vocabulary. The declaration tests remain useful after promotion;
readiness tests must evolve as real handlers land in Phases 3–4.

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 151
tests (81 retained plus 70 catalogue tests), formatting, Ruff, strict mypy,
existing semantic/temporal examples and viewers, and source/wheel builds.

No runtime conformance, example port, viewer CLI update, legacy removal,
migration support, or package-version bump is claimed by this phase.

## 7. Phase 3 — Local record validation

- [x] Reject blank entity and relation identifiers.
- [x] Reject leading and trailing identifier whitespace.
- [x] Preserve separate entity and relation identifier namespaces.
- [x] Never infer kind or meaning by parsing identifiers.
- [x] Reject blank required labels, proposition content, and roles.
- [x] Preserve the validity of duplicate human labels.
- [x] Validate `Credential.awarded_in` as `YearMonth`.
- [x] Preserve unknown property, qualifier, endpoint, and reference checks.
- [x] Preserve duplicate property- and qualifier-name checks.
- [x] Freeze stable diagnostic codes for the new rules.

Local-validation gate passed: every entity and relation assertion must pass
the local stage before graph-wide validation begins.

### 7.1 Implementation boundary and diagnostics

`record_identifier_lexical` and `required_text_non_blank` now have real
implementations in `caron/_invariants.py`. The internal registry records each
handler's local-record or realisation stage; declarations remain callback-free.
Handlers run only when declared, once in their stage. Lexical validation does
not parse prefixes, trim identifiers, normalize text, or restrict open roles.
Internal identifier whitespace remains valid, and text may have surrounding
whitespace provided it contains a non-whitespace character.

| Diagnostic code | Layer | Record / field | Meaning |
|---|---|---|---|
| `record.invalid_identifier` | local record | offending entity or relation id / `id` | Blank identifier or leading/trailing whitespace |
| `record.blank_required_text` | local record | owning record id / property or qualifier name | Present, text-typed required value contains only whitespace |

Missing fields and wrong value types retain their existing, distinct codes.
Duplicate-id diagnostics retain their realisation layer and separate entity
and relation namespaces, but are checked before graph validation. Endpoint,
reference, unknown-field, duplicate-field, and local temporal checks are retained.

`validate_candidate()` retains the schema-readiness gate, then checks ontology
identity and local records before cardinalities, temporal containment, or
realisation-stage handlers. Invalid candidates no longer accumulate downstream
graph diagnostics from malformed records; those checks wait until local errors
are resolved. The private `_validate_local_records()` helper returns diagnostics
only and cannot construct a validated realisation.

At the Phase 3 checkpoint, the development catalogue retains all eight
declarations while six handlers remain pending, so public candidate validation
still refuses acceptance. Tests exercise the private local stage against the
full `5.0-dev` catalogue without removing declarations or pretending it
conforms to `5.0`. Separate test-only ontologies verify the staged acceptance
machinery.

### 7.2 Verification record

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 349 tests
(151 retained plus 198 added), formatting, Ruff, strict mypy, semantic/temporal
examples, all existing viewers, and source/wheel builds.

New tests cover all 13 concept labels, independent Proposition content, all
three required role declarations, optional typed credential award months,
reference closure and kinds, unknown vocabulary, duplicate fields and record
identities, Unicode whitespace, opacity/case-sensitive identity, shared labels,
and input preservation. Generative tests check arbitrary Unicode identifiers
and required text. Stage tests prove local rejection prevents graph checks and
handlers run exactly once in stage order. The schema-readiness tests now expect
only the six genuinely unimplemented handlers.

No package-version bump, public `5.0` acceptance, example port, serialization,
or migration support is claimed. Phase 4 is next.

## 8. Phase 4 — Realisation-wide invariants

### 8.1 Semantic relation identity

- [x] Build a typed, qualifier-order-independent semantic relation key.
- [x] Exclude the relation assertion identifier from semantic equality.
- [x] Reject duplicate semantic facts with different identifiers.
- [x] Emit `realisation.duplicate_relation_fact`.
- [x] Count distinct semantic facts for cardinality validation.

### 8.2 Structural graphs

- [x] Reject `part_of` self-loops and longer cycles.
- [x] Accept valid multiple-parent Context DAGs.
- [x] Reject `suborganization_of` self-loops and longer cycles.
- [x] Make cycle diagnostics independent of record order.

### 8.3 Proposition locality

- [x] Accept same-Context `aims_at` assertions.
- [x] Reject mismatched Proposition locality.
- [x] Never rewrite, clone, or relocalize propositions during validation.

### 8.4 `bears_on`

- [x] Require the source to be an explicit activity outcome.
- [x] Require the target to be an explicit aim.
- [x] Reject identical source and target propositions.
- [x] Accept equal Contexts.
- [x] Accept a source Context nested within the target Context.
- [x] Reject sibling and reversed-context cases.
- [x] Never infer a `bears_on` assertion.

### 8.5 Temporal consistency

- [x] Preserve known, unknown, and ongoing end states.
- [x] Preserve transitive Context containment.
- [x] Preserve multiple-parent temporal-intersection checks.
- [x] Constrain Activity time through `occurs_in`.
- [x] Never copy a Context extent onto a child or Activity.
- [x] Keep ongoing observations fixed rather than clock-dependent.
- [x] Accept incomplete but consistent temporal information.
- [x] Reject impossible temporal interpretations.

### 8.6 Complete schema readiness

- [x] Replace the Phase 2 missing-handler expectations as real invariant
      implementations are registered; never substitute no-op handlers.
- [x] Assert that the complete development schema passes ontology
      self-validation with all eight declarations retained.

Phase 4 enforcement gate passed: the realisation-wide rules in section 11 and
the corresponding enforcement requirements in section 16.1 are executable.
The exact `5.0` public identity remains gated on the representative conformance
suite, non-inference audit, and promotion work in later phases.

### 8.7 Implementation boundary and diagnostics

`caron/_career_v5_invariants.py` implements the six realisation-stage handlers.
It also owns the typed semantic relation key used by both duplicate detection
and cardinality counting. The key consists of relation kind, complete source
and target identifiers, and a qualifier-name mapping to explicitly tagged
values. It excludes the assertion identifier and qualifier-entry order.

Cycle validation tests each structural edge against deterministic reachability.
This rejects self-loops and every edge participating in a longer cycle while
accepting multiple-parent DAGs. `aims_at` reads the Proposition's required
`context` property as the sole locality authority. `bears_on` checks explicit
outcome and aim assertions, distinct propositions, and directed Context
reachability; none of these handlers creates inferred assertions.

Temporal consistency retains the established existential interval semantics.
Known parent ends impose upper bounds; unknown and ongoing ends remain open,
with an ongoing observation fixing only its recorded minimum end. Every Context
must fit the intersection of all direct and transitive dated ancestors. An
Activity has no intrinsic extent in ontology `5.0`: its exactly-one `occurs_in`
fact constrains its nonempty occurrence without copying the Context extent.

Stable Phase 4 diagnostics are:

| Diagnostic code | Condition |
|---|---|
| `realisation.duplicate_relation_fact` | Two identified records have the same semantic relation key |
| `realisation.part_of_cycle` | A `part_of` edge participates in a cycle |
| `realisation.suborganization_of_cycle` | A `suborganization_of` edge participates in a cycle |
| `realisation.aims_at_context_mismatch` | Aim Context differs from the target Proposition locality |
| `realisation.bears_on_source_not_outcome` | Source Proposition lacks an explicit activity-outcome role |
| `realisation.bears_on_target_not_aim` | Target Proposition lacks an explicit aim role |
| `realisation.bears_on_self_reference` | Source and target are the same Proposition |
| `realisation.bears_on_incompatible_context` | Source locality is not equal to or nested within target locality |
| `realisation.temporal_containment_impossible` | Context containment admits no temporal interpretation |

Existing cardinality diagnostics remain unchanged. Cardinalities now count
distinct semantic facts, so repeated records produce a duplicate-fact error
without falsely increasing an exactly-one count.

### 8.8 Verification record

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 389
tests, formatting, Ruff, strict mypy, semantic/temporal examples, all existing
viewers, and source/wheel builds.

The 40 Phase 4 tests cover typed and qualifier-order-independent identity,
duplicate and distinct cardinality counts for Activity and Credential,
self-loops, longer cycles, multiple-parent DAGs, deterministic diagnostics,
Proposition locality, every activity-outcome role, equal/nested/sibling/reversed
`bears_on` locality, explicit-evidence non-inference, cross-Context outcomes,
known/unknown/ongoing extents, transitive and multiple-parent containment,
incomplete time, activity constraints, and preservation of asserted values.
The complete `5.0-dev` schema now passes `validate_ontology()` with all eight
declarations and real handlers. Conforming development candidates may be
accepted, but no public exact-`5.0` factory or package-version bump is claimed.

## 9. Phase 5 — Fixtures and conformance suite

### 9.1 Fixtures

- [x] Create a minimal valid `5.0` candidate.
- [x] Create focused builders for labelled entities, propositions, and
      relation assertions.
- [x] Create a rich valid candidate covering all 13 concepts.
- [x] Cover all 31 relation kinds across focused fixtures.

### 9.2 Required valid and invalid cases

- [x] Cover personal, collective, and multiple-performer activities.
- [x] Cover participation with and without an organization.
- [x] Cover collective membership and organization association.
- [x] Cover Language exposure, learning, use, and native-language facts.
- [x] Cover independent `applies` and `draws_on` facts.
- [x] Cover input, use, modification, and production distinctions.
- [x] Cover single- and joint-awarder credentials.
- [x] Cover known and absent `awarded_in` values.
- [x] Cover valid and invalid `aims_at` locality.
- [x] Cover equal, nested, sibling, and reversed `bears_on` Contexts.
- [x] Cover Place and `occurs_at`.
- [x] Cover known, unknown, ongoing, undated, nested, and contradictory time.
- [x] Cover every activity and credential cardinality failure.

### 9.3 Required non-inferences

- [x] Participation does not create performance.
- [x] Collective performance does not create personal performance.
- [x] Exposure does not create learning.
- [x] Learning does not create exposure or resource use.
- [x] Activity use does not create a Person-to-resource assertion.
- [x] `applies` and `draws_on` do not imply one another.
- [x] Language facts do not create `native_language`.
- [x] Artifact-role relations remain independent.
- [x] `supports` does not create `establishes`.
- [x] Context membership does not create `addresses`.
- [x] Outcome paths do not create `bears_on`.
- [x] Temporal containment does not copy extents.
- [x] Validation preserves the candidate's positive relation set exactly.

### 9.4 Generative invariants

- [x] Preserve validation independence from record ordering.
- [x] Generate equivalent qualifier-map orderings.
- [x] Generate valid and invalid endpoint-family combinations.
- [x] Preserve `YearMonth` round trips across years 1–9999.
- [x] Generate valid and impossible temporal-containment cases.

Acceptance gate passed: every mandatory conformance scenario has explicit test
evidence.

### 9.5 Fixture boundary

`tests/fixtures/v5.py` supplies test-only builders for labelled entities,
localized Propositions, identified relation assertions, candidates, valid
Activity performer configurations, and valid Credential awards. These are not
runtime factories or serialization formats.

The minimal fixture contains one Person, Context, and Activity with the two
required Activity facts. The rich fixture contains 24 entities and 37 relation
assertions. It independently covers all 13 concept kinds and all 31 relation
kinds while remaining valid, including:

- personal and collective performance;
- qualified participation with and without an Organization;
- Language exposure, learning, Activity use, and native-language facts;
- independent reusable-resource and Artifact roles;
- a joint award with a known `YearMonth`;
- Place, Proposition locality, explicit outcome roles, and `bears_on`;
- nested known Context extents.

### 9.6 Conformance evidence

`tests/conformance/test_v5_conformance.py` adds representative positive,
negative, and non-inference scenarios. It verifies all bounded Activity and
Credential cardinality failures; the `evidenced_by` `0..*` case is covered by
a valid Credential with no evidence assertion. Validation of the rich fixture
also proves that candidate entity and relation tuples are preserved exactly.

The focused Phase 3 tests remain the evidence for identifier, required-text,
typed-value, vocabulary, reference, and duplicate-field behavior. The focused
Phase 4 tests remain the evidence for semantic duplicates, structural cycles,
valid and invalid `aims_at`, equal/nested/sibling/reversed `bears_on`, and the
complete known/unknown/ongoing/undated temporal matrix. Phase 5 does not copy
those tests; it integrates their evidence into the conformance gate.

`tests/invariants/test_v5_conformance_invariants.py` adds generative checks for
record ordering, qualifier-map ordering, all declared endpoint families,
Credential `YearMonth` values across years 1–9999, and valid versus impossible
temporal containment.

### 9.7 Verification record

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 435
tests (389 retained plus 46 Phase 5 scenarios), formatting, Ruff, strict mypy,
semantic/temporal examples, all existing viewers, and source/wheel builds.

No runtime API, ontology identifier, package version, query behavior, example,
viewer, serialization, or migration capability changes in this phase. The
private `5.0-dev` identity remains in force; Phase 6 ports retained query
behavior before later visualization, legacy removal, and public promotion.

## 10. Phase 6 — Port retained query behavior

- [x] Port temporal fixtures from `0.5` to `5.0`.
- [x] Run `covered_months`, `before`, and `overlaps` on `5.0`.
- [x] Run definite and possible temporal-window selection on `5.0`.
- [x] Verify direct and inherited temporal witnesses.
- [x] Verify that `GraphView` never materializes derived assertions.
- [x] Port private query-algebra fixtures to the typed use relations.
- [x] Retain join, left-join, union, projection, ordering, and witness tests.
- [x] Handle `YearMonth` explicitly in scalar property lookup.
- [x] Keep `TemporalExtent` handling explicit rather than flattening it.
- [x] Do not add new reusable-resource-history queries in this phase.

Acceptance gate passed: every retained query behavior works against the
ontology `5.0-dev` implementation candidate.

### 10.1 Port boundary

`tests/fixtures/temporal_v5.py` replaces the query tests' dependency on the
legacy `0.5` example with a test-only `5.0-dev` candidate. It covers closed,
ongoing, inherited, and undated Context time, and uses the typed
`uses_technology` relation. The public temporal functions remain unchanged;
they now execute against a realisation accepted by the complete development
schema.

The private query-algebra fixture is also a valid `5.0-dev` candidate. Its
compact `uses` facts have become `uses_technology`, and a valid Credential
case exercises `awarded_in`. Scalar lookup preserves `YearMonth` as a typed
value. Lookup and ordering preserve an entire `TemporalExtent`, including its
end-state variant, rather than reducing it to a legacy year or separate
start/end fields.

No public query language, named reusable-resource-history query, derived
assertion, serialization format, or persistence contract is introduced.
`GraphView` continues to project only asserted entities and relations selected
by witnesses. Direct and inherited temporal evidence remains explicit, while
derived temporal classifications never become graph assertions.

### 10.2 Verification record

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 439
tests, formatting, Ruff, strict mypy, semantic/temporal examples, all existing
viewers, and source/wheel builds.

The retained query evidence comprises 15 temporal-query tests, four temporal
invariant tests, and nine private query-algebra tests. These 28 tests cover
month counts, ordering, overlap, definite/possible window selection, direct
and inherited witnesses, asserted-only graph projection, natural and left
joins, union, extension, projection, ordering, path results, selective empty
results, and typed property lookup. Four tests are new in this phase; the
remaining cases are ports of retained behavior. Maintained examples and
viewers intentionally remain on the legacy schemas until Phase 7.

## 11. Phase 7 — Examples and visualization

### 11.1 Ontology-schema viewer

- [x] Add appearances for the three new concepts.
- [x] Render ontology `5.0`.
- [x] Verify 13 nodes, 31 relation rules, and 41 expanded endpoint edges.
- [x] Display all six cardinalities.
- [x] Display the global-invariant inventory.

### 11.2 Realisation viewer

- [x] Serialize `YearMonth` properties.
- [x] Render Collective, Language, and Credential entities.
- [x] Preserve reference-valued qualifier display.
- [x] Preserve temporal-result and witness display.
- [x] Add a representative `5.0` career graph.
- [x] Keep renderer JSON outside persistence contracts.

### 11.3 Maintained examples

- [x] Replace the Model 4 semantic-spine example with a `5.0` example.
- [x] Port the two-context reusable-technology example.
- [x] Port the temporal-query example.
- [x] Update terminology and commands.
- [x] Run all maintained examples and viewers from `tools/verify.py`.

Acceptance gate passed: every maintained example and viewer is generated from
the ontology `5.0-dev` implementation candidate.

### 11.4 Example and viewer boundary

The ontology-schema viewer now renders only the maintained implementation
candidate. Its graph contains all 13 concepts, 31 relation rules, and 41
expanded endpoint pairs. Collective, Language, and Credential have explicit
appearances. The sidebar displays the complete inventories of six cardinality
requirements and eight declared global invariants rather than leaving them
only in the embedded data.

The semantic-spine example is a representative selective career graph using
all 13 concept kinds. It includes personal and collective performance,
Language use, an Organization reference qualifier, a Place, and a particular
Credential award with a typed `YearMonth`. The two-context example uses typed
Technology and Artifact use relations, and the temporal example uses the
ontology `5.0` vocabulary and validation boundary.

The example-coupled temporal-validation suite was classified during the port:
its seven retained validation behaviors now run on `5.0-dev`; the old test
whose sole purpose was to compare executable versions `4` and `0.5` was
superseded by a check of the integrated Context temporal property. Remaining
legacy-only tests are classified when their schemas are removed in Phase 8.

The realisation adapter preserves reference-valued qualifiers, structured
`YearMonth` and `TemporalExtent` values, temporal classifications, and their
witness records. Its output remains renderer-specific JSON under `examples/`;
it is not a semantic codec, persistence format, or public package contract.
The exact public ontology identity remains gated on the later promotion phase,
so these examples correctly identify the executable candidate as `5.0-dev`.

### 11.5 Verification record

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 441
tests, formatting, Ruff, strict mypy, the semantic and temporal examples, all
three realisation viewers, the ontology `5.0-dev` schema viewer, and source and
wheel builds. Focused renderer tests verify the catalogue counts, all
cardinality and invariant declarations, the three new concept appearances,
the integrated Credential award month, navigable Organization qualifier, and
temporal witness payload and inspector display.

## 12. Phase 8 — Remove legacy executable schemas

- [x] Remove `model4_ontology()`.
- [x] Remove `model_v0_5_ontology()`.
- [x] Remove their public exports.
- [x] Remove or rename misleading legacy-only constants.
- [x] Remove obsolete fixtures and tests.
- [x] Record every removal as ported, superseded, or historical.
- [x] Remove compact `uses` and `associated_with` from executable code.
- [x] Remove legacy Context start, end, and status from executable code.
- [x] Retain historical design documents and lineage references.

Acceptance gate passed: the runtime package contains one maintained ontology
implementation candidate and no accidental legacy support surface.

### 12.1 Removal and classification record

| Legacy item | Classification | Phase 8 disposition |
|---|---|---|
| `model4_ontology()` and `model_v0_5_ontology()` | Historical | Removed from `caron/ontology.py` and the public package exports; their specifications and Git history remain authoritative historical evidence. |
| Compact `ALL_CONCEPTS` inventory | Superseded | Removed because it omitted Collective, Language, and Credential; consumers inspect `OntologySchema.concepts`. |
| Compact `uses` and `associated_with` relation rules | Superseded | Removed with the legacy builders; typed use and organization-association rules remain in `5.0-dev`. |
| Context `start`, `end`, and `status` fields | Superseded | Removed with Model 4; Context has the optional typed `temporal_extent` property. |
| `tests/fixtures/minimal.py` | Ported and consolidated | Replaced by `minimal_v5_candidate()` and the builders in `tests/fixtures/v5.py`. |
| Generic ontology, validation, and meta-model tests | Ported | Rebased on the complete `5.0-dev` schema and minimal candidate. |
| Legacy generative validation suite | Superseded | Removed: dangling-reference coverage lives in local 5.0 validation tests, endpoint-family generation and order independence live in the 5.0 conformance invariants. |
| Model 4 versus `0.5` temporal comparison | Historical | Superseded during Phase 7 by the integrated Context temporal-property check. |
| M1-A, Model 4, and v0.5 design documents | Historical | Retained unchanged as design lineage; they are not executable package surfaces. |

This removal is intentionally breaking under the accepted pre-`1.0` policy.
No compatibility shim, alias, decoder, or data migration is introduced. The
private `5.0-dev` factory remains the only schema builder until the exact
public `5.0` promotion in the final acceptance phase.

### 12.2 Verification record

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 439
tests, formatting, Ruff, strict mypy, both maintained examples, all three
realisation viewers, the ontology `5.0-dev` schema viewer, and source and wheel
builds. An explicit regression asserts that `model4_ontology`,
`model_v0_5_ontology`, and `ALL_CONCEPTS` are absent from both the package API
and ontology module. Source searches confirm that compact relation rules and
legacy Context field declarations no longer exist in executable code.

## 13. Phase 9 — Documentation and release transition

- [x] Update `CURRENT.md` and the version ledger.
- [x] Mark ontology `5.0` as the current executable ontology.
- [x] Mark `4` and `0.5` as historical executable predecessors.
- [x] Record that compatibility guarantees begin no earlier than `caron 1.0`.
- [x] Keep migration explicitly deferred.
- [x] Update the package-boundary document and architecture-contract version.
- [x] Update the package implementation overview and README.
- [x] Update specification implementation-status metadata without changing
      accepted ontology semantics.
- [x] Change the package version to `0.2.0` and refresh `uv.lock`.
- [x] Review and minimize `caron.__all__`.

### 13.1 Verification record

The release-transition documents now distinguish package `0.2.0`, current
ontology generation `5.0`, and the private transitional runtime identity
`5.0-dev`. They record architecture contract `0.3`, classify executable
versions `4` and `0.5` as historical, defer migration, and make the pre-`1.0`
compatibility boundary explicit. Specification changes are limited to
implementation-status metadata and its accompanying status note; accepted
ontology semantics are unchanged.

The root export review retained the semantic records, ontology meta-model,
validation results, typed temporal queries, and graph-view types needed by
callers. Private schema construction, invariant registries and handlers,
query-algebra plans, renderers, storage, serialization, and migration remain
outside `caron.__all__`. An exact export-set regression now guards that
boundary; the public exact `5.0` factory remains reserved for Phase 10.

Verification on 2026-09-22: the full `tools/verify.py` gate passes with 440
tests, formatting, Ruff, strict mypy across 43 source files, both maintained
examples, all three realisation viewers, the ontology `5.0-dev` schema viewer,
and `caron` `0.2.0` source and wheel builds.

## 14. Phase 10 — Final acceptance

- [x] Run formatting, Ruff, and strict mypy.
- [x] Run all deterministic and generative tests.
- [x] Run all maintained examples and viewers.
- [x] Build the source distribution and wheel.
- [x] Install the wheel in a clean temporary environment.
- [x] Smoke-test the installed public API.
- [x] Review the final implementation against every section 16.1 obligation.
- [x] Promote the private development factory to public
      `career_ontology_v5_0()` with exact version `5.0` only after the full
      conformance gate passes; update tests, fixtures, examples, and viewers
      to the accepted identity and rerun the full gate.
- [x] Commit the acceptance transition.
- [ ] Push the implementation branch for review.
- [ ] Merge only after the complete verification gate passes.

Acceptance gate: `caron 0.2.0` implements the accepted ontology `5.0` without
claiming deferred migration, storage, or query-contract capabilities.

### 14.1 Section 16.1 conformance review

| Obligation | Final evidence |
|---|---|
| 1. Exact identity | Public `career_ontology_v5_0()` returns `caron.career-model` / `5.0`; root-export and clean-wheel smoke tests exercise it. |
| 2. Thirteen concepts and exact properties | `test_ontology_v5.py` independently enumerates every concept and property signature. |
| 3. Thirty-one relations, endpoint unions, and qualifiers | `test_ontology_v5.py` independently enumerates all relation signatures and 41 expanded endpoint pairs. |
| 4. Record identity and structural closure | `test_v5_local_validation.py` covers lexical identifiers, namespace uniqueness, required fields, value kinds, references, endpoints, and qualifiers. |
| 5. Semantic relation-fact uniqueness | `test_v5_realisation_invariants.py` and generative conformance tests cover record-id independence and qualifier-order equivalence. |
| 6. Activity and Credential cardinalities | Exact declaration tests and representative below/above-bound failures cover all six requirements. |
| 7. Context and Organization acyclicity | Self-loop, long-cycle, and valid multiple-parent DAG tests cover both structural relations. |
| 8. Proposition locality and `bears_on` | Same-context, nested-context, missing-role, sibling, reversed-direction, and self-reference cases are exercised. |
| 9. Month-level temporality | Value, local-validation, transitive-containment, and generative temporal suites cover known, unknown, ongoing, contradictory, nested, and unconstrained cases. |
| 10. Required non-inferences | The conformance suite independently checks performance, exposure, learning, use, artifact-role, outcome, `bears_on`, and temporal non-materialization boundaries. |
| 11. Exact-version rejection | Catalogue tests reject historical `4`, `0.5`, and another exact version rather than relabelling candidates. |
| 12. Derived results remain outside assertions | Temporal query and `GraphView` tests retain witnesses while the conformance suite verifies the positive relation set is unchanged. |
| 13. Representative valid and invalid candidates | Minimal, rich all-vocabulary, focused invalid, deterministic, and Hypothesis-generated candidates all pass their expected outcomes. |

The minimum scenario list following section 16.1 is covered across
`test_v5_conformance.py`, `test_v5_local_validation.py`,
`test_v5_realisation_invariants.py`, `test_temporal_validation.py`, and the two
generative invariant suites. No section 15 exclusion was added to the
ontology contract.

### 14.2 Final verification record

The unchanged private `5.0-dev` implementation first passed the complete
pre-promotion gate with 440 tests. Only then was it renamed to the public
`career_ontology_v5_0()` factory and assigned exact schema version `5.0`.
Tests, fixtures, examples, viewers, package exports, and current-facing
documents were updated to the accepted identity; historical phase records
retain the development identity where it describes an earlier checkpoint.

Final verification on 2026-09-22: `tools/verify.py` passes formatting, Ruff,
strict mypy across 43 source files, all 441 deterministic and Hypothesis tests,
both maintained examples, all three realisation viewers, and the exact
ontology `5.0` schema viewer. It builds the `caron 0.2.0` source distribution
and wheel, installs the wheel without dependencies in a clean temporary
environment, and runs an isolated installed-API smoke test confirming package
version `0.2.0`, public factory availability, exact schema identity, the
13/31/6/8 catalogue counts, and ontology self-validation.

The local acceptance gate is complete. Push and merge remain explicit
repository workflow actions; the branch is ready for review without claiming
migration, persistence, serialization, or a public query-plan contract.
