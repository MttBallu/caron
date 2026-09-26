# Neo4j query projection experiment — review v0.1

**Decision:** Keep the mixed mapping as an **optional, experimental query projection** of a `ValidatedRealisation`. It passed the frozen fidelity and M2-A retrieval gates on the pinned Community server. Do not promote it to authoritative persistence or the default query engine on this evidence. The next implementation decision is whether its Cypher and inspectable graph provide enough practical benefit to justify the full-snapshot adapter cost; no measured comparison against the in-memory evaluator has been run.

## 1. Scope and evidence

The frozen input manifest `caron-neo4j-experiment-inputs-v0.1.md` pins source commit `eae69a79f080eaf11db99c27d00bba619f1bdc2b`, executable ontology `caron.career-model/5.0`, the 2026-09-23 **draft** M2-A `ReusableEntityMatches` oracle and the GEANT4, whole-career, and ten-case fixtures. The separately preserved mapping reference is `caron-neo4j-projection-profile-v0.1.md`. The implementation and gates are in `caron/adapters/neo4j_*.py`, `tests/unit/test_neo4j_*.py`, `tests/integration/test_neo4j_live_projection.py`, and the [step 3](neo4j-projection-step3.md) through [step 8](neo4j-projection-step8.md) notes. The manifest and profile are not duplicated on this branch.

The user reports passing live runs against Neo4j **2026.09.0 Community**, explicitly selected **Cypher 25**, and Python driver **6.3.1**: snapshot counts and rollback; semantic reconstruction; the step-7 suite of **24** independently reported live tests (18 case/variant realisations, five invalid requests, one fixture/rollback test); and the focused step-8 whole-career test. Local Ruff, mypy and pytest passed at step 8 (**507 passed, 25 live skipped locally**). The user supplied the step-8 output, which includes the source-state ID and timings. The executed image digest and the user's checked-out Git commit were not captured, and the live results were reported by the user rather than reproduced in this workspace.

| Gate | Observed result | Boundary of the evidence |
| --- | --- | --- |
| Atomic whole-snapshot replacement | GEANT4 7 nodes/6 relationships; career 77 nodes/113 relationships; injected failure left the previous committed snapshot intact. | One isolated database, full replacement; no concurrent writers or incremental updates. |
| Inverse mapping | Typed records, domain IDs, qualifiers, property references, temporal alternatives and coverage round-tripped; malformed storage probes were rejected locally. | Malformed-link and cross-shape-collision probes use constructed storage rows, not manual corruption of the live database. |
| Draft query contract | C01–C10, variants, empty cases and request diagnostics passed live; C06 attribution, C07 alternative supports and C09 local contexts remained distinct. | Only this draft M2-A request; no interpretation, temporal filtering or public API acceptance. |
| Whole-career sampling | GEANT4 3 matches/7 support assertions; Monte Carlo transport 1/3; English 1/3; Python 8/24, with exact source witnesses and reference-closed views. | Four selected targets in one 69-entity/97-assertion fixture, not a workload or scalability study. |

## 2. Verdicts against the experiment questions

| Dimension | Verdict | Reason |
| --- | --- | --- |
| **Mapping fidelity** | **Pass for profile 0.1 and the tested ontology 5.0 records.** | The two assertion shapes retain identified relations and typed values. Inverse reconstruction revalidates ontology 5.0; whole-career and focused alternatives round-trip. Physical encoding links never become domain facts. |
| **Query-contract fidelity** | **Pass for the frozen draft M2-A request.** | Two parameterized Cypher branches yield exact bindings and named source assertion IDs. Assembly checks those IDs against reconstructed records in the same read transaction and selects only supporting records plus referenced entities. Empty matches preserve request, source and coverage. |
| **Operational usefulness** | **Promising for graph inspection and this structural query, with an unresolved cost.** | The Cypher patterns follow the two represented evidence shapes directly. The adapter currently performs full extraction and ontology validation for every request before running the retrieval branches. No comparison shows it improves maintenance or query work over the private in-memory algebra. |

The original question about the **mixed mapping** has a qualified positive answer. `learns` is visibly a relation node with a Context link, while the three activity assertions form a compact path through direct relationships. A reviewer can trace C01, C02 and C07 from Cypher columns to domain IDs and typed supports; the inverse has deterministic rules for both shapes. The cost is a special-case branch in projection, decoding and query construction. The physical shapes are storage details, not two kinds of ontology assertions. This is clear enough for the tested query; other queries may change that assessment.

## 3. Mapping alternatives and constraints

| Choice | Mixed mapping used in the spike | Uniform assertion-node design, analytical comparison only |
| --- | --- | --- |
| Direct activity branch | Three `CARON_DIRECT` edges with `kind` properties. | Three assertion nodes, each traversed by `CARON_SOURCE` and `CARON_TARGET` links. |
| Learning branch | One `CaronRelation` node with source, target and Context links. | The same three-link pattern. |
| Inverse mapping | Two assertion decoders and checks that a kind uses its assigned shape. | One assertion-node decoder for all kinds, plus qualifier-specific checks. |
| Assertion ID uniqueness | One constraint on `CARON_DIRECT.id` and one on `CaronRelation.id`; cross-shape collisions need adapter validation. | One constraint across assertion nodes could guard assertion IDs regardless of relation kind. Entity/assertion cross-category identity would still need checking. |
| Predicted GEANT4 storage | 7 nodes, 6 relationships. | 10 nodes, 9 relationships: 5 entities, 4 assertion nodes, 1 marker; 8 endpoint links and 1 Context qualifier link. |
| Predicted whole-career storage | 77 nodes, 113 relationships. | 167 nodes, 203 relationships: 69 entities, 97 assertion nodes, 1 marker; 194 endpoint links, 6 qualifier links and 3 Proposition Context links. |

The uniform design would simplify physical assertion identity and the inverse, but lengthen the activity query and add storage links for each direct assertion. Its correctness, Cypher plans and runtime were **not tested** here. A domain-specific relationship type for each of the 27 direct kinds could make some Cypher patterns shorter, but would complicate generic handling and per-type uniqueness; it was likewise not implemented. Flattening the `learns` Context into a string property would shorten a pattern but lose its explicit graph reference; it is not recommended for this profile. The tested mixed mapping should remain the baseline if this optional adapter is continued; compare a uniform implementation only when another query exposes a concrete readability or identity problem.

Four uniqueness constraints were installed by the live suite: `CaronEntity.id`, `CaronRelation.id`, `CARON_DIRECT.id`, and the `CaronProjection.marker`. They guard uniqueness **within** their physical categories. They do not enforce property existence, endpoint concept kinds, exactly one source/target or qualifier link, Activity cardinalities, cross-shape IDs, semantic duplicate facts or temporal consistency. `validate_candidate` remains the admission boundary; the strict extractor rejects malformed storage and revalidates it before assembly. No `SHOW CONSTRAINTS` output or independent constraint inventory was captured from the live server.

## 4. Runtime and integration cost

The step-8 source-state ID was `13cbe70f70bb4d825c1f4a88984478fe973ed8a93464948cee212943636ce522`. Reported wall times were **0.585975 s** for whole-career load and **0.065969 s** for a separate full reconstruction. Four requests took **0.368236 s** (GEANT4), **0.170913 s** (Monte Carlo transport), **0.032550 s** (English) and **0.050195 s** (Python), respectively. They ran once in that order; connection and cache warm-up may contribute. They are context, not a throughput estimate or a comparison of Cypher with the in-memory evaluator.

One assembled request executes six read statements in one transaction: fetch all nodes, fetch all relationships, read the marker, read the requested endpoint labels, run the learning branch, and run the activity branch. It reconstructs and validates the entire source graph, including records unrelated to the requested Person or target, before checking the Cypher rows against it. This protects the query result from stale or malformed projection records in the experiment, but means query cost grows with the full snapshot even for a small result. The projection uses whole-snapshot replacement in a dedicated database, not concurrent multi-realisation storage. Driver imports remain in the optional adapter boundary; the core ontology and validator do not depend on Neo4j.

## 5. Decision and follow-up

Keep this branch as evidence that **Neo4j can serve as a query projection** behind Caron's validation boundary. The mixed shape is adequate for M2-A; the result carries no Neo4j element ID or raw driver object, and the ontology remains the authority. Do not merge a public `ReusableEntityMatches` API merely because this private adapter passed: the draft request, diagnostics and result shape require their own contract review.

Before making Neo4j the default query path, measure it against the in-memory evaluator on the **same** validated snapshots and representative requests, and decide how to avoid re-extracting the full graph without weakening snapshot consistency and ontology checks. If the projection becomes long-lived, test refresh/read concurrency, recovery, larger snapshots, schema migration and deployed constraint inventory. A proposal to use Neo4j as **authoritative persistence** must separately specify mutations, validation-before-commit, recovery and migration semantics; this experiment did not test that role. The image digest and executed client commit can be added to this record if they become available, but the missing values do not change the reported conformance verdict.

The [requirements and lessons retrospective](neo4j-projection-retrospective-v0.1.md) compares the four original hypotheses with the results, implementation friction, and planned comparison work that remains untested.
