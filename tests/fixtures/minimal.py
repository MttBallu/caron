"""Small valid realisations used as test starting points."""

from caron import (
    ACTIVITY,
    CONTEXT,
    PERSON,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    RealisationCandidate,
    RelationAssertion,
    model4_ontology,
)


def labelled(entity_id: str, kind: str, label: str | None = None) -> Entity:
    return Entity(
        id=entity_id,
        kind=kind,
        properties=(Property("label", label or entity_id),),
    )


def minimal_candidate() -> RealisationCandidate:
    ontology = model4_ontology()
    person = labelled("person:ada", PERSON, "Ada")
    context = labelled("context:lab", CONTEXT, "Research lab")
    activity = labelled("activity:build", ACTIVITY, "Build a prototype")
    return RealisationCandidate(
        id="realisation:minimal",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(person, context, activity),
        relations=(
            RelationAssertion(
                id="relation:performs",
                kind="performs",
                source=EntityRef(person.id),
                target=EntityRef(activity.id),
            ),
            RelationAssertion(
                id="relation:occurs-in",
                kind="occurs_in",
                source=EntityRef(activity.id),
                target=EntityRef(context.id),
            ),
        ),
        coverage=Coverage(CoverageStatus.SELECTIVE, "Minimal validation fixture"),
    )
