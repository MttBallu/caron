"""Executable tour of the semantic spine currently implemented by ``caron``.

Run from the project root with::

    uv run python examples/semantic_spine.py

At this stage, the package can:

1. expose and inspect an explicit ontology schema;
2. represent career entities and relation assertions as immutable records;
3. keep invalid input representable as a ``RealisationCandidate``;
4. validate a candidate and return structured diagnostics;
5. produce an immutable ``ValidatedRealisation`` after successful validation;
6. support direct reads over that validated value.

This Model 4 example stops at direct validated reads. The separate temporal
example exercises the v0.5 query and ``GraphView`` boundary. Serialization and
narrative answer construction remain outside both examples.
"""

from dataclasses import replace

from caron import (
    ACTIVITY,
    ARTIFACT,
    CONTEXT,
    METHOD,
    PERSON,
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
    ValidatedRealisation,
    model4_ontology,
    validate_candidate,
)


def labelled(entity_id: str, kind: str, label: str) -> Entity:
    """Create an entity having only the common required label property."""

    return Entity(entity_id, kind, (Property("label", label),))


def build_candidate() -> RealisationCandidate:
    """Build a small but semantically varied career-model candidate."""

    ontology = model4_ontology()

    person = labelled("person:matteo", PERSON, "Mattéo")
    context = Entity(
        id="context:phd",
        kind=CONTEXT,
        properties=(
            Property("label", "Nuclear-physics PhD"),
            Property("start", 2022),
            Property("status", "completed"),
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
    discrepancy = Entity(
        id="proposition:rb90-discrepancy",
        kind=PROPOSITION,
        properties=(
            Property("label", "Rb-90 cascade discrepancy"),
            Property(
                "content",
                "The measured cascade intensity differs from evaluated data.",
            ),
            Property("context", EntityRef(context.id)),
        ),
    )

    relations = (
        RelationAssertion(
            "relation:participation",
            "participates_in",
            EntityRef(person.id),
            EntityRef(context.id),
            (Qualifier("role", "doctoral researcher"),),
        ),
        RelationAssertion(
            "relation:performs",
            "performs",
            EntityRef(person.id),
            EntityRef(activity.id),
        ),
        RelationAssertion(
            "relation:occurs-in",
            "occurs_in",
            EntityRef(activity.id),
            EntityRef(context.id),
        ),
        RelationAssertion(
            "relation:uses-python",
            "uses",
            EntityRef(activity.id),
            EntityRef(python.id),
        ),
        RelationAssertion(
            "relation:applies-fitting",
            "applies",
            EntityRef(activity.id),
            EntityRef(peak_fitting.id),
        ),
        RelationAssertion(
            "relation:draws-on-spectroscopy",
            "draws_on",
            EntityRef(activity.id),
            EntityRef(spectroscopy.id),
        ),
        RelationAssertion(
            "relation:takes-spectrum",
            "takes_input",
            EntityRef(activity.id),
            EntityRef(spectrum.id),
        ),
        RelationAssertion(
            "relation:produces-report",
            "produces",
            EntityRef(activity.id),
            EntityRef(report.id),
        ),
        RelationAssertion(
            "relation:establishes-discrepancy",
            "establishes",
            EntityRef(activity.id),
            EntityRef(discrepancy.id),
        ),
        RelationAssertion(
            "relation:learns-fitting",
            "learns",
            EntityRef(person.id),
            EntityRef(peak_fitting.id),
            (Qualifier("context", EntityRef(context.id)),),
        ),
    )

    return RealisationCandidate(
        id="realisation:career-example",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(
            person,
            context,
            activity,
            python,
            peak_fitting,
            spectroscopy,
            spectrum,
            report,
            discrepancy,
        ),
        relations=relations,
        coverage=Coverage(
            CoverageStatus.SELECTIVE,
            "One PhD activity and the evidence directly attached to it",
        ),
    )


def validate_example(candidate: RealisationCandidate) -> ValidatedRealisation:
    """Cross the explicit candidate-to-validated boundary."""

    match validate_candidate(model4_ontology(), candidate):
        case Accepted(realisation):
            return realisation
        case Rejected(diagnostics):
            details = "\n".join(
                f"- {item.code}: {item.message}" for item in diagnostics
            )
            raise RuntimeError(f"The example should be valid:\n{details}")


def show_schema() -> None:
    """Demonstrate that model rules are data that can be inspected."""

    ontology = model4_ontology()
    learns = ontology.relation("learns")
    assert learns is not None

    print("ONTOLOGY")
    print(f"  identity: {ontology.id} version {ontology.version}")
    print(f"  concepts: {len(ontology.concepts)}")
    print(f"  relation kinds: {len(ontology.relations)}")
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
    match validate_candidate(model4_ontology(), invalid):
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

    print("THIS MODEL 4 EXAMPLE STOPS AT DIRECT VALIDATED READS")
    print("  temporal queries and GraphView: examples.temporal_queries")
    print("  serialization, storage, narrative answers, CLI: deferred")


if __name__ == "__main__":
    main()
