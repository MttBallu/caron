"""Executable tour of the ontology 5.0 semantic spine.

Run from the project root with::

    uv run python -m examples.semantic_spine

The example is a selective career graph, not a complete career record. It
demonstrates every ontology 5.0 concept kind, typed properties, identified
relation assertions, the candidate-to-validated boundary, and direct reads.
The example targets the accepted exact ``5.0`` identity. Renderer JSON,
persistence, and narrative answer construction remain separate concerns.
"""

from dataclasses import replace

from caron import (
    ACTIVITY,
    ARTIFACT,
    COLLECTIVE,
    CONTEXT,
    CREDENTIAL,
    LANGUAGE,
    METHOD,
    ORGANIZATION,
    PERSON,
    PLACE,
    PROPOSITION,
    SUBJECT,
    TECHNOLOGY,
    Accepted,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    Rejected,
    RelationAssertion,
    TemporalExtent,
    ValidatedRealisation,
    YearMonth,
    validate_candidate,
)
from caron.ontology import career_ontology_v5_0


def labelled(
    entity_id: str,
    kind: str,
    label: str,
    *properties: Property,
) -> Entity:
    """Create a labelled entity with optional additional typed properties."""

    return Entity(entity_id, kind, (Property("label", label), *properties))


def assertion(
    relation_id: str,
    kind: str,
    source_id: str,
    target_id: str,
    *qualifiers: Qualifier,
) -> RelationAssertion:
    """Create one identified positive relation fact."""

    return RelationAssertion(
        relation_id,
        kind,
        EntityRef(source_id),
        EntityRef(target_id),
        qualifiers,
    )


def _proposition(
    entity_id: str,
    label: str,
    content: str,
    context_id: str,
) -> Entity:
    return labelled(
        entity_id,
        PROPOSITION,
        label,
        Property("content", content),
        Property("context", EntityRef(context_id)),
    )


def build_candidate() -> RealisationCandidate:
    """Build a representative ontology 5.0 career candidate."""

    ontology = career_ontology_v5_0()

    person = labelled("person:matteo", PERSON, "Mattéo")
    collective = labelled(
        "collective:gamma-analysis-team",
        COLLECTIVE,
        "Gamma-analysis team",
    )
    context = labelled(
        "context:phd",
        CONTEXT,
        "Nuclear-physics PhD",
        Property(
            "temporal_extent",
            TemporalExtent.closed("2022-10", "2025-10"),
        ),
    )
    activity = labelled(
        "activity:analyse-gamma-cascades",
        ACTIVITY,
        "Analyse delayed gamma cascades",
    )
    python = labelled("technology:python", TECHNOLOGY, "Python")
    peak_fitting = labelled("method:peak-fitting", METHOD, "Peak fitting")
    spectroscopy = labelled(
        "subject:gamma-spectroscopy",
        SUBJECT,
        "Gamma spectroscopy",
    )
    english = labelled("language:english", LANGUAGE, "English")
    spectrum = labelled(
        "artifact:coincidence-spectrum",
        ARTIFACT,
        "Gamma-gamma coincidence spectrum",
    )
    report = labelled(
        "artifact:discrepancy-report",
        ARTIFACT,
        "Rb-90 discrepancy report",
    )
    diploma = labelled(
        "artifact:doctoral-diploma",
        ARTIFACT,
        "Doctoral diploma",
    )
    discrepancy = _proposition(
        "proposition:rb90-discrepancy",
        "Rb-90 cascade discrepancy",
        "The measured cascade intensity differs from evaluated data.",
        context.id,
    )
    cea = labelled("organization:cea", ORGANIZATION, "CEA")
    university = labelled(
        "organization:paris-saclay",
        ORGANIZATION,
        "Université Paris-Saclay",
    )
    saclay = labelled("place:saclay", PLACE, "Saclay")
    doctorate = labelled(
        "credential:doctorate",
        CREDENTIAL,
        "Doctorate in nuclear physics",
        Property("awarded_in", YearMonth.parse("2025-10")),
    )

    relations = (
        assertion(
            "relation:participation",
            "participates_in",
            person.id,
            context.id,
            Qualifier("role", "doctoral researcher"),
            Qualifier("organization", EntityRef(cea.id)),
        ),
        assertion(
            "relation:collective-membership",
            "collective_membership",
            person.id,
            collective.id,
            Qualifier("context", EntityRef(context.id)),
            Qualifier("role", "member"),
        ),
        assertion(
            "relation:organization-association",
            "organization_association",
            cea.id,
            context.id,
            Qualifier("role", "host organization"),
        ),
        assertion("relation:occurs-at", "occurs_at", context.id, saclay.id),
        assertion("relation:performs:person", "performs", person.id, activity.id),
        assertion(
            "relation:performs:collective",
            "performs",
            collective.id,
            activity.id,
        ),
        assertion("relation:occurs-in", "occurs_in", activity.id, context.id),
        assertion(
            "relation:uses-python",
            "uses_technology",
            activity.id,
            python.id,
        ),
        assertion(
            "relation:uses-spectrum",
            "uses_artifact",
            activity.id,
            spectrum.id,
        ),
        assertion(
            "relation:uses-english",
            "uses_language",
            activity.id,
            english.id,
        ),
        assertion(
            "relation:applies-fitting",
            "applies",
            activity.id,
            peak_fitting.id,
        ),
        assertion(
            "relation:draws-on-spectroscopy",
            "draws_on",
            activity.id,
            spectroscopy.id,
        ),
        assertion(
            "relation:takes-spectrum",
            "takes_input",
            activity.id,
            spectrum.id,
        ),
        assertion(
            "relation:produces-report",
            "produces",
            activity.id,
            report.id,
        ),
        assertion(
            "relation:establishes-discrepancy",
            "establishes",
            activity.id,
            discrepancy.id,
        ),
        assertion(
            "relation:learns-fitting",
            "learns",
            person.id,
            peak_fitting.id,
            Qualifier("context", EntityRef(context.id)),
        ),
        assertion(
            "relation:exposed-to-english",
            "exposed_to",
            person.id,
            english.id,
            Qualifier("context", EntityRef(context.id)),
        ),
        assertion(
            "relation:awarded-to",
            "awarded_to",
            doctorate.id,
            person.id,
        ),
        assertion(
            "relation:awarded-by",
            "awarded_by",
            doctorate.id,
            university.id,
        ),
        assertion(
            "relation:obtained-through",
            "obtained_through",
            doctorate.id,
            context.id,
        ),
        assertion(
            "relation:evidenced-by",
            "evidenced_by",
            doctorate.id,
            diploma.id,
        ),
    )

    return RealisationCandidate(
        id="realisation:career-example",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(
            person,
            collective,
            context,
            activity,
            python,
            peak_fitting,
            spectroscopy,
            english,
            spectrum,
            report,
            diploma,
            discrepancy,
            cea,
            university,
            saclay,
            doctorate,
        ),
        relations=relations,
        coverage=Coverage(
            CoverageStatus.SELECTIVE,
            "One PhD activity, its resources and evidence, and its doctorate award",
        ),
    )


def validate_example(candidate: RealisationCandidate) -> ValidatedRealisation:
    """Cross the explicit candidate-to-validated boundary."""

    match validate_candidate(career_ontology_v5_0(), candidate):
        case Accepted(realisation):
            return realisation
        case Rejected(diagnostics):
            details = "\n".join(
                f"- {item.code}: {item.message}" for item in diagnostics
            )
            raise RuntimeError(f"The example should be valid:\n{details}")


def show_schema() -> None:
    """Demonstrate that model rules are data that can be inspected."""

    ontology = career_ontology_v5_0()
    learns = ontology.relation("learns")
    assert learns is not None

    print("ONTOLOGY")
    print(f"  identity: {ontology.id} version {ontology.version}")
    print(f"  concepts: {len(ontology.concepts)}")
    print(f"  relation kinds: {len(ontology.relations)}")
    print(f"  global invariants: {len(ontology.invariants)}")
    print(f"  learns targets: {', '.join(sorted(learns.target_kinds))}")
    print()


def show_direct_reads(realisation: ValidatedRealisation) -> None:
    """Use the small read API without pretending it is a query engine."""

    activity = realisation.entities_of_kind(ACTIVITY)[0]
    outgoing = realisation.matching_relations(source_id=activity.id)

    print("VALIDATED REALISATION")
    print(f"  coverage: {realisation.coverage.status.value}")
    print(f"  scope: {realisation.coverage.scope}")
    print(f"  selected activity: {activity.property('label')}")
    print("  directly attached information:")
    for relation in outgoing:
        target = realisation.entity(relation.target.entity_id)
        assert target is not None
        print(f"    {relation.kind} -> {target.property('label')}")
    print()


def show_rejection(candidate: RealisationCandidate) -> None:
    """Remove contextual grounding and inspect the resulting diagnostic."""

    invalid = replace(
        candidate,
        id="realisation:invalid-example",
        relations=tuple(
            relation for relation in candidate.relations if relation.kind != "occurs_in"
        ),
    )

    print("INVALID CANDIDATE")
    match validate_candidate(career_ontology_v5_0(), invalid):
        case Accepted(_):
            raise AssertionError("An ungrounded activity must not be accepted")
        case Rejected(diagnostics):
            for diagnostic in diagnostics:
                print(
                    f"  [{diagnostic.layer.value}] {diagnostic.code}: "
                    f"{diagnostic.message}"
                )
    print()


def main() -> None:
    candidate = build_candidate()
    show_schema()
    show_direct_reads(validate_example(candidate))
    show_rejection(candidate)

    print("ONTOLOGY 5.0 EXAMPLE")
    print("  temporal queries and GraphView: examples.temporal_queries")
    print("  persistence, narrative answers, CLI: deferred")


if __name__ == "__main__":
    main()
