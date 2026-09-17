"""A small career realisation with one technology shared across two contexts.

The example makes reuse explicit without inferring a transfer relation: two
activities occur in different contexts and both have a ``uses`` relation to
the same Python entity.
"""

from caron import (
    ACTIVITY,
    CONTEXT,
    PERSON,
    TECHNOLOGY,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    RelationAssertion,
    model4_ontology,
)
from examples.semantic_spine import labelled


def build_candidate() -> RealisationCandidate:
    """Build two contexts whose activities share the same Python entity."""

    ontology = model4_ontology()
    person = labelled("person:matteo", PERSON, "Mattéo")
    phd = Entity(
        id="context:phd",
        kind=CONTEXT,
        properties=(
            Property("label", "Nuclear-physics PhD"),
            Property("start", 2022),
            Property("end", 2025),
            Property("status", "completed"),
        ),
    )
    data_project = Entity(
        id="context:data-project",
        kind=CONTEXT,
        properties=(
            Property("label", "Environmental data project"),
            Property("start", 2025),
            Property("status", "completed"),
        ),
    )
    analyse_spectra = labelled(
        "activity:analyse-spectra",
        ACTIVITY,
        "Analyse gamma spectra",
    )
    build_pipeline = labelled(
        "activity:build-data-pipeline",
        ACTIVITY,
        "Build an environmental data pipeline",
    )
    python = labelled("technology:python", TECHNOLOGY, "Python")

    return RealisationCandidate(
        id="realisation:two-contexts",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(
            person,
            phd,
            data_project,
            analyse_spectra,
            build_pipeline,
            python,
        ),
        relations=(
            RelationAssertion(
                "relation:participates-in-phd",
                "participates_in",
                EntityRef(person.id),
                EntityRef(phd.id),
                (Qualifier("role", "doctoral researcher"),),
            ),
            RelationAssertion(
                "relation:participates-in-data-project",
                "participates_in",
                EntityRef(person.id),
                EntityRef(data_project.id),
                (Qualifier("role", "data engineer"),),
            ),
            RelationAssertion(
                "relation:performs-spectrum-analysis",
                "performs",
                EntityRef(person.id),
                EntityRef(analyse_spectra.id),
            ),
            RelationAssertion(
                "relation:performs-pipeline-build",
                "performs",
                EntityRef(person.id),
                EntityRef(build_pipeline.id),
            ),
            RelationAssertion(
                "relation:spectrum-analysis-occurs-in-phd",
                "occurs_in",
                EntityRef(analyse_spectra.id),
                EntityRef(phd.id),
            ),
            RelationAssertion(
                "relation:pipeline-build-occurs-in-data-project",
                "occurs_in",
                EntityRef(build_pipeline.id),
                EntityRef(data_project.id),
            ),
            RelationAssertion(
                "relation:spectrum-analysis-uses-python",
                "uses",
                EntityRef(analyse_spectra.id),
                EntityRef(python.id),
            ),
            RelationAssertion(
                "relation:pipeline-build-uses-python",
                "uses",
                EntityRef(build_pipeline.id),
                EntityRef(python.id),
            ),
        ),
        coverage=Coverage(
            CoverageStatus.SELECTIVE,
            "Two activities in distinct contexts sharing one technology",
        ),
    )
