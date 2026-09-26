"""Frozen M2-A C01–C10 outcomes, independent of the Neo4j query implementation.

Transcribes the separate realisations and support-role expectations in the
2026-09-23 draft m2a-structural-matches-contract-experiment.md.
"""

from dataclasses import dataclass

from caron import (
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RelationAssertion,
    TemporalExtent,
)
from caron.adapters.neo4j_results import ActivityResourceMatch, LearningMatch, Match
from tests.fixtures.v5 import assertion, labelled


@dataclass(frozen=True)
class Case:
    id: str
    entities: tuple[Entity, ...]
    relations: tuple[RelationAssertion, ...]
    expected: tuple[Match, ...]
    view_entities: frozenset[str]
    view_relations: frozenset[str]


def _entities(**kinds: str) -> tuple[Entity, ...]:
    return tuple(labelled(entity_id, kind) for entity_id, kind in kinds.items())


def _learns(context: str = "c", relation_id: str = "l1") -> RelationAssertion:
    return assertion(
        relation_id, "learns", "p", "x", Qualifier("context", EntityRef(context))
    )


def _activity(
    activity: str = "a",
    context: str = "c",
    resource_kind: str = "uses_technology",
    suffix: str = "1",
) -> tuple[RelationAssertion, ...]:
    return (
        assertion(f"p{suffix}", "performs", "p", activity),
        assertion(f"o{suffix}", "occurs_in", activity, context),
        assertion(f"u{suffix}", resource_kind, activity, "x"),
    )


def _learning(context: str = "c", relation_id: str = "l1") -> LearningMatch:
    return LearningMatch(
        EntityRef("p"), EntityRef("x"), EntityRef(context), relation_id
    )


def _match(
    activity: str = "a",
    context: str = "c",
    resource_kind: str = "uses_technology",
    suffix: str = "1",
) -> ActivityResourceMatch:
    return ActivityResourceMatch(
        EntityRef("p"),
        EntityRef(activity),
        EntityRef("x"),
        EntityRef(context),
        resource_kind,
        f"p{suffix}",
        f"o{suffix}",
        f"u{suffix}",
    )


CASES = (
    Case(
        "C01_learning_without_activity",
        _entities(p="Person", x="Technology", c="Context"),
        (_learns(),),
        (_learning(),),
        frozenset({"p", "x", "c"}),
        frozenset({"l1"}),
    ),
    Case(
        "C02_activity_without_learning",
        _entities(p="Person", x="Technology", a="Activity", c="Context"),
        _activity(),
        (_match(),),
        frozenset({"p", "x", "a", "c"}),
        frozenset({"p1", "o1", "u1"}),
    ),
    Case(
        "C03_coexistence_without_sequence",
        _entities(p="Person", x="Technology", a="Activity", c="Context"),
        (_learns(), *_activity()),
        (_learning(), _match()),
        frozenset({"p", "x", "a", "c"}),
        frozenset({"l1", "p1", "o1", "u1"}),
    ),
    Case(
        "C04_method_has_two_distinct_roles",
        _entities(p="Person", x="Method", a="Activity", c="Context"),
        (
            assertion("p1", "performs", "p", "a"),
            assertion("o1", "occurs_in", "a", "c"),
            assertion("m1", "applies", "a", "x"),
            assertion("m2", "draws_on", "a", "x"),
        ),
        (
            ActivityResourceMatch(
                EntityRef("p"),
                EntityRef("a"),
                EntityRef("x"),
                EntityRef("c"),
                "applies",
                "p1",
                "o1",
                "m1",
            ),
            ActivityResourceMatch(
                EntityRef("p"),
                EntityRef("a"),
                EntityRef("x"),
                EntityRef("c"),
                "draws_on",
                "p1",
                "o1",
                "m2",
            ),
        ),
        frozenset({"p", "x", "a", "c"}),
        frozenset({"p1", "o1", "m1", "m2"}),
    ),
    Case(
        "C05_exposure_only",
        _entities(p="Person", x="Technology", c="Context"),
        (
            assertion(
                "e1", "exposed_to", "p", "x", Qualifier("context", EntityRef("c"))
            ),
        ),
        (),
        frozenset(),
        frozenset(),
    ),
    Case(
        "C06_shared_activity",
        _entities(
            p="Person", group="Collective", x="Technology", a="Activity", c="Context"
        ),
        (*_activity(), assertion("p2", "performs", "group", "a")),
        (_match(),),
        frozenset({"p", "x", "a", "c"}),
        frozenset({"p1", "o1", "u1"}),
    ),
    Case(
        "C06_collective_only_variant",
        _entities(
            p="Person", group="Collective", x="Technology", a="Activity", c="Context"
        ),
        (
            assertion("p2", "performs", "group", "a"),
            *_activity()[1:],
            assertion(
                "membership",
                "collective_membership",
                "p",
                "group",
                Qualifier("role", "member"),
                Qualifier("context", EntityRef("c")),
            ),
        ),
        (),
        frozenset(),
        frozenset(),
    ),
    Case(
        "C07_same_displayed_binding_two_supports",
        _entities(
            p="Person", x="Technology", a1="Activity", a2="Activity", c="Context"
        ),
        (*_activity("a1"), *_activity("a2", suffix="2")),
        (_match("a1"), _match("a2", suffix="2")),
        frozenset({"p", "x", "a1", "a2", "c"}),
        frozenset({"p1", "o1", "u1", "p2", "o2", "u2"}),
    ),
    Case(
        "C08_empty_selective_realisation",
        _entities(p="Person", x="Technology"),
        (),
        (),
        frozenset(),
        frozenset(),
    ),
    Case(
        "C09_nested_contexts_do_not_merge_local_facts",
        _entities(
            p="Person", x="Technology", a="Activity", child="Context", parent="Context"
        ),
        (
            _learns("parent"),
            *_activity(context="child"),
            assertion("h1", "part_of", "child", "parent"),
        ),
        (_learning("parent"), _match(context="child")),
        frozenset({"p", "x", "a", "child", "parent"}),
        frozenset({"l1", "p1", "o1", "u1"}),
    ),
    Case(
        "C10_overlapping_context_extents_do_not_order_facts",
        (
            labelled("p", "Person"),
            labelled("x", "Technology"),
            labelled("a", "Activity"),
            labelled(
                "learning_context",
                "Context",
                None,
                Property(
                    "temporal_extent", TemporalExtent.closed("2024-01", "2024-06")
                ),
            ),
            labelled(
                "activity_context",
                "Context",
                None,
                Property(
                    "temporal_extent", TemporalExtent.closed("2024-03", "2024-12")
                ),
            ),
        ),
        (_learns("learning_context"), *_activity(context="activity_context")),
        (_learning("learning_context"), _match(context="activity_context")),
        frozenset({"p", "x", "a", "learning_context", "activity_context"}),
        frozenset({"l1", "p1", "o1", "u1"}),
    ),
    *(
        Case(
            f"C01_learning_{kind}",
            _entities(p="Person", x=kind, c="Context"),
            (_learns(),),
            (_learning(),),
            frozenset({"p", "x", "c"}),
            frozenset({"l1"}),
        )
        for kind in ("Language", "Method", "Subject")
    ),
    *(
        Case(
            f"C02_activity_{kind}_{relation}",
            _entities(p="Person", x=kind, a="Activity", c="Context"),
            _activity(resource_kind=relation),
            (_match(resource_kind=relation),),
            frozenset({"p", "x", "a", "c"}),
            frozenset({"p1", "o1", "u1"}),
        )
        for kind, relation in (
            ("Language", "uses_language"),
            ("Method", "applies"),
            ("Method", "draws_on"),
            ("Subject", "draws_on"),
        )
    ),
)
