# Step 8: whole-career query probe

This gate uses the already frozen `caron/data/career-across-contexts-v0.1.yaml` (69 domain entities and 97 assertions; projection counts 77 nodes and 113 relationships). `tests/fixtures/neo4j_career.py` fixes source assertion IDs and computes complete match/support expectations directly from the validated source records. The local unit test checks these IDs before a Neo4j query runs. No new ontology or fixture-specific production rule is introduced.

| Request for `person:matteo` | Learning matches | Activity matches | Expected minimal view |
| --- | ---: | ---: | ---: |
| `technology:geant4` | 1 | 2 | 7 entities, 7 assertions |
| `method:monte-carlo-transport` | 0 | 1 | 4 entities, 3 assertions |
| `language:english` | 0 | 1 | 4 entities, 3 assertions |
| `technology:python` | 0 | 8 | 18 entities, 24 assertions |

All Learnable targets in this whole-career fixture have at least one match; successful empty results were tested separately in C05, C06's variant and C08. The GEANT4 match uses the local `context:geant4-course` from its `learns` qualifier and two distinct activity contexts. The other requests exercise `applies`, `uses_language`, and a larger `uses_technology` join across contexts.

The new `test_live_whole_career_m2a_queries` projects the fixture once, reconstructs and compares all typed entity and assertion records and metadata, then checks every result against independently joined source records. It checks the request, coverage, source-state ID, typed bindings and named support IDs, plus exact view relation/entity sets and reference closure. The test leaves the whole-career snapshot installed. It prints wall times for the transactional load, full reconstruction and each query as context; there are no performance thresholds or benchmark claims.

The current query path performs a full graph extraction and ontology revalidation on **every request**, then reads the marker, requested endpoints and two Cypher branches in the same transaction: six read statements per request. This keeps reconstruction and retrieval consistent for the experiment, but adds adapter work and whole-snapshot cost. Step 9 should weigh that complexity against the clarity and usefulness of the Cypher patterns; a future optimized path would require its own consistency and validation design.

Against the dedicated disposable Community `2026.09.0` container, after pulling the experiment branch:

```bash
CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 uv run --env-file .env --group dev --extra neo4j pytest -v -s tests/integration/test_neo4j_live_projection.py -k whole_career_m2a_queries
```

## Reported live run, 2026-09-26

The user reports that the focused live test **passed** on Neo4j Community `2026.09.0` with explicit Cypher 25 and Python driver `6.3.1`. The fixture source-state ID was `13cbe70f70bb4d825c1f4a88984478fe973ed8a93464948cee212943636ce522`. The test compared the reconstructed records and each match, support and view with the validated source. The resulting measurements were:

| Operation / target | Matches | View entities | View assertions | Wall time (s) |
| --- | ---: | ---: | ---: | ---: |
| Snapshot load | — | — | — | 0.585975 |
| Full reconstruction | — | — | — | 0.065969 |
| `technology:geant4` | 3 | 7 | 7 | 0.368236 |
| `method:monte-carlo-transport` | 1 | 4 | 3 | 0.170913 |
| `language:english` | 1 | 4 | 3 | 0.032550 |
| `technology:python` | 8 | 18 | 24 | 0.050195 |

This is one run with mixed query order and possible warm-up effects. The timings characterize this particular whole-snapshot adapter path; they do not establish comparative performance or a throughput target. The executed image digest and local repository commit were not captured in the reported output. **Step 8's live gate passed.**
