# Neo4j whole-snapshot projection: step 3

This experimental adapter implements `caron-neo4j-projection-profile-v0.1.md` against `caron` source commit `eae69a79f080eaf11db99c27d00bba619f1bdc2b` (Ontology 5.0). The profile and frozen input manifest are the experiment references, kept separately from this code branch. The adapter is in `caron/adapters/neo4j_projection.py`; it accepts only a `ValidatedRealisation`, and Neo4j is a replaceable query projection.

`prepare_snapshot` builds the two assertion shapes and preserves domain IDs, text, reference links, month values, temporal end alternatives, coverage, and optional loader source-state metadata. `project_snapshot` checks that its database is empty or has a matching Caron projection marker, deletes the previous snapshot, writes the replacement, and verifies physical counts in one managed write transaction. If a write fails, the transaction rolls back, leaving the previous committed snapshot. `install_projection_constraints` installs four Community uniqueness constraints as a separate setup operation; existence, semantic rules, and cross-shape assertion ID collisions remain Caron's responsibility.

For the live gate, use a dedicated Neo4j Community `2026.09.0` test database. The live test replaces any existing matching Caron projection in that database. With the optional driver installed, run:

```bash
uv sync --group dev --extra neo4j
export CARON_NEO4J_EXPERIMENT_URI='bolt://localhost:7687'
export CARON_NEO4J_EXPERIMENT_USER='neo4j'
export CARON_NEO4J_EXPERIMENT_PASSWORD='<your test password>'
export CARON_NEO4J_EXPERIMENT_DATABASE='neo4j'
uv run --group dev --extra neo4j pytest -q -s tests/integration/test_neo4j_live_projection.py
```

The live test asserts the exact server version and Community edition, installs constraints, loads the pinned GEANT4 and whole-career YAML through the accepted reader, compares committed physical counts and domain IDs with each validated source, checks copied source-state metadata, and injects a failure after deleting a previous snapshot to verify rollback. Expected counts are 7 nodes/6 relationships and 77 nodes/113 relationships respectively. Capture the image digest and platform (or installation identifier), effective Cypher setting, printed server and driver versions, executed commit, and fixture source-state hashes in the run report. The test skips when `CARON_NEO4J_EXPERIMENT_URI` is absent; a skip is **not** evidence that the step 3 database gate passed.

Local checks are `uv run --group dev ruff check .`, `uv run --group dev mypy caron tests`, and `uv run --group dev pytest -q`. The unit checks cover the two frozen fixtures, alternative temporal-end encoding, and the managed transaction's failure path using an instrumented test driver. They do not execute Cypher. Extraction and semantic round-trip belong to step 4.
