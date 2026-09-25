# Neo4j whole-snapshot projection: step 3

This experimental adapter implements `caron-neo4j-projection-profile-v0.1.md` against `caron` source commit `eae69a79f080eaf11db99c27d00bba619f1bdc2b` (Ontology 5.0). The profile and frozen input manifest are the experiment references, kept separately from this code branch. The adapter is in `caron/adapters/neo4j_projection.py`; it accepts only a `ValidatedRealisation`, and Neo4j is a replaceable query projection.

`prepare_snapshot` builds the two assertion shapes and preserves domain IDs, text, reference links, month values, temporal end alternatives, coverage, and optional loader source-state metadata. `project_snapshot` checks that its database is empty or has a matching Caron projection marker, deletes the previous snapshot, writes the replacement, and verifies physical counts in one managed write transaction. If a write fails, the transaction rolls back, leaving the previous committed snapshot. `install_projection_constraints` installs four Community uniqueness constraints as a separate setup operation; existence, semantic rules, and cross-shape assertion ID collisions remain Caron's responsibility.

Use an existing Neo4j server if its URI reaches a **dedicated experiment database** and the read-only preflight confirms the pinned Community `2026.09.0` target. The Python `neo4j` package is the driver; it does not start the server. Docker is optional and useful when you need an isolated instance of the exact pinned release.

Copy the tracked placeholder file to a local `.env`, set your actual URI, username, password, and database name there, and restrict the file to your user. The `.env` file is ignored by Git; it is still plaintext on your machine. Preserve the URI scheme supplied by your server (for example, `neo4j+s://` for a TLS connection). No additional dotenv package is needed: `uv run --env-file` loads the variables for the command. Do not paste credentials into the repository or test output. Then run:

```bash
cp .env.example .env
chmod 600 .env
# Edit .env with your connection details before continuing.
uv sync --group dev --extra neo4j
uv run --env-file .env --group dev --extra neo4j python scripts/neo4j_projection_preflight.py
```

The preflight verifies connectivity, the server version/edition, support for an explicitly selected `CYPHER 25` query, and whether the target graph is empty or already contains a Caron projection. The projector prefixes its Cypher statements with `CYPHER 25`; it does not depend on or inspect the database's default language setting. The preflight makes no writes and does not print credentials. If its target differs from the frozen input, record that deviation before running the experiment. If it reports other data, use a separate disposable database or server.

An Aura instance reporting `5.27-aura enterprise` passes the connectivity and Cypher 25 probes, but does not meet the frozen `2026.09.0 Community` gate. A clean database has no Caron labels yet; the occupancy check uses label strings and dynamic property access so this expected state does not produce missing-token warnings. An Aura run could be recorded separately as an exploratory compatibility check, after explicitly choosing a disposable target and adapting the version assertion; it would not replace the Community gate.

The live test **replaces the snapshot** in that database. After confirming that the target is disposable, opt in explicitly:

```bash
CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 uv run --env-file .env --group dev --extra neo4j pytest -q -s tests/integration/test_neo4j_live_projection.py
```

The live test asserts the exact server version and Community edition, installs constraints, loads the pinned GEANT4 and whole-career YAML through the accepted reader, compares committed physical counts and domain IDs with each validated source, checks copied source-state metadata, and injects a failure after deleting a previous snapshot to verify rollback. Expected counts are 7 nodes/6 relationships and 77 nodes/113 relationships respectively. Capture the image digest and platform (or installation identifier), effective Cypher setting, printed server and driver versions, executed commit, and fixture source-state hashes in the run report. The test skips without the connection variables and explicit write opt-in; a skip is **not** evidence that the step 3 database gate passed.

Local checks are `uv run --group dev ruff check .`, `uv run --group dev mypy caron tests`, and `uv run --group dev pytest -q`. The unit checks cover the two frozen fixtures, alternative temporal-end encoding, and the managed transaction's failure path using an instrumented test driver. They do not execute Cypher. Extraction and semantic round-trip belong to step 4.
