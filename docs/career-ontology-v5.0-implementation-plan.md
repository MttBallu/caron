---
kind: implementation_plan
status: active
date: 2026-09-22
ontology_id: caron.career-model
ontology_target: "5.0"
package_target: "0.2.0"
architecture_contract_target: "0.3"
current_phase: phase_4_realisation_invariants
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
- [ ] Classify legacy tests while porting them as retained, superseded, or
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

The development catalogue retains all eight declarations. Six handlers remain
pending, so public candidate validation still refuses acceptance. Tests exercise
the private local stage against the full `5.0-dev` catalogue without removing
declarations or pretending it conforms to `5.0`. Separate test-only ontologies
verify the staged acceptance machinery.

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

- [ ] Build a typed, qualifier-order-independent semantic relation key.
- [ ] Exclude the relation assertion identifier from semantic equality.
- [ ] Reject duplicate semantic facts with different identifiers.
- [ ] Emit `realisation.duplicate_relation_fact`.
- [ ] Count distinct semantic facts for cardinality validation.

### 8.2 Structural graphs

- [ ] Reject `part_of` self-loops and longer cycles.
- [ ] Accept valid multiple-parent Context DAGs.
- [ ] Reject `suborganization_of` self-loops and longer cycles.
- [ ] Make cycle diagnostics independent of record order.

### 8.3 Proposition locality

- [ ] Accept same-Context `aims_at` assertions.
- [ ] Reject mismatched Proposition locality.
- [ ] Never rewrite, clone, or relocalize propositions during validation.

### 8.4 `bears_on`

- [ ] Require the source to be an explicit activity outcome.
- [ ] Require the target to be an explicit aim.
- [ ] Reject identical source and target propositions.
- [ ] Accept equal Contexts.
- [ ] Accept a source Context nested within the target Context.
- [ ] Reject sibling and reversed-context cases.
- [ ] Never infer a `bears_on` assertion.

### 8.5 Temporal consistency

- [ ] Preserve known, unknown, and ongoing end states.
- [ ] Preserve transitive Context containment.
- [ ] Preserve multiple-parent temporal-intersection checks.
- [ ] Constrain Activity time through `occurs_in`.
- [ ] Never copy a Context extent onto a child or Activity.
- [ ] Keep ongoing observations fixed rather than clock-dependent.
- [ ] Accept incomplete but consistent temporal information.
- [ ] Reject impossible temporal interpretations.

### 8.6 Complete schema readiness

- [ ] Replace the Phase 2 missing-handler expectations as real invariant
      implementations are registered; never substitute no-op handlers.
- [ ] Assert that the complete development schema passes ontology
      self-validation with all eight declarations retained.

Acceptance gate: sections 11 and 16.1 of the accepted specification are
executable.

## 9. Phase 5 — Fixtures and conformance suite

### 9.1 Fixtures

- [ ] Create a minimal valid `5.0` candidate.
- [ ] Create focused builders for labelled entities, propositions, and
      relation assertions.
- [ ] Create a rich valid candidate covering all 13 concepts.
- [ ] Cover all 31 relation kinds across focused fixtures.

### 9.2 Required valid and invalid cases

- [ ] Cover personal, collective, and multiple-performer activities.
- [ ] Cover participation with and without an organization.
- [ ] Cover collective membership and organization association.
- [ ] Cover Language exposure, learning, use, and native-language facts.
- [ ] Cover independent `applies` and `draws_on` facts.
- [ ] Cover input, use, modification, and production distinctions.
- [ ] Cover single- and joint-awarder credentials.
- [ ] Cover known and absent `awarded_in` values.
- [ ] Cover valid and invalid `aims_at` locality.
- [ ] Cover equal, nested, sibling, and reversed `bears_on` Contexts.
- [ ] Cover Place and `occurs_at`.
- [ ] Cover known, unknown, ongoing, undated, nested, and contradictory time.
- [ ] Cover every activity and credential cardinality failure.

### 9.3 Required non-inferences

- [ ] Participation does not create performance.
- [ ] Collective performance does not create personal performance.
- [ ] Exposure does not create learning.
- [ ] Learning does not create exposure or resource use.
- [ ] Activity use does not create a Person-to-resource assertion.
- [ ] `applies` and `draws_on` do not imply one another.
- [ ] Language facts do not create `native_language`.
- [ ] Artifact-role relations remain independent.
- [ ] `supports` does not create `establishes`.
- [ ] Context membership does not create `addresses`.
- [ ] Outcome paths do not create `bears_on`.
- [ ] Temporal containment does not copy extents.
- [ ] Validation preserves the candidate's positive relation set exactly.

### 9.4 Generative invariants

- [ ] Preserve validation independence from record ordering.
- [ ] Generate equivalent qualifier-map orderings.
- [ ] Generate valid and invalid endpoint-family combinations.
- [ ] Preserve `YearMonth` round trips across years 1–9999.
- [ ] Generate valid and impossible temporal-containment cases.

Acceptance gate: every mandatory conformance scenario has explicit test
evidence.

## 10. Phase 6 — Port retained query behavior

- [ ] Port temporal fixtures from `0.5` to `5.0`.
- [ ] Run `covered_months`, `before`, and `overlaps` on `5.0`.
- [ ] Run definite and possible temporal-window selection on `5.0`.
- [ ] Verify direct and inherited temporal witnesses.
- [ ] Verify that `GraphView` never materializes derived assertions.
- [ ] Port private query-algebra fixtures to the typed use relations.
- [ ] Retain join, left-join, union, projection, ordering, and witness tests.
- [ ] Handle `YearMonth` explicitly in scalar property lookup.
- [ ] Keep `TemporalExtent` handling explicit rather than flattening it.
- [ ] Do not add new reusable-resource-history queries in this phase.

Acceptance gate: every retained query behavior works against ontology `5.0`.

## 11. Phase 7 — Examples and visualization

### 11.1 Ontology-schema viewer

- [ ] Add appearances for the three new concepts.
- [ ] Render ontology `5.0`.
- [ ] Verify 13 nodes, 31 relation rules, and 41 expanded endpoint edges.
- [ ] Display all six cardinalities.
- [ ] Display the global-invariant inventory.

### 11.2 Realisation viewer

- [ ] Serialize `YearMonth` properties.
- [ ] Render Collective, Language, and Credential entities.
- [ ] Preserve reference-valued qualifier display.
- [ ] Preserve temporal-result and witness display.
- [ ] Add a representative `5.0` career graph.
- [ ] Keep renderer JSON outside persistence contracts.

### 11.3 Maintained examples

- [ ] Replace the Model 4 semantic-spine example with a `5.0` example.
- [ ] Port the two-context reusable-technology example.
- [ ] Port the temporal-query example.
- [ ] Update terminology and commands.
- [ ] Run all maintained examples and viewers from `tools/verify.py`.

Acceptance gate: every maintained example and viewer is generated from the
`5.0` implementation.

## 12. Phase 8 — Remove legacy executable schemas

- [ ] Remove `model4_ontology()`.
- [ ] Remove `model_v0_5_ontology()`.
- [ ] Remove their public exports.
- [ ] Remove or rename misleading legacy-only constants.
- [ ] Remove obsolete fixtures and tests.
- [ ] Record every removal as ported, superseded, or historical.
- [ ] Remove compact `uses` and `associated_with` from executable code.
- [ ] Remove legacy Context start, end, and status from executable code.
- [ ] Retain historical design documents and lineage references.

Acceptance gate: the runtime package contains one maintained ontology and no
accidental legacy support surface.

## 13. Phase 9 — Documentation and release transition

- [ ] Update `CURRENT.md` and the version ledger.
- [ ] Mark ontology `5.0` as the current executable ontology.
- [ ] Mark `4` and `0.5` as historical executable predecessors.
- [ ] Record that compatibility guarantees begin no earlier than `caron 1.0`.
- [ ] Keep migration explicitly deferred.
- [ ] Update the package-boundary document and architecture-contract version.
- [ ] Update the package implementation overview and README.
- [ ] Update specification implementation-status metadata without changing
      accepted ontology semantics.
- [ ] Change the package version to `0.2.0` and refresh `uv.lock`.
- [ ] Review and minimize `caron.__all__`.

## 14. Phase 10 — Final acceptance

- [ ] Run formatting, Ruff, and strict mypy.
- [ ] Run all deterministic and generative tests.
- [ ] Run all maintained examples and viewers.
- [ ] Build the source distribution and wheel.
- [ ] Install the wheel in a clean temporary environment.
- [ ] Smoke-test the installed public API.
- [ ] Review the final implementation against every section 16.1 obligation.
- [ ] Promote the private development factory to public
      `career_ontology_v5_0()` with exact version `5.0` only after the full
      conformance gate passes; update tests, fixtures, examples, and viewers
      to the accepted identity and rerun the full gate.
- [ ] Commit the acceptance transition.
- [ ] Push the implementation branch for review.
- [ ] Merge only after the complete verification gate passes.

Acceptance gate: `caron 0.2.0` implements the accepted ontology `5.0` without
claiming deferred migration, storage, or query-contract capabilities.
