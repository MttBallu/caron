"""A career realisation showing development across two meaningful contexts.

The example follows the Model 4 examples directly: an optimal-transport
investigation during a PhD is followed by work on the ``jax-geopro`` open-source
project. Shared reusable entities connect the contexts; no primitive transfer
relation is asserted.
"""

from caron import (
    ACTIVITY,
    ARTIFACT,
    CONTEXT,
    METHOD,
    PERSON,
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
    model4_ontology,
)
from examples.semantic_spine import labelled


def build_candidate() -> RealisationCandidate:
    """Build two evidence-rich contexts joined by reusable career entities."""

    ontology = model4_ontology()
    person = labelled("person:matteo", PERSON, "Mattéo")

    phd_ot = Entity(
        id="context:phd-optimal-transport",
        kind=CONTEXT,
        properties=(
            Property("label", "PhD — optimal-transport investigation"),
            Property("start", 2024),
            Property("end", 2025),
            Property("status", "completed"),
        ),
    )
    jax_geopro = Entity(
        id="context:jax-geopro",
        kind=CONTEXT,
        properties=(
            Property("label", "jax-geopro open-source project"),
            Property("start", 2026),
            Property("status", "ongoing"),
        ),
    )

    evaluate_ot = labelled(
        "activity:evaluate-ot-formulation",
        ACTIVITY,
        "Evaluate optimal-transport formulations",
    )
    design_measures = labelled(
        "activity:design-discrete-measure-abstraction",
        ACTIVITY,
        "Design a discrete-measure abstraction",
    )
    implement_losses = labelled(
        "activity:implement-ot-losses",
        ACTIVITY,
        "Implement differentiable optimal-transport losses",
    )

    python = labelled("technology:python", TECHNOLOGY, "Python")
    pytorch = labelled("technology:pytorch", TECHNOLOGY, "PyTorch")
    jax = labelled("technology:jax", TECHNOLOGY, "JAX")
    optimal_transport = labelled(
        "method:optimal-transport",
        METHOD,
        "Optimal transport",
    )
    discrete_measures = labelled(
        "subject:discrete-measures",
        SUBJECT,
        "Discrete measures",
    )
    software_design = labelled(
        "subject:software-design",
        SUBJECT,
        "Software design",
    )
    evaluation_notebook = labelled(
        "artifact:ot-evaluation-notebook",
        ARTIFACT,
        "Optimal-transport evaluation notebook",
    )
    codebase = labelled(
        "artifact:jax-geopro-codebase",
        ARTIFACT,
        "jax-geopro codebase",
    )

    phd_question = Entity(
        id="proposition:phd-ot-question",
        kind=PROPOSITION,
        properties=(
            Property("label", "Evaluate OT for dense regression"),
            Property(
                "content",
                "Determine whether optimal-transport formulations are useful "
                "for dense spectrum regression.",
            ),
            Property("context", EntityRef(phd_ot.id)),
        ),
    )
    jax_geopro_goal = Entity(
        id="proposition:jax-geopro-goal",
        kind=PROPOSITION,
        properties=(
            Property("label", "Reusable differentiable loss library"),
            Property(
                "content",
                "A reusable JAX implementation of differentiable losses for "
                "discrete measures is available.",
            ),
            Property("context", EntityRef(jax_geopro.id)),
        ),
    )

    relations = (
        RelationAssertion(
            "relation:participates-in-phd-ot",
            "participates_in",
            EntityRef(person.id),
            EntityRef(phd_ot.id),
            (Qualifier("role", "doctoral researcher"),),
        ),
        RelationAssertion(
            "relation:participates-in-jax-geopro",
            "participates_in",
            EntityRef(person.id),
            EntityRef(jax_geopro.id),
            (Qualifier("role", "open-source maintainer"),),
        ),
        RelationAssertion(
            "relation:performs-evaluate-ot",
            "performs",
            EntityRef(person.id),
            EntityRef(evaluate_ot.id),
        ),
        RelationAssertion(
            "relation:performs-design-measures",
            "performs",
            EntityRef(person.id),
            EntityRef(design_measures.id),
        ),
        RelationAssertion(
            "relation:performs-implement-losses",
            "performs",
            EntityRef(person.id),
            EntityRef(implement_losses.id),
        ),
        RelationAssertion(
            "relation:evaluate-ot-occurs-in-phd",
            "occurs_in",
            EntityRef(evaluate_ot.id),
            EntityRef(phd_ot.id),
        ),
        RelationAssertion(
            "relation:design-measures-occurs-in-jax-geopro",
            "occurs_in",
            EntityRef(design_measures.id),
            EntityRef(jax_geopro.id),
        ),
        RelationAssertion(
            "relation:implement-losses-occurs-in-jax-geopro",
            "occurs_in",
            EntityRef(implement_losses.id),
            EntityRef(jax_geopro.id),
        ),
        RelationAssertion(
            "relation:phd-aims-at-ot-question",
            "aims_at",
            EntityRef(phd_ot.id),
            EntityRef(phd_question.id),
        ),
        RelationAssertion(
            "relation:jax-geopro-aims-at-library",
            "aims_at",
            EntityRef(jax_geopro.id),
            EntityRef(jax_geopro_goal.id),
        ),
        RelationAssertion(
            "relation:evaluate-ot-uses-python",
            "uses",
            EntityRef(evaluate_ot.id),
            EntityRef(python.id),
        ),
        RelationAssertion(
            "relation:evaluate-ot-uses-pytorch",
            "uses",
            EntityRef(evaluate_ot.id),
            EntityRef(pytorch.id),
        ),
        RelationAssertion(
            "relation:design-measures-uses-python",
            "uses",
            EntityRef(design_measures.id),
            EntityRef(python.id),
        ),
        RelationAssertion(
            "relation:design-measures-uses-jax",
            "uses",
            EntityRef(design_measures.id),
            EntityRef(jax.id),
        ),
        RelationAssertion(
            "relation:implement-losses-uses-jax",
            "uses",
            EntityRef(implement_losses.id),
            EntityRef(jax.id),
        ),
        RelationAssertion(
            "relation:evaluate-ot-applies-optimal-transport",
            "applies",
            EntityRef(evaluate_ot.id),
            EntityRef(optimal_transport.id),
        ),
        RelationAssertion(
            "relation:implement-losses-applies-optimal-transport",
            "applies",
            EntityRef(implement_losses.id),
            EntityRef(optimal_transport.id),
        ),
        RelationAssertion(
            "relation:evaluate-ot-draws-on-discrete-measures",
            "draws_on",
            EntityRef(evaluate_ot.id),
            EntityRef(discrete_measures.id),
        ),
        RelationAssertion(
            "relation:design-measures-draws-on-discrete-measures",
            "draws_on",
            EntityRef(design_measures.id),
            EntityRef(discrete_measures.id),
        ),
        RelationAssertion(
            "relation:design-measures-draws-on-software-design",
            "draws_on",
            EntityRef(design_measures.id),
            EntityRef(software_design.id),
        ),
        RelationAssertion(
            "relation:implement-losses-draws-on-discrete-measures",
            "draws_on",
            EntityRef(implement_losses.id),
            EntityRef(discrete_measures.id),
        ),
        RelationAssertion(
            "relation:evaluate-ot-produces-notebook",
            "produces",
            EntityRef(evaluate_ot.id),
            EntityRef(evaluation_notebook.id),
        ),
        RelationAssertion(
            "relation:design-measures-produces-codebase",
            "produces",
            EntityRef(design_measures.id),
            EntityRef(codebase.id),
        ),
        RelationAssertion(
            "relation:implement-losses-produces-codebase",
            "produces",
            EntityRef(implement_losses.id),
            EntityRef(codebase.id),
        ),
        RelationAssertion(
            "relation:implement-losses-supports-library-goal",
            "supports",
            EntityRef(implement_losses.id),
            EntityRef(jax_geopro_goal.id),
        ),
        RelationAssertion(
            "relation:learns-ot-in-phd",
            "learns",
            EntityRef(person.id),
            EntityRef(optimal_transport.id),
            (Qualifier("context", EntityRef(phd_ot.id)),),
        ),
        RelationAssertion(
            "relation:deepens-ot-in-jax-geopro",
            "learns",
            EntityRef(person.id),
            EntityRef(optimal_transport.id),
            (Qualifier("context", EntityRef(jax_geopro.id)),),
        ),
    )

    return RealisationCandidate(
        id="realisation:cross-context-development",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(
            person,
            phd_ot,
            jax_geopro,
            evaluate_ot,
            design_measures,
            implement_losses,
            python,
            pytorch,
            jax,
            optimal_transport,
            discrete_measures,
            software_design,
            evaluation_notebook,
            codebase,
            phd_question,
            jax_geopro_goal,
        ),
        relations=relations,
        coverage=Coverage(
            CoverageStatus.SELECTIVE,
            "Optimal-transport development from a PhD investigation to the "
            "jax-geopro open-source project",
        ),
    )
