"""Read-only check of the pinned Neo4j experiment target.

Load local credentials with ``uv run --env-file .env --extra neo4j``.
The script reports server metadata and graph occupancy, never credentials.
"""

import os

from neo4j import GraphDatabase


def main() -> None:
    required = (
        "CARON_NEO4J_EXPERIMENT_URI",
        "CARON_NEO4J_EXPERIMENT_USER",
        "CARON_NEO4J_EXPERIMENT_PASSWORD",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")
    uri, user, password = (os.environ[name] for name in required)
    database = os.environ.get("CARON_NEO4J_EXPERIMENT_DATABASE", "neo4j")
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session(database=database) as session:
            component = session.run(
                "CALL dbms.components() YIELD name, versions, edition "
                "WHERE name = 'Neo4j Kernel' "
                "RETURN versions[0] AS version, edition"
            ).single(strict=True)
            cypher = session.run("CYPHER 25 RETURN 25 AS version").single(
                strict=True
            )
            graph = session.run(
                "MATCH (n) RETURN count(n) AS nodes, "
                "count(CASE WHEN n:CaronProjection AND n.marker = 'active' "
                "THEN 1 END) AS markers, "
                "count(CASE WHEN n:CaronProjection OR n:CaronEntity OR n:CaronRelation "
                "THEN 1 END) AS owned"
            ).single(strict=True)

    print(f"Database: {database}")
    print(f"Server: {component['version']} {component['edition']}")
    print("Cypher language: 25 (selected explicitly by the projector)")
    print(
        f"Existing nodes: {graph['nodes']}; "
        f"Caron projection markers: {graph['markers']}"
    )
    if (
        component["version"] != "2026.09.0"
        or component["edition"].lower() != "community"
        or cypher["version"] != 25
    ):
        raise SystemExit("Server differs from the frozen experiment target")
    if graph["nodes"] and (graph["markers"] != 1 or graph["owned"] != graph["nodes"]):
        raise SystemExit(
            "Database contains other data; use an isolated experiment database"
        )
    print("Read-only preflight passed; no snapshot was written.")


if __name__ == "__main__":
    main()
