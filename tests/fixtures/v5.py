"""Reusable candidates and builders for ontology 5.0 conformance tests."""

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
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    RelationAssertion,
    TemporalExtent,
    YearMonth,
)

V5_ONTOLOGY_ID = "caron.career-model"
V5_DEVELOPMENT_VERSION = "5.0-dev"


def labelled(
    entity_id: str,
    kind: str,
    label: str | None = None,
    *properties: Property,
) -> Entity:
    """Build a labelled entity with optional additional typed properties."""

    return Entity(
        entity_id,
        kind,
        (Property("label", label or entity_id), *properties),
    )


def proposition(
    entity_id: str,
    context_id: str,
    content: str,
    *,
    label: str | None = None,
) -> Entity:
    """Build a Proposition whose required locality is explicit."""

    return labelled(
        entity_id,
        PROPOSITION,
        label,
        Property("content", content),
        Property("context", EntityRef(context_id)),
    )


def assertion(
    relation_id: str,
    kind: str,
    source_id: str,
    target_id: str,
    *qualifiers: Qualifier,
) -> RelationAssertion:
    """Build one identified positive relation fact."""

    return RelationAssertion(
        relation_id,
        kind,
        EntityRef(source_id),
        EntityRef(target_id),
        qualifiers,
    )


def v5_candidate(
    entities: tuple[Entity, ...],
    relations: tuple[RelationAssertion, ...] = (),
    *,
    candidate_id: str = "realisation:v5-focused",
    scope: str = "Focused ontology 5.0 conformance fixture",
) -> RealisationCandidate:
    """Build an immutable candidate targeting the private development schema."""

    return RealisationCandidate(
        candidate_id,
        V5_ONTOLOGY_ID,
        V5_DEVELOPMENT_VERSION,
        entities,
        relations,
        Coverage(CoverageStatus.SELECTIVE, scope),
    )


def minimal_v5_candidate() -> RealisationCandidate:
    """Return the smallest useful valid candidate containing an Activity."""

    entities = (
        labelled("person:minimal", PERSON, "Minimal person"),
        labelled("context:minimal", CONTEXT, "Minimal context"),
        labelled("activity:minimal", ACTIVITY, "Minimal activity"),
    )
    relations = (
        assertion(
            "relation:minimal-performs",
            "performs",
            "person:minimal",
            "activity:minimal",
        ),
        assertion(
            "relation:minimal-occurs",
            "occurs_in",
            "activity:minimal",
            "context:minimal",
        ),
    )
    return v5_candidate(
        entities,
        relations,
        candidate_id="realisation:v5-minimal",
        scope="One person performing one activity in one context",
    )


def activity_candidate(
    performer_kinds: tuple[str, ...] = (PERSON,),
) -> RealisationCandidate:
    """Build a valid Activity with the requested personal/collective performers."""

    context = labelled("context:activity", CONTEXT)
    activity = labelled("activity:focused", ACTIVITY)
    performers = tuple(
        labelled(f"performer:{index}", kind)
        for index, kind in enumerate(performer_kinds, start=1)
    )
    relations = (
        *(
            assertion(
                f"relation:performs:{index}",
                "performs",
                performer.id,
                activity.id,
            )
            for index, performer in enumerate(performers, start=1)
        ),
        assertion("relation:occurs", "occurs_in", activity.id, context.id),
    )
    return v5_candidate((*performers, context, activity), relations)


def credential_candidate(
    *,
    awarder_count: int = 1,
    awarded_in: YearMonth | None = None,
) -> RealisationCandidate:
    """Build a valid particular award with one or more awarding organizations."""

    properties = () if awarded_in is None else (Property("awarded_in", awarded_in),)
    credential = labelled("credential:focused", CREDENTIAL, None, *properties)
    person = labelled("person:recipient", PERSON)
    context = labelled("context:programme", CONTEXT)
    awarders = tuple(
        labelled(f"organization:awarder:{index}", ORGANIZATION)
        for index in range(1, awarder_count + 1)
    )
    relations = (
        assertion(
            "relation:awarded-to",
            "awarded_to",
            credential.id,
            person.id,
        ),
        *(
            assertion(
                f"relation:awarded-by:{index}",
                "awarded_by",
                credential.id,
                awarder.id,
            )
            for index, awarder in enumerate(awarders, start=1)
        ),
        assertion(
            "relation:obtained-through",
            "obtained_through",
            credential.id,
            context.id,
        ),
    )
    return v5_candidate((credential, person, context, *awarders), relations)


def rich_v5_candidate() -> RealisationCandidate:
    """Return a valid candidate covering all concepts and relation kinds."""

    career = labelled(
        "context:career",
        CONTEXT,
        "Doctoral career period",
        Property("temporal_extent", TemporalExtent.closed("2022-10", "2025-10")),
    )
    project = labelled(
        "context:project",
        CONTEXT,
        "Delayed-gamma project",
        Property("temporal_extent", TemporalExtent.closed("2023-01", "2024-12")),
    )
    person = labelled("person:ada", PERSON, "Ada")
    reviewer = labelled("person:reviewer", PERSON, "External reviewer")
    collective = labelled("collective:team", COLLECTIVE, "Analysis team")
    activity = labelled("activity:analysis", ACTIVITY, "Analyse gamma cascades")
    technology = labelled("technology:python", TECHNOLOGY, "Python")
    method = labelled("method:peak-fit", METHOD, "Two-dimensional peak fitting")
    subject = labelled("subject:spectroscopy", SUBJECT, "Gamma spectroscopy")
    language = labelled("language:english", LANGUAGE, "English")
    spectrum = labelled("artifact:spectrum", ARTIFACT, "Coincidence spectrum")
    report = labelled("artifact:report", ARTIFACT, "Discrepancy report")
    diploma = labelled("artifact:diploma", ARTIFACT, "Doctoral diploma")
    cea = labelled("organization:cea", ORGANIZATION, "CEA")
    laboratory = labelled("organization:laboratory", ORGANIZATION, "DPhN")
    university = labelled(
        "organization:university", ORGANIZATION, "Université Paris-Saclay"
    )
    place = labelled("place:saclay", PLACE, "Saclay")
    credential = labelled(
        "credential:doctorate",
        CREDENTIAL,
        "Doctorate",
        Property("awarded_in", YearMonth.parse("2025-10")),
    )
    aim = proposition(
        "proposition:aim",
        project.id,
        "Explain the observed cascade discrepancy.",
        label="Project aim",
    )
    motivation = proposition(
        "proposition:motivation",
        career.id,
        "Reliable decay data matters for nuclear applications.",
        label="Scientific motivation",
    )
    result = proposition(
        "proposition:result",
        project.id,
        "The measured ratio differs from the evaluated value.",
        label="Measured discrepancy",
    )
    established = proposition(
        "proposition:established",
        project.id,
        "The discrepancy persists under the validation protocol.",
        label="Validated discrepancy",
    )
    supported = proposition(
        "proposition:supported",
        project.id,
        "The ground-state feeding may be overestimated.",
        label="Supported hypothesis",
    )
    contradicted = proposition(
        "proposition:contradicted",
        project.id,
        "The evaluated cascade intensity fully explains the data.",
        label="Contradicted account",
    )

    entities = (
        person,
        reviewer,
        collective,
        career,
        project,
        activity,
        technology,
        method,
        subject,
        language,
        spectrum,
        report,
        diploma,
        aim,
        motivation,
        result,
        established,
        supported,
        contradicted,
        cea,
        laboratory,
        university,
        place,
        credential,
    )
    relations = (
        assertion("relation:part-of", "part_of", project.id, career.id),
        assertion(
            "relation:suborganization",
            "suborganization_of",
            laboratory.id,
            cea.id,
        ),
        assertion("relation:performs:person", "performs", person.id, activity.id),
        assertion(
            "relation:performs:collective", "performs", collective.id, activity.id
        ),
        assertion("relation:occurs", "occurs_in", activity.id, project.id),
        assertion(
            "relation:participates:organization",
            "participates_in",
            person.id,
            project.id,
            Qualifier("role", "Doctoral researcher"),
            Qualifier("organization", EntityRef(laboratory.id)),
        ),
        assertion(
            "relation:participates:plain",
            "participates_in",
            reviewer.id,
            project.id,
            Qualifier("role", "Reviewer"),
        ),
        assertion(
            "relation:membership",
            "collective_membership",
            person.id,
            collective.id,
            Qualifier("context", EntityRef(project.id)),
            Qualifier("role", "Member"),
        ),
        assertion(
            "relation:organization-association",
            "organization_association",
            laboratory.id,
            project.id,
            Qualifier("role", "Host laboratory"),
        ),
        assertion("relation:occurs-at", "occurs_at", project.id, place.id),
        assertion(
            "relation:exposed:technology",
            "exposed_to",
            person.id,
            technology.id,
            Qualifier("context", EntityRef(project.id)),
        ),
        assertion(
            "relation:exposed:language",
            "exposed_to",
            person.id,
            language.id,
            Qualifier("context", EntityRef(project.id)),
        ),
        assertion(
            "relation:learns:method",
            "learns",
            person.id,
            method.id,
            Qualifier("context", EntityRef(project.id)),
        ),
        assertion(
            "relation:learns:language",
            "learns",
            person.id,
            language.id,
            Qualifier("context", EntityRef(project.id)),
        ),
        assertion(
            "relation:uses-technology",
            "uses_technology",
            activity.id,
            technology.id,
        ),
        assertion(
            "relation:uses-artifact",
            "uses_artifact",
            activity.id,
            spectrum.id,
        ),
        assertion(
            "relation:uses-language",
            "uses_language",
            activity.id,
            language.id,
        ),
        assertion("relation:applies", "applies", activity.id, method.id),
        assertion("relation:draws-on:method", "draws_on", activity.id, method.id),
        assertion("relation:draws-on:subject", "draws_on", activity.id, subject.id),
        assertion(
            "relation:native-language",
            "native_language",
            reviewer.id,
            language.id,
        ),
        assertion("relation:takes-input", "takes_input", activity.id, spectrum.id),
        assertion("relation:produces", "produces", activity.id, report.id),
        assertion("relation:modifies", "modifies", activity.id, spectrum.id),
        assertion("relation:awarded-to", "awarded_to", credential.id, person.id),
        assertion("relation:awarded-by:cea", "awarded_by", credential.id, cea.id),
        assertion(
            "relation:awarded-by:university",
            "awarded_by",
            credential.id,
            university.id,
        ),
        assertion(
            "relation:obtained-through",
            "obtained_through",
            credential.id,
            career.id,
        ),
        assertion("relation:evidenced-by", "evidenced_by", credential.id, diploma.id),
        assertion("relation:aims-at", "aims_at", project.id, aim.id),
        assertion("relation:addresses", "addresses", activity.id, aim.id),
        assertion("relation:motivates", "motivates", motivation.id, activity.id),
        assertion("relation:results-in", "results_in", activity.id, result.id),
        assertion("relation:establishes", "establishes", activity.id, established.id),
        assertion("relation:supports", "supports", activity.id, supported.id),
        assertion("relation:contradicts", "contradicts", activity.id, contradicted.id),
        assertion("relation:bears-on", "bears_on", result.id, aim.id),
    )
    return v5_candidate(
        entities,
        relations,
        candidate_id="realisation:v5-rich",
        scope="Representative graph covering the complete ontology 5.0 vocabulary",
    )
