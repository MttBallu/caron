# Neo4j structural retrieval: step 5

`caron/adapters/neo4j_retrieval.py` evaluates the frozen draft M2-A `ReusableEntityMatches` patterns privately, against one already projected snapshot. It does not publish a new query API or construct a `GraphView`. `retrieve_match_rows(driver, person_id=..., target_id=..., expected_realisation_id=..., expected_source_state_id=..., database=...)` returns two tuples of plain typed rows and the copied snapshot identity and coverage. The optional source-state ID must match when the caller supplies one.

All checks and both patterns execute in one managed read transaction. The evaluator checks one active profile 0.1 marker, the exact ontology and realisation identity, the requested Person and Learnable concept labels, and selects allowed activity-resource kinds from the stored target kind: `Technology → uses_technology`, `Language → uses_language`, `Method → applies | draws_on`, `Subject → draws_on`. IDs remain query parameters. Query results contain domain assertion IDs in separate `learns`, `performs`, `occurs_in`, and `resource_relation` roles. There is no `DISTINCT`, grouping, context inheritance, temporal filter, `exposed_to` match, or implied relation. Match order has no temporal meaning.

The learning branch follows the `CaronRelation` node's `CARON_SOURCE`, `CARON_TARGET`, and `CARON_Q_CONTEXT` links. The activity branch joins three `CARON_DIRECT` assertions through the requested Person, Activity, its local Context, and the requested resource. The match rows preserve the activity-resource relation's original `kind`; `applies` and `draws_on` remain separate even for the same Method and Activity. Request diagnostics and construction of typed public-style matches, supports and a reference-closed view belong to step 6.

Unit tests check snapshot mismatch, parameter use, target-kind filtering, and distinct support rows. The augmented live test projects the frozen C01 learning-only and C02 activity-only cases as **separate** accepted realisations, checks their exact bindings and support IDs, then projects the GEANT4 and whole-career fixtures as before. It ends with the whole-career snapshot, so the database remains inspectable after a successful run. Against the dedicated disposable Community `2026.09.0` container, after pulling the experiment branch:

```bash
CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 uv run --env-file .env --group dev --extra neo4j pytest -q -s tests/integration/test_neo4j_live_projection.py
```

The command replaces snapshots and requires the existing explicit write opt-in. A passing result is the step 5 live gate for C01/C02 and snapshot identity; the remaining eight cases, target-kind variants, empty coverage and adversarial combinations are assessed in step 7.
