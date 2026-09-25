# Neo4j reconstruction: step 4

`caron/adapters/neo4j_reconstruction.py` reads one profile 0.1 snapshot in a managed Neo4j read transaction. It extracts the raw node and relationship labels, properties, and temporary storage IDs, decodes them into a typed `RealisationCandidate`, and calls the existing ontology 5.0 `validate_candidate`. `extract_snapshot(driver, database="neo4j")` returns the candidate, its validated form, and the optional copied YAML `source_state_id`. Neo4j element IDs are used only to connect rows **within that read transaction**; the reconstructed records use the original domain IDs.

The decoder rejects missing or extra storage fields and labels, unexpected link types, missing or repeated endpoint and qualifier links, a Proposition context link to a non-Context, incomplete temporal slots, unknown relation kinds, duplicate domain IDs across physical shapes, and candidates rejected by ontology validation. It compares semantic records by domain ID, typed properties and qualifiers by name; physical IDs, record order, and YAML formatting do not enter the comparison.

Unit probes exercise the GEANT4 and whole-career fixtures, the distinct absent/unknown/ongoing temporal alternatives, `collective_membership` and `exposed_to`, and malformed or ontologically invalid snapshots. These tests use independently constructed storage rows and do not execute Cypher. The live test reads the **committed** graph back after each fixture projection, compares its typed records and copied source-state metadata with the original validated fixture, and confirms the previous snapshot remains identical after the injected failed replacement.

Against the dedicated, disposable local Community `2026.09.0` container, rerun the augmented live test after updating the experiment branch:

```bash
CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 uv run --env-file .env --group dev --extra neo4j pytest -q -s tests/integration/test_neo4j_live_projection.py
```

The write opt-in is required because this test replaces snapshots. It ends with the whole-career fixture in the database, so the graph remains available for inspection. Record the pytest result alongside the server and driver version, fixture source-state hashes, executed commit, and Docker image digest or local image ID. The local tests establish decoder behavior; successful execution of the augmented live test establishes that the actual Neo4j projection round-trips through this inverse profile. Broader adversarial query behavior remains for steps 5–7.
