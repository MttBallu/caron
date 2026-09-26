---
kind: experiment_retrospective
status: draft_for_architecture_review
version: "0.1"
date: 2026-09-26
project: caron
---

# Neo4j projection: requirements and lessons

This retrospective examines what the Neo4j experiment taught us about Caron's implementation, before deciding how to proceed with M2-A. The separately preserved `caron-neo4j-projection-experiment-v0.1.md` stated the initial question and four hypotheses; the [step-9 review](neo4j-projection-review-v0.1.md) records the conformance verdict and run evidence. The plan and `caron-neo4j-projection-profile-v0.1.md` are reference files outside this repository checkout.

## 1. What the experiment was meant to decide

The question was whether an accepted ontology 5.0 realisation could be projected into Neo4j, read back without losing represented facts, and queried for the draft M2-A structural matches with each original assertion in its proper support role. A positive answer would make Neo4j a candidate **query projection**. It would not establish an authoritative store, a public M2-A API, or a performance advantage over in-memory querying.

The original plan asked for three separate verdicts: mapping fidelity, query-contract fidelity, and operational usefulness. Its fourth hypothesis, proportionality, is a judgment about complexity and benefit, rather than a test that passes when the other three pass. This distinction proved essential: the correctness gates passed, while the operational value remains unproven.

| Original requirement or hypothesis | Observation | Assessment |
| --- | --- | --- |
| **H1: preserve ontology 5.0 records.** Retain IDs, endpoints, qualifiers, typed properties, temporal alternatives and coverage; add no domain assertions. | The two pinned snapshots round-tripped as typed records and revalidated. The 69-entity/97-assertion career fixture projected to 77 nodes/113 relationships. Focused probes covered mapping paths absent from that fixture. Missing or duplicated encoding links and cross-shape ID collisions were rejected in constructed-row tests. | **Passed for profile 0.1 and tested shapes.** This is semantic record equality, not reproduction of YAML bytes, comments, or order. Malformed-shape probes were local, not manually corrupted live databases. |
| **H2: retrieve exact draft M2-A matches and minimal supports.** Exercise ten cases, variants, empty results and request errors. | All 24 separately reported step-7 live tests passed according to the user's run. C06 retained personal attribution, C07 kept alternative support paths separate, and C09 retained the local Context. Four whole-career target probes agreed with independent source expectations. | **Passed for the frozen draft request.** It does not accept that request as a public contract or establish behavior for other queries. |
| **H3: keep the result intelligible without Neo4j concepts.** Retain request, source identity, coverage, matches, support IDs and a closed view. | The private assembled result contains domain IDs, typed match records, coverage and `GraphView`, with no Neo4j element IDs, paths or driver objects. Assembly reconstructs source records from the same committed snapshot used by Cypher. | **Passed at the result-value boundary.** The evaluator and result assembly still live together in a Neo4j adapter module; a backend-independent public API has not been extracted or accepted. |
| **H4: remain proportionate.** Use one mapping across fixtures without special cases and determine whether graph traversal justifies the adapter. | The same profile handled the career fixture without fixture-specific rules. The implementation requires two physical assertion shapes, a strict inverse, consistency checks and full-snapshot extraction and validation for each assembled request. There is no comparison against an in-memory evaluator on equal inputs. | **Partly demonstrated, decision open.** The mapping is explainable for M2-A, but its maintenance and runtime cost has not been justified by a measured benefit. |

## 2. What worked well

**The admission boundary held.** Projection accepts a `ValidatedRealisation`; Neo4j does not decide ontology validity. Reconstruction builds a candidate and invokes the existing validator. The database's four uniqueness constraints protect IDs within physical categories, while semantic cardinalities, endpoint kinds, qualifier obligations, temporal consistency and cross-shape identity remain Caron's checks. This made the database useful without creating a competing ontology.

**The experiment could falsify more than a happy-path query.** It checked an atomic replacement with injected failure, a typed inverse, malformed storage shapes, exact M2-A supports, invalid requests and successful empty results. The source realisation served as an oracle after execution, rather than as hidden input to the Cypher result. Splitting the live suite into named cases also made it clear which assertions were being exercised.

**Identified assertions survived physical representation.** A direct relation is a Neo4j relationship with its own domain ID; a relation admitting an entity-valued qualifier is a storage node with links to its endpoints and qualifier entity. Both decode to the same `RelationAssertion` type. The learning and activity Cypher branches can return the exact `learns`, `performs`, `occurs_in` and resource assertion IDs, so a displayed binding cannot silently replace its evidence.

**The graph was inspectable.** The user could inspect the projected career graph in Neo4j Browser before proceeding with reconstruction. This is a practical benefit of the projection, although visual inspection is not evidence that the semantic inverse or query contract is correct.

**The adapter stayed outside the core.** The ontology, candidate validator and ordinary public queries do not depend on the Neo4j driver. The snapshot carries ontology, realisation, coverage, profile and optional source-state metadata; storage IDs do not leak into the result. This leaves the experiment reversible at the package architecture level.

## 3. What was awkward or did not establish value

**The physical mapping duplicates semantic knowledge.** Profile 0.1 selects four relation kinds for node encoding and 27 for direct relationships. Projection, extraction and Cypher must agree on that choice. Neo4j can enforce uniqueness only separately for direct relationships and relation nodes, so the adapter checks cross-shape collisions. The uniform assertion-node alternative was compared analytically: it could simplify decoding and assertion ID constraints, but would add nodes and traversals. Its behavior and runtime were not implemented or measured. The mixed design is an adequate experimental baseline, not a settled universal mapping.

**Trusting a query result currently requires reading the whole snapshot.** One assembled request reads all nodes and relationships, reconstructs and revalidates the candidate, checks the marker and endpoints, then runs two Cypher branches, all in one read transaction. This protects against inconsistent or malformed storage, but the work scales with the complete realisation even when one target yields a small view. The separate reconstruction took 0.065969 seconds in the reported career run; the four single-run request times ranged from 0.032550 to 0.368236 seconds. These observations do not isolate Cypher cost, establish throughput, or compare against in-memory evaluation.

**The result contract was tested before becoming a shared interface.** The private Neo4j result has the right draft M2-A fields, but Caron's general in-memory public query catalogue remains temporal and the private algebra covers only part of the M2-A draft. Conformance against an explicit oracle demonstrates query fidelity; it does not yet demonstrate backend interchangeability or that Neo4j simplifies implementation compared with a complete in-memory evaluator.

**The first database environment caused avoidable friction.** The initial credentials reached Aura `5.27-aura Enterprise`, while the frozen gate targeted local `2026.09.0 Community`. `SHOW SETTINGS` was unavailable there, and occupancy checks warned about labels absent from the empty database. The preflight was revised to probe Cypher 25 directly and avoid missing-label warnings; the user then ran the pinned Community container. These were preflight and environment issues, not failures of the domain mapping. They show that a versioned adapter needs a modest, reliable compatibility check and clear isolation from any unrelated database.

**The experiment does not test durable operation.** It replaces one isolated snapshot at a time. It does not cover concurrent refresh and readers, multiple realisations, incremental edits, recovery, migration or deployment constraints. The live report came from the user's local container; the executed image digest and checked-out client commit were not captured. Those limits do not negate the conformance tests, but they matter for reproducibility and any production proposal.

**Some proposed comparison work was not completed.** The projection profile proposed implementing the exercised relation kinds with a uniform assertion-node mapping and asking a reviewer unfamiliar with the implementation to trace C01, C07 and qualified-relation reconstruction. The final comparison instead derived storage counts and likely tradeoffs analytically; it did not run the alternative or record that independent trace review. Likewise, the live database's deployed constraints were installed by the suite but not inventoried independently with `SHOW CONSTRAINTS`. These omissions narrow the mapping-preference and operational-usefulness conclusions; they do not alter the observed mixed-mapping conformance result.

## 4. Answers to the original review questions

| Original question | Answer after the spike |
| --- | --- |
| Does the mixed mapping clarify or obstruct identified relations? | It makes the M2-A patterns traceable and keeps assertion IDs explicit. Its two physical shapes complicate generic projection, inverse mapping and cross-shape uniqueness. No evidence yet favors it over a tested uniform alternative for future queries. |
| Can results be assembled from Neo4j without another source at query time? | Yes, for this isolated snapshot: reconstruction and Cypher run in one read transaction. The authored fixture is an independent test oracle, not a runtime data source. The price is reconstructing the entire snapshot for every request. |
| What does Cypher simplify relative to in-memory querying? | It expresses the two structural traversals clearly and provides an inspectable graph. A maintenance or performance advantage is **not established**, because the complete in-memory M2-A evaluator and equal-input comparison have not been built. |
| Which constraints protect the projection? | Four uniqueness constraints cover entity, direct assertion, qualified assertion and marker IDs within their physical categories. They do not enforce ontology conformance, required links, properties, cross-shape IDs or semantic duplicate facts. |
| Is an optional projection useful before authoritative persistence? | It is technically viable for this draft structural query and graph inspection. Whether the benefit warrants a running database and adapter remains an application decision; this experiment supplies correctness evidence, not that cost-benefit verdict. |

## 5. Architectural consequence before M2-A

The safe conclusion is narrow: **Neo4j can reproduce the tested ontology 5.0 snapshot and the draft M2-A results, but it is not yet Caron's default query engine or durable authority.** The successful result should inform the M2-A contract without letting the Neo4j layout define it.

Before optimizing this adapter, settle one backend-independent request and result contract, including how each match names its minimal supports and how an empty result retains coverage. Implement the same accepted behavior in memory, then compare correctness, code complexity and measured costs on identical realisations. If Neo4j still serves a concrete use, investigate selective result verification or validated snapshot generations so each request need not reconstruct everything; such a change must retain snapshot consistency and the admission boundary. An authoritative storage design would require a separate experiment and contract.

The existing [step-9 review](neo4j-projection-review-v0.1.md) remains the record of the verdict and exact test evidence. This retrospective records the requirements comparison and the architectural lessons; it does not change ontology 5.0 or accept the draft M2-A API.
