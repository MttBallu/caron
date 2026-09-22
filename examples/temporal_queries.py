"""Exercise ontology 5.0 temporality on three Python-use contexts."""

from caron import (
    ACTIVITY,
    CONTEXT,
    PERSON,
    TECHNOLOGY,
    Accepted,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    RealisationCandidate,
    RelationAssertion,
    TemporalMatchMode,
    TemporalWindow,
    before,
    covered_months,
    select_activities_in_window,
    validate_candidate,
)
from caron.ontology import career_ontology_v5_0
from caron.temporal import TemporalExtent


def labelled(entity_id: str, kind: str, label: str) -> Entity:
    return Entity(entity_id, kind, (Property("label", label),))


def build_candidate() -> RealisationCandidate:
    """Build the ALICE, PhD synthetic-data, and jax-geopro realisation."""

    ontology = career_ontology_v5_0()
    person = labelled("person:matteo", PERSON, "Mattéo")
    alice = Entity(
        "context:alice-project",
        CONTEXT,
        (
            Property("label", "ALICE data-analysis project"),
            Property("temporal_extent", TemporalExtent.closed("2021-11", "2022-02")),
        ),
    )
    phd = Entity(
        "context:phd",
        CONTEXT,
        (
            Property("label", "PhD in nuclear physics"),
            Property("temporal_extent", TemporalExtent.closed("2022-10", "2025-10")),
        ),
    )
    synthetic = labelled(
        "context:synthetic-data-work",
        CONTEXT,
        "Synthetic-data generation work",
    )
    jax_geopro = Entity(
        "context:jax-geopro",
        CONTEXT,
        (
            Property("label", "jax-geopro project"),
            Property(
                "temporal_extent",
                TemporalExtent.ongoing("2026-04", as_of="2026-09"),
            ),
        ),
    )
    alice_activity = labelled(
        "activity:analyse-alice-data",
        ACTIVITY,
        "Analyse ALICE collision data",
    )
    synthetic_activity = labelled(
        "activity:build-synthetic-dataset",
        ACTIVITY,
        "Build a labelled synthetic training dataset",
    )
    jax_activity = labelled(
        "activity:implement-discrete-measure-losses",
        ACTIVITY,
        "Implement losses for discrete measures",
    )
    python = labelled("technology:python", TECHNOLOGY, "Python")

    relations = (
        RelationAssertion(
            "relation:synthetic-part-of-phd",
            "part_of",
            EntityRef(synthetic.id),
            EntityRef(phd.id),
        ),
        RelationAssertion(
            "relation:matteo-performs-alice",
            "performs",
            EntityRef(person.id),
            EntityRef(alice_activity.id),
        ),
        RelationAssertion(
            "relation:matteo-performs-synthetic",
            "performs",
            EntityRef(person.id),
            EntityRef(synthetic_activity.id),
        ),
        RelationAssertion(
            "relation:matteo-performs-jax",
            "performs",
            EntityRef(person.id),
            EntityRef(jax_activity.id),
        ),
        RelationAssertion(
            "relation:alice-activity-occurs-in",
            "occurs_in",
            EntityRef(alice_activity.id),
            EntityRef(alice.id),
        ),
        RelationAssertion(
            "relation:synthetic-activity-occurs-in",
            "occurs_in",
            EntityRef(synthetic_activity.id),
            EntityRef(synthetic.id),
        ),
        RelationAssertion(
            "relation:jax-activity-occurs-in",
            "occurs_in",
            EntityRef(jax_activity.id),
            EntityRef(jax_geopro.id),
        ),
        RelationAssertion(
            "relation:alice-uses-python",
            "uses_technology",
            EntityRef(alice_activity.id),
            EntityRef(python.id),
        ),
        RelationAssertion(
            "relation:synthetic-uses-python",
            "uses_technology",
            EntityRef(synthetic_activity.id),
            EntityRef(python.id),
        ),
        RelationAssertion(
            "relation:jax-uses-python",
            "uses_technology",
            EntityRef(jax_activity.id),
            EntityRef(python.id),
        ),
    )
    return RealisationCandidate(
        id="realisation:temporal-reference",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(
            person,
            alice,
            phd,
            synthetic,
            jax_geopro,
            alice_activity,
            synthetic_activity,
            jax_activity,
            python,
        ),
        relations=relations,
        coverage=Coverage(
            CoverageStatus.SELECTIVE,
            "ALICE, PhD synthetic-data, and jax-geopro Python activities",
        ),
    )


def main() -> None:
    validation = validate_candidate(career_ontology_v5_0(), build_candidate())
    if not isinstance(validation, Accepted):
        for diagnostic in validation.diagnostics:
            print(f"[{diagnostic.code}] {diagnostic.message}")
        raise SystemExit(1)
    realisation = validation.realisation

    print("COVERED MONTHS")
    for context_id in (
        "context:alice-project",
        "context:phd",
        "context:synthetic-data-work",
        "context:jax-geopro",
    ):
        count_result = covered_months(realisation, context_id)
        bounds = f"{count_result.minimum}..{count_result.maximum}"
        print(f"  {context_id}: {count_result.kind.value} {bounds}")

    print("\nORDERING")
    for left, right in (
        ("activity:analyse-alice-data", "activity:build-synthetic-dataset"),
        (
            "activity:build-synthetic-dataset",
            "activity:implement-discrete-measure-losses",
        ),
    ):
        order_result = before(realisation, left, right)
        print(f"  {left} < {right}: {order_result.classification.value}")

    print("\nPOSSIBLE ACTIVITY MATCHES IN 2022")
    view = select_activities_in_window(
        realisation,
        TemporalWindow.closed("2022-01", "2022-12"),
        mode=TemporalMatchMode.POSSIBLE,
    )
    for match in view.results:
        print(f"  {match.entity.entity_id}: {match.classification.value}")


if __name__ == "__main__":
    main()
