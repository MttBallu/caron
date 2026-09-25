# Step 6: assemble the draft M2-A result

`caron/adapters/neo4j_results.py` is a private experiment adapter. `evaluate_projected_matches` accepts a typed `Request(person_id, target_id)` and the expected snapshot identity. It reconstructs the stored snapshot and retrieves structural matches inside the **same Neo4j read transaction**. Its result retains the request, source identity, optional source-state ID and coverage; no driver record or database internal ID enters the result.

The two frozen match variants retain the named assertion IDs: `LearningMatch.learns` and `ActivityResourceMatch.performs`, `.occurs_in`, `.resource_relation`. For each row the adapter resolves the ID to an ontology assertion and checks its kind, direction, endpoints and, for `learns`, its Context qualifier. It unions the selected assertions into a `GraphView`, closes over qualifier and entity-property references, and keeps each match's separate supports. The view contains no inferred assertions. An empty successful query has an empty view and retains request and coverage. Invalid Person/target requests return the proposed diagnostic codes with no view. A different ontology/version cannot be projected under profile 0.1: reconstruction rejects its marker as a storage-profile error before a request can be assembled; the pure assembler has a proposed `query.unsupported_ontology` diagnostic for sources supplied outside this profile.

Against the dedicated disposable Community `2026.09.0` container, after pulling the experiment branch:

```bash
CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 uv run --env-file .env --group dev --extra neo4j pytest -v -s tests/integration/test_neo4j_live_projection.py
```

The C01 and C02 tests now additionally exercise the single-transaction assembled result and compare the view's exact entity and assertion IDs; the fixture/rollback test remains the third case. Each case restores the whole-career snapshot after its check. Local unit, Ruff and mypy checks pass; the live step-6 check awaits the user's container. Step 7 will exercise all ten adversarial cases, target-kind alternatives and request diagnostics.
