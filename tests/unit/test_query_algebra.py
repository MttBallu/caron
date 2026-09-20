from caron import EntityRef
from caron._query_algebra import (
    BindingTable,
    EntityConstant,
    EntityValue,
    Extend,
    Join,
    LeftJoin,
    LookupProperty,
    OrderBy,
    PathSet,
    Project,
    QualifierPattern,
    RelationPattern,
    Union,
    Variable,
    binding_table,
    evaluate_plan,
    graph_view_from_relation,
    path_set,
)
from tests.fixtures.query_algebra import validated_query_algebra_fixture


def _activities_in_context_plan() -> OrderBy:
    activity = Variable("activity")
    resource = Variable("resource")
    role = Variable("role")
    activities = Join(
        (
            RelationPattern(
                frozenset({"performs"}),
                EntityConstant("matteo"),
                activity,
            ),
            RelationPattern(
                frozenset({"occurs_in"}),
                activity,
                EntityConstant("jax_geopro"),
            ),
        )
    )
    resources = RelationPattern(
        frozenset({"uses", "produces"}),
        activity,
        resource,
        kind_variable=role,
    )
    return OrderBy(
        Project(
            LeftJoin(activities, resources, (role, resource)),
            (activity, role, resource),
        ),
        (activity, role, resource),
    )


def _reusable_entity_history_plan(target_id: str = "geant4") -> OrderBy:
    activity = Variable("activity")
    context = Variable("context")
    context_start = Variable("context_start")
    event_kind = Variable("event_kind")
    learning = Extend(
        RelationPattern(
            frozenset({"learns"}),
            EntityConstant("matteo"),
            EntityConstant(target_id),
            kind_variable=event_kind,
            qualifiers=(QualifierPattern("context", context),),
        ),
        ((activity, None),),
    )
    practical = Join(
        (
            RelationPattern(
                frozenset({"performs"}),
                EntityConstant("matteo"),
                activity,
            ),
            RelationPattern(
                frozenset({"uses", "applies", "draws_on"}),
                activity,
                EntityConstant(target_id),
                kind_variable=event_kind,
            ),
            RelationPattern(frozenset({"occurs_in"}), activity, context),
        )
    )
    events = Union((learning, practical))
    return OrderBy(
        Project(
            LookupProperty(
                events,
                context,
                "start",
                context_start,
                allow_missing=True,
            ),
            (event_kind, context, activity, context_start),
        ),
        (context_start,),
    )


def _problem_solving_plan() -> Project:
    first_activity = Variable("first_activity")
    first_proposition = Variable("first_proposition")
    second_activity = Variable("second_activity")
    second_proposition = Variable("second_proposition")
    first_outcome = Variable("first_outcome")
    motivation = Variable("motivation")
    second_outcome = Variable("second_outcome")
    return Project(
        Join(
            (
                RelationPattern(
                    frozenset({"performs"}),
                    EntityConstant("matteo"),
                    first_activity,
                ),
                RelationPattern(
                    frozenset({"occurs_in"}),
                    first_activity,
                    EntityConstant("gamma_ml"),
                ),
                RelationPattern(
                    frozenset({"results_in", "establishes"}),
                    first_activity,
                    first_proposition,
                    relation_variable=first_outcome,
                ),
                RelationPattern(
                    frozenset({"motivates"}),
                    first_proposition,
                    second_activity,
                    relation_variable=motivation,
                ),
                RelationPattern(
                    frozenset({"performs"}),
                    EntityConstant("matteo"),
                    second_activity,
                ),
                RelationPattern(
                    frozenset({"occurs_in"}),
                    second_activity,
                    EntityConstant("gamma_ml"),
                ),
                RelationPattern(
                    frozenset({"results_in", "establishes"}),
                    second_activity,
                    second_proposition,
                    relation_variable=second_outcome,
                ),
            )
        ),
        (
            first_activity,
            first_proposition,
            second_activity,
            second_proposition,
            first_outcome,
            motivation,
            second_outcome,
        ),
    )


def test_natural_join_combines_bindings_and_witnesses() -> None:
    activity = Variable("activity")
    context = Variable("context")
    plan = Project(
        Join(
            (
                RelationPattern(
                    frozenset({"performs"}),
                    EntityConstant("matteo"),
                    activity,
                ),
                RelationPattern(frozenset({"occurs_in"}), activity, context),
            )
        ),
        (activity, context),
    )
    relation = evaluate_plan(validated_query_algebra_fixture(), plan)
    detector_row = next(
        row
        for row in relation.rows
        if row.value(activity) == EntityValue("implement_detector_simulation")
    )

    assert detector_row.value(context) == EntityValue("beta_telescope")
    assert frozenset(detector_row.witness.relations) == frozenset(
        {
            "performs:implement_detector_simulation",
            "occurs_in:implement_detector_simulation",
        }
    )


def test_left_join_returns_normalized_rows_and_a_witness_derived_view() -> None:
    realisation = validated_query_algebra_fixture()
    variables = (
        Variable("activity"),
        Variable("role"),
        Variable("resource"),
    )
    relation = evaluate_plan(realisation, _activities_in_context_plan())
    answer = binding_table(relation, variables=variables, ordered_by=variables)
    view = graph_view_from_relation(
        realisation,
        query_name="activities_in_context",
        relation=relation,
    )

    assert isinstance(answer, BindingTable)
    assert tuple(row.values for row in answer.rows) == (
        ("design_measure_abstraction", "produces", "jax_codebase"),
        ("design_measure_abstraction", "uses", "jax"),
        ("implement_ot_losses", "produces", "jax_codebase"),
        ("implement_ot_losses", "uses", "jax"),
        ("review_api_constraints", None, None),
    )
    assert {entity.id for entity in view.entities} == {
        "design_measure_abstraction",
        "implement_ot_losses",
        "jax",
        "jax_codebase",
        "jax_geopro",
        "matteo",
        "review_api_constraints",
    }


def test_union_and_property_lookup_preserve_unknown_dates_and_witnesses() -> None:
    realisation = validated_query_algebra_fixture()
    variables = (
        Variable("event_kind"),
        Variable("context"),
        Variable("activity"),
        Variable("context_start"),
    )
    relation = evaluate_plan(realisation, _reusable_entity_history_plan())
    answer = binding_table(
        relation,
        variables=variables,
        ordered_by=(Variable("context_start"),),
    )
    view = graph_view_from_relation(
        realisation,
        query_name="reusable_entity_history",
        relation=relation,
    )

    assert tuple(row.values for row in answer.rows) == (
        ("learns", "msc", None, 2021),
        ("uses", "beta_telescope", "implement_detector_simulation", 2024),
        ("learns", "geant4_refresh", None, None),
    )
    assert all(row.witness.relations for row in relation.rows)
    assert relation.rows[0].witness.properties == ((EntityRef("msc"), "start"),)
    assert relation.rows[2].witness.properties == ()
    assert "learns:geant4:msc" in {item.id for item in view.relations}
    assert {"msc", "beta_telescope", "geant4"} <= {item.id for item in view.entities}


def test_explicit_problem_path_excludes_contextual_chronology() -> None:
    realisation = validated_query_algebra_fixture()
    relation = evaluate_plan(realisation, _problem_solving_plan())
    answer = path_set(
        relation,
        node_variables=(
            Variable("first_activity"),
            Variable("first_proposition"),
            Variable("second_activity"),
            Variable("second_proposition"),
        ),
        relation_variables=(
            Variable("first_outcome"),
            Variable("motivation"),
            Variable("second_outcome"),
        ),
    )
    view = graph_view_from_relation(
        realisation,
        query_name="problem_solving_trajectories",
        relation=relation,
    )

    assert isinstance(answer, PathSet)
    assert answer.paths[0].node_ids == (
        "train_initial_unet",
        "training_instability",
        "investigate_edge_cases",
        "edge_case_diagnosis",
    )
    assert "unrelated_cleanup" not in {entity.id for entity in view.entities}
    assert "gamma_ml" in {entity.id for entity in view.entities}


def test_projection_retains_witnesses_for_graph_view_construction() -> None:
    realisation = validated_query_algebra_fixture()
    relation = evaluate_plan(realisation, _reusable_entity_history_plan())
    view = graph_view_from_relation(
        realisation,
        query_name="reusable_entity_history",
        relation=relation,
    )
    view_relation_ids = {item.id for item in view.relations}

    assert all(set(row.witness.relations) <= view_relation_ids for row in relation.rows)


def test_empty_result_preserves_selective_coverage() -> None:
    realisation = validated_query_algebra_fixture()
    relation = evaluate_plan(
        realisation,
        _reusable_entity_history_plan(target_id="python"),
    )
    view = graph_view_from_relation(
        realisation,
        query_name="empty_reusable_entity_history",
        relation=relation,
    )

    assert relation.rows == ()
    assert view.entities == ()
    assert view.relations == ()
    assert view.coverage == realisation.coverage
