"""Validated Model 4 fixture for the ported query-algebra regressions."""

from caron import (
    Accepted,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    RelationAssertion,
    ValidatedRealisation,
    model4_ontology,
    validate_candidate,
)


def _entity(
    entity_id: str,
    kind: str,
    label: str,
    **properties: str | int | EntityRef,
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
        _entity("msc", "Context", "MSc subatomic physics", start=2021),
        _entity(
            "beta_telescope",
            "Context",
            "Beta-spectrometer development",
            start=2024,
        ),
        _entity("geant4_refresh", "Context", "Informal GEANT4 refresh"),
        _entity("gamma_ml", "Context", "Gamma-analysis machine learning", start=2023),
        _entity("jax_geopro", "Context", "jax-geopro", start=2026),
        _entity("geant4", "Technology", "GEANT4"),
        _entity("jax", "Technology", "JAX"),
        _entity("python", "Technology", "Python"),
        _entity("jax_codebase", "Artifact", "jax-geopro codebase"),
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
            RelationAssertion(
                f"performs:{activity}",
                "performs",
                EntityRef("matteo"),
                EntityRef(activity),
            ),
            RelationAssertion(
                f"occurs_in:{activity}",
                "occurs_in",
                EntityRef(activity),
                EntityRef(context),
            ),
        )
    )
    relations = (
        *structural_relations,
        RelationAssertion(
            "learns:geant4:msc",
            "learns",
            EntityRef("matteo"),
            EntityRef("geant4"),
            (Qualifier("context", EntityRef("msc")),),
        ),
        RelationAssertion(
            "learns:geant4:refresh",
            "learns",
            EntityRef("matteo"),
            EntityRef("geant4"),
            (Qualifier("context", EntityRef("geant4_refresh")),),
        ),
        RelationAssertion(
            "uses:geant4:detector",
            "uses",
            EntityRef("implement_detector_simulation"),
            EntityRef("geant4"),
        ),
        RelationAssertion(
            "uses:jax:design",
            "uses",
            EntityRef("design_measure_abstraction"),
            EntityRef("jax"),
        ),
        RelationAssertion(
            "uses:jax:ot",
            "uses",
            EntityRef("implement_ot_losses"),
            EntityRef("jax"),
        ),
        RelationAssertion(
            "produces:codebase:design",
            "produces",
            EntityRef("design_measure_abstraction"),
            EntityRef("jax_codebase"),
        ),
        RelationAssertion(
            "produces:codebase:ot",
            "produces",
            EntityRef("implement_ot_losses"),
            EntityRef("jax_codebase"),
        ),
        RelationAssertion(
            "results_in:instability",
            "results_in",
            EntityRef("train_initial_unet"),
            EntityRef("training_instability"),
        ),
        RelationAssertion(
            "motivates:edge_investigation",
            "motivates",
            EntityRef("training_instability"),
            EntityRef("investigate_edge_cases"),
        ),
        RelationAssertion(
            "establishes:edge_diagnosis",
            "establishes",
            EntityRef("investigate_edge_cases"),
            EntityRef("edge_case_diagnosis"),
        ),
    )
    return RealisationCandidate(
        id="query-algebra-fixture",
        ontology_id="caron.career-model",
        ontology_version="4",
        entities=entities,
        relations=relations,
        coverage=Coverage(
            CoverageStatus.SELECTIVE,
            "Query-algebra regression fixture; absence is not career absence.",
        ),
    )


def validated_query_algebra_fixture() -> ValidatedRealisation:
    result = validate_candidate(model4_ontology(), query_algebra_candidate())
    if not isinstance(result, Accepted):
        raise AssertionError(result.diagnostics)
    return result.realisation
