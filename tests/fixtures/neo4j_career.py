"""Whole-career M2-A probes with fixed source assertion expectations."""

from dataclasses import dataclass

from caron._m2a import (
    ActivityResourceMatch,
    LearningMatch,
    Match,
)
from caron.entities import EntityRef
from caron.realisations import ValidatedRealisation

PERSON = "person:matteo"


@dataclass(frozen=True)
class CareerProbe:
    target_id: str
    learning_ids: frozenset[str]
    resource_ids: frozenset[str]


PROBES = (
    CareerProbe(
        "technology:geant4",
        frozenset({"r:learns-geant4-msc"}),
        frozenset(
            {
                "r:fipps-simulation-uses-geant4",
                "r:beta-simulation-uses-geant4",
            }
        ),
    ),
    CareerProbe(
        "method:monte-carlo-transport",
        frozenset(),
        frozenset({"r:beta-simulation-applies-monte-carlo"}),
    ),
    CareerProbe(
        "language:english",
        frozenset(),
        frozenset({"r:presentation-uses-english"}),
    ),
    CareerProbe(
        "technology:python",
        frozenset(),
        frozenset(
            {
                "r:open-data-uses-python",
                "r:galaxy-fit-uses-python",
                "r:alice-uses-python",
                "r:gamma-analysis-uses-python",
                "r:synthetic-uses-python",
                "r:unet-uses-python",
                "r:comparison-uses-python",
                "r:jax-losses-uses-python",
            }
        ),
    ),
)


def source_matches(source: ValidatedRealisation, target_id: str) -> tuple[Match, ...]:
    """Independent source-record join; never reads the Neo4j projection."""
    target = source.entity(target_id)
    assert target is not None
    kinds = {
        "Technology": {"uses_technology"},
        "Language": {"uses_language"},
        "Method": {"applies", "draws_on"},
        "Subject": {"draws_on"},
    }[target.kind]
    matches: list[Match] = []
    for relation in source.relations:
        if (
            relation.kind == "learns"
            and relation.source.entity_id == PERSON
            and relation.target.entity_id == target_id
        ):
            context = relation.qualifier("context")
            assert isinstance(context, EntityRef)
            matches.append(
                LearningMatch(
                    EntityRef(PERSON), EntityRef(target_id), context, relation.id
                )
            )
        if relation.kind not in kinds or relation.target.entity_id != target_id:
            continue
        activity_id = relation.source.entity_id
        for performance in source.matching_relations(
            kind="performs", source_id=PERSON, target_id=activity_id
        ):
            for location in source.matching_relations(
                kind="occurs_in", source_id=activity_id
            ):
                matches.append(
                    ActivityResourceMatch(
                        EntityRef(PERSON),
                        EntityRef(activity_id),
                        EntityRef(target_id),
                        location.target,
                        relation.kind,
                        performance.id,
                        location.id,
                        relation.id,
                    )
                )
    return tuple(matches)


def source_view_ids(
    source: ValidatedRealisation, matches: tuple[Match, ...]
) -> tuple[frozenset[str], frozenset[str]]:
    """Expected minimal union of supporting records and reference closure."""
    relation_ids: set[str] = set()
    entity_ids: set[str] = set()
    for match in matches:
        if isinstance(match, LearningMatch):
            relation_ids.add(match.learns)
        else:
            relation_ids.update(
                (match.performs, match.occurs_in, match.resource_relation)
            )
    for relation_id in relation_ids:
        relation = source.relation(relation_id)
        assert relation is not None
        entity_ids.update((relation.source.entity_id, relation.target.entity_id))
        entity_ids.update(
            qualifier.value.entity_id
            for qualifier in relation.qualifiers
            if isinstance(qualifier.value, EntityRef)
        )
    pending = list(entity_ids)
    while pending:
        entity = source.entity(pending.pop())
        assert entity is not None
        for prop in entity.properties:
            if (
                isinstance(prop.value, EntityRef)
                and prop.value.entity_id not in entity_ids
            ):
                entity_ids.add(prop.value.entity_id)
                pending.append(prop.value.entity_id)
    return frozenset(entity_ids), frozenset(relation_ids)
