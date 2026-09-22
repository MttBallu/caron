"""Two ontology 5.0 career contexts connected by practical use of Python.

ALICE data analysis during an MSc and later synthetic-data work during a PhD
both use the same Python entity. Context is supplied by activities and their
``occurs_in`` relations; no primitive transfer or decontextualized
person-skill relation is asserted.
"""

from caron import (
    ACTIVITY,
    ARTIFACT,
    CONTEXT,
    ORGANIZATION,
    PERSON,
    SUBJECT,
    TECHNOLOGY,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    RelationAssertion,
    TemporalExtent,
)
from caron.ontology import career_ontology_v5_0
from examples.semantic_spine import labelled


def build_candidate() -> RealisationCandidate:
    """Build two evidence-rich activities joined by one Python entity."""

    ontology = career_ontology_v5_0()
    person = labelled("person:matteo", PERSON, "Mattéo")

    alice_context = Entity(
        id="context:msc-alice-analysis",
        kind=CONTEXT,
        properties=(
            Property("label", "MSc — ALICE data-analysis project"),
            Property(
                "temporal_extent",
                TemporalExtent.closed("2021-11", "2022-02"),
            ),
        ),
    )
    synthetic_data_context = Entity(
        id="context:phd-synthetic-data",
        kind=CONTEXT,
        properties=(
            Property("label", "PhD — synthetic-data work"),
            Property(
                "temporal_extent",
                TemporalExtent.closed("2022-10", "2025-10"),
            ),
        ),
    )

    analyse_alice_data = labelled(
        "activity:analyse-alice-data",
        ACTIVITY,
        "Analyse ALICE collision data",
    )
    build_training_dataset = labelled(
        "activity:build-training-dataset",
        ACTIVITY,
        "Build a labelled synthetic training dataset",
    )

    python = labelled("technology:python", TECHNOLOGY, "Python")
    root = labelled("technology:root", TECHNOLOGY, "ROOT")
    polars = labelled("technology:polars", TECHNOLOGY, "Polars")
    hdf5 = labelled("technology:hdf5", TECHNOLOGY, "HDF5")
    particle_physics = labelled(
        "subject:particle-physics",
        SUBJECT,
        "Particle physics",
    )
    gamma_spectroscopy = labelled(
        "subject:gamma-spectroscopy",
        SUBJECT,
        "Gamma spectroscopy",
    )

    alice_collaboration = labelled(
        "organization:alice-collaboration",
        ORGANIZATION,
        "ALICE Collaboration",
    )
    alice_dataset = labelled(
        "artifact:alice-collision-dataset",
        ARTIFACT,
        "ALICE collision dataset",
    )
    alice_notebook = labelled(
        "artifact:alice-analysis-notebook",
        ARTIFACT,
        "ALICE analysis notebook",
    )
    synthetic_codebase = labelled(
        "artifact:synthetic-data-codebase",
        ARTIFACT,
        "Synthetic-data generation codebase",
    )
    synthetic_pool = labelled(
        "artifact:synthetic-data-pool",
        ARTIFACT,
        "Synthetic spectrum pool",
    )
    generation_metadata = labelled(
        "artifact:generation-metadata",
        ARTIFACT,
        "Generation metadata",
    )
    training_dataset = labelled(
        "artifact:training-dataset",
        ARTIFACT,
        "Labelled synthetic training dataset",
    )

    relations = (
        RelationAssertion(
            "relation:participates-in-alice-project",
            "participates_in",
            EntityRef(person.id),
            EntityRef(alice_context.id),
            (
                Qualifier("role", "MSc student researcher"),
                Qualifier("organization", EntityRef(alice_collaboration.id)),
            ),
        ),
        RelationAssertion(
            "relation:participates-in-synthetic-data-work",
            "participates_in",
            EntityRef(person.id),
            EntityRef(synthetic_data_context.id),
            (Qualifier("role", "doctoral researcher"),),
        ),
        RelationAssertion(
            "relation:performs-alice-analysis",
            "performs",
            EntityRef(person.id),
            EntityRef(analyse_alice_data.id),
        ),
        RelationAssertion(
            "relation:performs-dataset-build",
            "performs",
            EntityRef(person.id),
            EntityRef(build_training_dataset.id),
        ),
        RelationAssertion(
            "relation:alice-analysis-occurs-in-project",
            "occurs_in",
            EntityRef(analyse_alice_data.id),
            EntityRef(alice_context.id),
        ),
        RelationAssertion(
            "relation:dataset-build-occurs-in-synthetic-work",
            "occurs_in",
            EntityRef(build_training_dataset.id),
            EntityRef(synthetic_data_context.id),
        ),
        RelationAssertion(
            "relation:alice-project-associated-with-collaboration",
            "organization_association",
            EntityRef(alice_collaboration.id),
            EntityRef(alice_context.id),
            (Qualifier("role", "host collaboration"),),
        ),
        RelationAssertion(
            "relation:alice-analysis-uses-python",
            "uses_technology",
            EntityRef(analyse_alice_data.id),
            EntityRef(python.id),
        ),
        RelationAssertion(
            "relation:alice-analysis-uses-root",
            "uses_technology",
            EntityRef(analyse_alice_data.id),
            EntityRef(root.id),
        ),
        RelationAssertion(
            "relation:alice-analysis-draws-on-particle-physics",
            "draws_on",
            EntityRef(analyse_alice_data.id),
            EntityRef(particle_physics.id),
        ),
        RelationAssertion(
            "relation:alice-analysis-takes-collision-data",
            "takes_input",
            EntityRef(analyse_alice_data.id),
            EntityRef(alice_dataset.id),
        ),
        RelationAssertion(
            "relation:alice-analysis-produces-notebook",
            "produces",
            EntityRef(analyse_alice_data.id),
            EntityRef(alice_notebook.id),
        ),
        RelationAssertion(
            "relation:dataset-build-uses-python",
            "uses_technology",
            EntityRef(build_training_dataset.id),
            EntityRef(python.id),
        ),
        RelationAssertion(
            "relation:dataset-build-uses-polars",
            "uses_technology",
            EntityRef(build_training_dataset.id),
            EntityRef(polars.id),
        ),
        RelationAssertion(
            "relation:dataset-build-uses-hdf5",
            "uses_technology",
            EntityRef(build_training_dataset.id),
            EntityRef(hdf5.id),
        ),
        RelationAssertion(
            "relation:dataset-build-uses-codebase",
            "uses_artifact",
            EntityRef(build_training_dataset.id),
            EntityRef(synthetic_codebase.id),
        ),
        RelationAssertion(
            "relation:dataset-build-draws-on-spectroscopy",
            "draws_on",
            EntityRef(build_training_dataset.id),
            EntityRef(gamma_spectroscopy.id),
        ),
        RelationAssertion(
            "relation:dataset-build-takes-pool",
            "takes_input",
            EntityRef(build_training_dataset.id),
            EntityRef(synthetic_pool.id),
        ),
        RelationAssertion(
            "relation:dataset-build-takes-metadata",
            "takes_input",
            EntityRef(build_training_dataset.id),
            EntityRef(generation_metadata.id),
        ),
        RelationAssertion(
            "relation:dataset-build-produces-training-dataset",
            "produces",
            EntityRef(build_training_dataset.id),
            EntityRef(training_dataset.id),
        ),
    )

    return RealisationCandidate(
        id="realisation:python-across-contexts",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(
            person,
            alice_context,
            synthetic_data_context,
            analyse_alice_data,
            build_training_dataset,
            python,
            root,
            polars,
            hdf5,
            particle_physics,
            gamma_spectroscopy,
            alice_collaboration,
            alice_dataset,
            alice_notebook,
            synthetic_codebase,
            synthetic_pool,
            generation_metadata,
            training_dataset,
        ),
        relations=relations,
        coverage=Coverage(
            CoverageStatus.SELECTIVE,
            "Python use in an MSc ALICE analysis project and later PhD "
            "synthetic-data work",
        ),
    )
