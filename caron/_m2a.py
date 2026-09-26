"""Private reference evaluator for the draft M2-A structural request.

The query selects asserted patterns and their identified supports. It neither
interprets the person's abilities nor adds inferred ontology assertions.
"""

from dataclasses import dataclass

from caron.entities import Entity, EntityRef
from caron.ontology import career_ontology_v5_0
from caron.realisations import Coverage, ValidatedRealisation
from caron.relations import RelationAssertion
from caron.views import GraphView, QueryBinding

_RESOURCE_KINDS: dict[str, frozenset[str]] = {
    "Technology": frozenset({"uses_technology"}),
    "Language": frozenset({"uses_language"}),
    "Method": frozenset({"applies", "draws_on"}),
    "Subject": frozenset({"draws_on"}),
}


@dataclass(frozen=True, slots=True)
class Request:
    person_id: str
    target_id: str


@dataclass(frozen=True, slots=True)
class RequestDiagnostic:
    code: str
    entity_id: str


@dataclass(frozen=True, slots=True)
class LearningMatch:
    person: EntityRef
    target: EntityRef
    context: EntityRef
    learns: str


@dataclass(frozen=True, slots=True)
class ActivityResourceMatch:
    person: EntityRef
    activity: EntityRef
    target: EntityRef
    local_context: EntityRef
    resource_kind: str
    performs: str
    occurs_in: str
    resource_relation: str


type Match = LearningMatch | ActivityResourceMatch


@dataclass(frozen=True, slots=True)
class MatchesAccepted:
    request: Request
    source_realisation_id: str
    ontology_id: str
    ontology_version: str
    coverage: Coverage
    matches: tuple[Match, ...]
    view: GraphView[Match]

    def __post_init__(self) -> None:
        if self.view.results != self.matches:
            raise ValueError("The view must mirror the authoritative matches")


@dataclass(frozen=True, slots=True)
class MatchesRejected:
    request: Request
    source_realisation_id: str
    ontology_id: str
    ontology_version: str
    diagnostics: tuple[RequestDiagnostic, ...]

    def __post_init__(self) -> None:
        if not self.diagnostics:
            raise ValueError("A rejected request requires a diagnostic")


type MatchOutcome = MatchesAccepted | MatchesRejected


def request_diagnostics(
    source: ValidatedRealisation, request: Request
) -> tuple[RequestDiagnostic, ...]:
    if source.ontology != career_ontology_v5_0():
        return (RequestDiagnostic("query.unsupported_ontology", source.ontology.id),)
    person = source.entity(request.person_id)
    target = source.entity(request.target_id)
    errors: list[RequestDiagnostic] = []
    if person is None:
        errors.append(RequestDiagnostic("query.unknown_person", request.person_id))
    elif person.kind != "Person":
        errors.append(RequestDiagnostic("query.invalid_person_kind", request.person_id))
    if target is None:
        errors.append(RequestDiagnostic("query.unknown_target", request.target_id))
    elif target.kind not in _RESOURCE_KINDS:
        errors.append(RequestDiagnostic("query.invalid_target_kind", request.target_id))
    return tuple(errors)


def _match_key(match: Match) -> tuple[str, ...]:
    if isinstance(match, LearningMatch):
        return ("0", match.context.entity_id, match.learns)
    return (
        "1",
        match.activity.entity_id,
        match.local_context.entity_id,
        match.resource_kind,
        match.performs,
        match.occurs_in,
        match.resource_relation,
    )


def build_view(
    source: ValidatedRealisation, request: Request, matches: tuple[Match, ...]
) -> GraphView[Match]:
    """Select precisely the supports and close their semantic entity references."""
    relations_by_id = {relation.id: relation for relation in source.relations}
    entities_by_id = {entity.id: entity for entity in source.entities}
    selected_relations: dict[str, RelationAssertion] = {}
    selected_entities: dict[str, Entity] = {}

    def select_entity(entity_id: str) -> None:
        selected_entities[entity_id] = entities_by_id[entity_id]

    for match in matches:
        support_ids = (
            (match.learns,)
            if isinstance(match, LearningMatch)
            else (match.performs, match.occurs_in, match.resource_relation)
        )
        for relation_id in support_ids:
            relation = relations_by_id[relation_id]
            selected_relations[relation_id] = relation
            select_entity(relation.source.entity_id)
            select_entity(relation.target.entity_id)
            for qualifier in relation.qualifiers:
                if isinstance(qualifier.value, EntityRef):
                    select_entity(qualifier.value.entity_id)

    pending = list(selected_entities.values())
    while pending:
        entity = pending.pop()
        for prop in entity.properties:
            if (
                isinstance(prop.value, EntityRef)
                and prop.value.entity_id not in selected_entities
            ):
                select_entity(prop.value.entity_id)
                pending.append(selected_entities[prop.value.entity_id])

    return GraphView(
        query_name="ReusableEntityMatches",
        source_realisation_id=source.id,
        ontology=source.ontology,
        entities=tuple(sorted(selected_entities.values(), key=lambda item: item.id)),
        relations=tuple(sorted(selected_relations.values(), key=lambda item: item.id)),
        bindings=(
            (
                QueryBinding("person", EntityRef(request.person_id)),
                QueryBinding("target", EntityRef(request.target_id)),
            )
            if matches
            else ()
        ),
        results=matches,
        coverage=source.coverage,
    )


def evaluate_matches(source: ValidatedRealisation, request: Request) -> MatchOutcome:
    """Evaluate the two fixed M2-A patterns over an accepted realisation."""
    identity = (request, source.id, source.ontology.id, source.ontology.version)
    diagnostics = request_diagnostics(source, request)
    if diagnostics:
        return MatchesRejected(*identity, diagnostics)

    target = source.entity(request.target_id)
    assert target is not None  # Checked above, together with its concept kind.
    kinds = _RESOURCE_KINDS[target.kind]
    matches: set[Match] = set()
    for relation in source.relations:
        if (
            relation.kind == "learns"
            and relation.source.entity_id == request.person_id
            and relation.target.entity_id == request.target_id
        ):
            context = relation.qualifier("context")
            assert isinstance(context, EntityRef)  # Required by exact ontology 5.0.
            matches.add(
                LearningMatch(
                    EntityRef(request.person_id),
                    EntityRef(request.target_id),
                    context,
                    relation.id,
                )
            )
        if relation.kind not in kinds or relation.target.entity_id != request.target_id:
            continue
        activity_id = relation.source.entity_id
        for performance in source.matching_relations(
            kind="performs", source_id=request.person_id, target_id=activity_id
        ):
            for location in source.matching_relations(
                kind="occurs_in", source_id=activity_id
            ):
                matches.add(
                    ActivityResourceMatch(
                        EntityRef(request.person_id),
                        EntityRef(activity_id),
                        EntityRef(request.target_id),
                        location.target,
                        relation.kind,
                        performance.id,
                        location.id,
                        relation.id,
                    )
                )
    selected = tuple(sorted(matches, key=_match_key))
    return MatchesAccepted(
        *identity, source.coverage, selected, build_view(source, request, selected)
    )
