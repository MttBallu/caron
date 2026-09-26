# Step 7: adversarial M2-A conformance suite

`tests/fixtures/neo4j_m2a.py` transcribes the separate C01–C10 realisations and expected match/support records from the frozen 2026-09-23 draft `m2a-structural-matches-contract-experiment.md`. It also includes C06 without personal `performs`, C01 for the other three Learnable kinds, and C02 for `Language`, both `Method` relations and `Subject`: **18 separately validated fixtures**. The expected result for each lists complete typed matches, named assertion IDs, and exact entity and relation IDs of the view. No order between matches is interpreted as career time.

`tests/unit/test_neo4j_m2a_cases.py` checks that every realisation passes ontology 5.0 validation and independently evaluates its two patterns using the existing private in-memory algebra. It compares all bindings and individual witness sets with the draft's expectations. This algebra is a comparison at the operator level; it does not supply the Neo4j expected rows. An additional unit probe checks `query.unsupported_ontology` when the pure result assembler receives a validated source of another ontology version. The Neo4j projection profile itself rejects such a snapshot before request evaluation.

The live suite now projects each of the 18 fixtures separately, evaluates `Request("p", "x")`, and compares exact matches, support roles, source records, view records, request, identity, and coverage. It verifies empty matches and empty views for C05, the C06 variant and C08; C06 excludes the collective performer's support and C09 excludes the context-parent link. Five separate live requests check unknown Person, wrong Person kind, unknown target, and wrong target kind (including an Artifact). Every test restores the whole-career snapshot, and the fixture/rollback test still runs independently. Thus pytest collects **24 live cases**; a skipped local live test is not evidence that Cypher passed.

Against the dedicated disposable Community `2026.09.0` container, after pulling the experiment branch:

```bash
CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 uv run --env-file .env --group dev --extra neo4j pytest -v -s tests/integration/test_neo4j_live_projection.py
```

This suite replaces the narrower two-case live test from step 6. A failure can be classified from the stages: candidate validation means a fixture/schema discrepancy; incorrect binding or support in `result.matches` means Cypher retrieval or result assembly; unexpected selected view records mean assembly/closure; a rejected request with the wrong code means request validation. A passing local suite establishes fixture and algebra checks, while the step-7 database gate awaits the live command above.
