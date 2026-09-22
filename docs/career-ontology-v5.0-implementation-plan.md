---
kind: implementation_plan
status: active
date: 2026-09-22
ontology_id: caron.career-model
ontology_target: "5.0"
package_target: "0.2.0"
architecture_contract_target: "0.3"
current_phase: phase_2_exact_schema
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

- [ ] Add `Collective`, `Language`, and `Credential` concept constants.
- [ ] Define all 13 exact concept kinds.
- [ ] Require `label: Text` on every concept.
- [ ] Define optional `Context.temporal_extent: TemporalExtent`.
- [ ] Define required `Proposition.content: Text`.
- [ ] Define required `Proposition.context: EntityReference[Context]`.
- [ ] Define optional `Credential.awarded_in: YearMonth`.
- [ ] Exclude generic Context status and standalone start/end properties.

### 6.2 Endpoint families

- [ ] Define internal `Agent` endpoint kinds.
- [ ] Define internal `Learnable` endpoint kinds.
- [ ] Define internal `IntellectualResource` endpoint kinds.
- [ ] Ensure family names cannot be used as entity kinds.

### 6.3 Relations and qualifiers

- [ ] Define all 31 exact relation kinds.
- [ ] Define every source- and target-kind set.
- [ ] Define every required and optional qualifier.
- [ ] Require the `participates_in.role` qualifier.
- [ ] Add optional `participates_in.organization`.
- [ ] Require `collective_membership.context` and `.role`.
- [ ] Require `organization_association.role`.
- [ ] Split compact `uses` into `uses_technology` and `uses_artifact`.
- [ ] Add `uses_language` and `native_language`.
- [ ] Add `modifies`.
- [ ] Add all four credential relations.
- [ ] Add `addresses` and `bears_on`.

### 6.4 Cardinalities

- [ ] Require one or more performers for each Activity.
- [ ] Require exactly one `occurs_in` for each Activity.
- [ ] Require exactly one `awarded_to` for each Credential.
- [ ] Require one or more `awarded_by` for each Credential.
- [ ] Require one or more `obtained_through` for each Credential.
- [ ] Declare zero or more `evidenced_by` for each Credential.

### 6.5 Exactness tests

- [ ] Assert exact ontology identity and version.
- [ ] Assert the exact 13-concept inventory and property signatures.
- [ ] Assert the exact 31-relation inventory, endpoints, and qualifiers.
- [ ] Assert all six cardinality declarations.
- [ ] Assert all global-invariant declarations.
- [ ] Assert that the complete schema passes ontology self-validation.

Acceptance gate: the immutable executable schema exactly represents sections
5–10 of the accepted specification.

## 7. Phase 3 — Local record validation

- [ ] Reject blank entity and relation identifiers.
- [ ] Reject leading and trailing identifier whitespace.
- [ ] Preserve separate entity and relation identifier namespaces.
- [ ] Never infer kind or meaning by parsing identifiers.
- [ ] Reject blank required labels, proposition content, and roles.
- [ ] Preserve the validity of duplicate human labels.
- [ ] Validate `Credential.awarded_in` as `YearMonth`.
- [ ] Preserve unknown property, qualifier, endpoint, and reference checks.
- [ ] Preserve duplicate property- and qualifier-name checks.
- [ ] Freeze stable diagnostic codes for the new rules.

Acceptance gate: every entity and relation assertion is locally valid before
graph-wide validation begins.

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
- [ ] Commit the acceptance transition.
- [ ] Push the implementation branch for review.
- [ ] Merge only after the complete verification gate passes.

Acceptance gate: `caron 0.2.0` implements the accepted ontology `5.0` without
claiming deferred migration, storage, or query-contract capabilities.
