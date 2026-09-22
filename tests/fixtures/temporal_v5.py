"""Ontology 5.0 temporal-query fixture spanning four career contexts."""

from caron import (
    ACTIVITY,
    CONTEXT,
    PERSON,
    TECHNOLOGY,
    Property,
    RealisationCandidate,
    TemporalExtent,
)
from tests.fixtures.v5 import assertion, labelled, v5_candidate


def temporal_v5_candidate() -> RealisationCandidate:
    """Build dated, inherited, ongoing, and undated temporal cases."""

    person = labelled("person:matteo", PERSON, "Mattéo")
    alice = labelled(
        "context:alice-project",
        CONTEXT,
        "ALICE data-analysis project",
        Property("temporal_extent", TemporalExtent.closed("2021-11", "2022-02")),
    )
    phd = labelled(
        "context:phd",
        CONTEXT,
        "PhD in nuclear physics",
        Property("temporal_extent", TemporalExtent.closed("2022-10", "2025-10")),
    )
    synthetic = labelled(
        "context:synthetic-data-work",
        CONTEXT,
        "Synthetic-data generation work",
    )
    jax_geopro = labelled(
        "context:jax-geopro",
        CONTEXT,
        "jax-geopro project",
        Property(
            "temporal_extent",
            TemporalExtent.ongoing("2026-04", as_of="2026-09"),
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
        assertion(
            "relation:synthetic-part-of-phd",
            "part_of",
            synthetic.id,
            phd.id,
        ),
        assertion(
            "relation:matteo-performs-alice",
            "performs",
            person.id,
            alice_activity.id,
        ),
        assertion(
            "relation:matteo-performs-synthetic",
            "performs",
            person.id,
            synthetic_activity.id,
        ),
        assertion(
            "relation:matteo-performs-jax",
            "performs",
            person.id,
            jax_activity.id,
        ),
        assertion(
            "relation:alice-activity-occurs-in",
            "occurs_in",
            alice_activity.id,
            alice.id,
        ),
        assertion(
            "relation:synthetic-activity-occurs-in",
            "occurs_in",
            synthetic_activity.id,
            synthetic.id,
        ),
        assertion(
            "relation:jax-activity-occurs-in",
            "occurs_in",
            jax_activity.id,
            jax_geopro.id,
        ),
        assertion(
            "relation:alice-uses-python",
            "uses_technology",
            alice_activity.id,
            python.id,
        ),
        assertion(
            "relation:synthetic-uses-python",
            "uses_technology",
            synthetic_activity.id,
            python.id,
        ),
        assertion(
            "relation:jax-uses-python",
            "uses_technology",
            jax_activity.id,
            python.id,
        ),
    )
    return v5_candidate(
        (
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
        relations,
        candidate_id="realisation:temporal-v5",
        scope="ALICE, PhD synthetic-data, and jax-geopro Python activities",
    )
