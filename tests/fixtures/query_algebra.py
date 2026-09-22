"""Validated ontology 5.0 fixture for private query-algebra regressions."""

from caron import (
    Accepted,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    TemporalExtent,
    ValidatedRealisation,
    YearMonth,
    validate_candidate,
)
from caron.entities import PropertyValue
from caron.ontology import _career_ontology_v5_0_development
from tests.fixtures.v5 import assertion, v5_candidate


def _entity(
    entity_id: str,
    kind: str,
    label: str,
    **properties: PropertyValue,
) -> Entity:
    return Entity(
        entity_id,
        kind,
        (Property("label", label),)
        + tuple(Property(name, value) for name, value in properties.items()),
    )


def query_algebra_candidate() -> RealisationCandidate:
    entities = (
        _entity("matteo", "Person", "Matteo"),
        _entity(
            "msc",
            "Context",
            "MSc subatomic physics",
            temporal_extent=TemporalExtent.closed("2021-09", "2022-02"),
        ),
        _entity(
            "beta_telescope",
            "Context",
            "Beta-spectrometer development",
            temporal_extent=TemporalExtent.closed("2024-01", "2025-06"),
        ),
        _entity("geant4_refresh", "Context", "Informal GEANT4 refresh"),
        _entity(
            "gamma_ml",
            "Context",
            "Gamma-analysis machine learning",
            temporal_extent=TemporalExtent.closed("2023-01", "2024-12"),
        ),
        _entity(
            "jax_geopro",
            "Context",
            "jax-geopro",
            temporal_extent=TemporalExtent.ongoing("2026-04", as_of="2026-09"),
        ),
        _entity("geant4", "Technology", "GEANT4"),
        _entity("jax", "Technology", "JAX"),
        _entity("python", "Technology", "Python"),
        _entity("jax_codebase", "Artifact", "jax-geopro codebase"),
        _entity("university", "Organization", "Université Paris-Saclay"),
        _entity(
            "doctorate",
            "Credential",
            "Doctorate",
            awarded_in=YearMonth.parse("2025-10"),
        ),
        _entity(
            "implement_detector_simulation",
            "Activity",
            "Implement detector simulation",
        ),
        _entity(
            "design_measure_abstraction",
            "Activity",
            "Design discrete-measure abstraction",
        ),
        _entity(
            "implement_ot_losses",
            "Activity",
            "Implement optimal-transport losses",
        ),
        _entity("review_api_constraints", "Activity", "Review API constraints"),
        _entity("train_initial_unet", "Activity", "Train initial U-Net"),
        _entity("investigate_edge_cases", "Activity", "Investigate edge cases"),
        _entity("unrelated_cleanup", "Activity", "Unrelated later cleanup"),
        _entity(
            "training_instability",
            "Proposition",
            "Training instability",
            content="Initial U-Net training is unstable.",
            context=EntityRef("gamma_ml"),
        ),
        _entity(
            "edge_case_diagnosis",
            "Proposition",
            "Edge-case diagnosis",
            content="Edge and bin-boundary cases cause the instability.",
            context=EntityRef("gamma_ml"),
        ),
    )

    activities_and_contexts = {
        "implement_detector_simulation": "beta_telescope",
        "design_measure_abstraction": "jax_geopro",
        "implement_ot_losses": "jax_geopro",
        "review_api_constraints": "jax_geopro",
        "train_initial_unet": "gamma_ml",
        "investigate_edge_cases": "gamma_ml",
        "unrelated_cleanup": "gamma_ml",
    }
    structural_relations = tuple(
        relation
        for activity, context in activities_and_contexts.items()
        for relation in (
            assertion(
                f"performs:{activity}",
                "performs",
                "matteo",
                activity,
            ),
            assertion(
                f"occurs_in:{activity}",
                "occurs_in",
                activity,
                context,
            ),
        )
    )
    relations = (
        *structural_relations,
        assertion(
            "learns:geant4:msc",
            "learns",
            "matteo",
            "geant4",
            Qualifier("context", EntityRef("msc")),
        ),
        assertion(
            "learns:geant4:refresh",
            "learns",
            "matteo",
            "geant4",
            Qualifier("context", EntityRef("geant4_refresh")),
        ),
        assertion(
            "uses:geant4:detector",
            "uses_technology",
            "implement_detector_simulation",
            "geant4",
        ),
        assertion(
            "uses:jax:design",
            "uses_technology",
            "design_measure_abstraction",
            "jax",
        ),
        assertion(
            "uses:jax:ot",
            "uses_technology",
            "implement_ot_losses",
            "jax",
        ),
        assertion(
            "produces:codebase:design",
            "produces",
            "design_measure_abstraction",
            "jax_codebase",
        ),
        assertion(
            "produces:codebase:ot",
            "produces",
            "implement_ot_losses",
            "jax_codebase",
        ),
        assertion(
            "results_in:instability",
            "results_in",
            "train_initial_unet",
            "training_instability",
        ),
        assertion(
            "motivates:edge_investigation",
            "motivates",
            "training_instability",
            "investigate_edge_cases",
        ),
        assertion(
            "establishes:edge_diagnosis",
            "establishes",
            "investigate_edge_cases",
            "edge_case_diagnosis",
        ),
        assertion(
            "awarded_to:doctorate",
            "awarded_to",
            "doctorate",
            "matteo",
        ),
        assertion(
            "awarded_by:doctorate",
            "awarded_by",
            "doctorate",
            "university",
        ),
        assertion(
            "obtained_through:doctorate",
            "obtained_through",
            "doctorate",
            "gamma_ml",
        ),
    )
    return v5_candidate(
        entities,
        relations,
        candidate_id="query-algebra-fixture",
        scope="Query-algebra regression fixture; absence is not career absence.",
    )


def validated_query_algebra_fixture() -> ValidatedRealisation:
    result = validate_candidate(
        _career_ontology_v5_0_development(), query_algebra_candidate()
    )
    if not isinstance(result, Accepted):
        raise AssertionError(result.diagnostics)
    return result.realisation
