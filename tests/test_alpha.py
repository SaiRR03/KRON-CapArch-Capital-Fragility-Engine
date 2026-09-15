import math

import numpy as np

from examples.synthetic_case import build_synthetic_case, combined_breach_scenario, default_delay_assumptions
from kron_cfe import (
    Scenario,
    build_decision_profile,
    evaluate_constraints,
    first_boundary,
    run_case,
    run_delay_transmission,
)


def test_base_financial_core_reproduces_frozen_case():
    case = build_synthetic_case()
    result = run_case(case)
    assert np.isclose(result.financial_state.annual_debt_service, 7.207393476871886, atol=1e-9)
    assert np.isclose(result.financial_state.minimum_dscr, 1.942450079823, atol=1e-9)
    assert np.isclose(result.financial_state.equity_irr, 0.229760805686, atol=1e-9)


def test_fixed_debt_10pct_capex_hits_sponsor_boundary():
    case = build_synthetic_case()
    result = run_case(case, "capex", 0.10)
    state = evaluate_constraints(result)
    assert np.isclose(result.funding_state.required_sponsor_support, 10.0)
    assert np.isclose(result.funding_state.sponsor_headroom, 0.0, atol=1e-9)
    assert state["Sponsor Support"].status == "BOUNDARY"


def test_fixed_debt_20pct_capex_creates_10m_shortfall():
    case = build_synthetic_case()
    result = run_case(case, "capex", 0.20)
    assert np.isclose(result.funding_state.required_sponsor_support, 20.0)
    assert np.isclose(result.funding_state.sponsor_headroom, -10.0)
    assert np.isclose(result.funding_state.funding_shortfall, 10.0)


def test_frozen_action2_boundaries():
    case = build_synthetic_case()
    assert np.isclose(first_boundary(case, "capex").boundary_magnitude, 0.10, atol=1e-9)
    assert np.isclose(first_boundary(case, "revenue").boundary_magnitude, 0.233050752572, atol=1e-8)
    assert np.isclose(first_boundary(case, "opex").boundary_magnitude, 0.776835841907, atol=1e-8)
    assert np.isclose(first_boundary(case, "interest_rate").boundary_magnitude, 0.084720629726, atol=1e-8)


def test_delay_transmission_reproduces_controlled_result():
    case = build_synthetic_case()
    delay = run_delay_transmission(case, 0.20, default_delay_assumptions())
    assert np.isclose(delay.stressed_schedule_months, 28.8)
    assert np.isclose(delay.incremental_delay_months, 4.8)
    assert np.isclose(delay.additional_idc, 1.68, atol=1e-9)
    assert np.isclose(delay.equivalent_capex_stress, 0.0168, atol=1e-9)
    assert delay.delay_adjusted_equity_irr < delay.base_equity_irr


def test_base_boundary_breach_states():
    case = build_synthetic_case()
    delay = default_delay_assumptions()

    base = build_decision_profile(case, Scenario(name="Base Case"), delay)
    assert base.model_status == "WITHIN TESTED LIMITS"
    assert base.primary_vulnerability == "No active scenario vulnerability"

    boundary = build_decision_profile(case, Scenario(name="Boundary", capex_overrun_pct=0.10), delay)
    assert boundary.model_status == "AT INTERVENTION BOUNDARY"
    assert np.isclose(boundary.scenario_funding_shortfall, 0.0, atol=1e-9)

    breach = build_decision_profile(case, combined_breach_scenario(), delay)
    assert breach.model_status == "INTERVENTION THRESHOLD BREACHED"
    investment = breach.resilience_profile.loc[
        breach.resilience_profile["Financial Channel"] == "Investment Cost"
    ].iloc[0]
    assert np.isclose(investment["Current Stress"], 0.1168, atol=1e-9)
    assert np.isclose(investment["Stress Capacity Used"], 1.168, atol=1e-9)
    assert np.isclose(breach.scenario_funding_shortfall, 1.68, atol=1e-9)


def test_funding_architecture_constant_leverage():
    case = build_synthetic_case()
    case = case.__class__(
        project=case.project,
        financing=case.financing.__class__(
            funding_rule="constant_leverage",
            debt_share=0.80,
            committed_debt=None,
            annual_interest_rate=0.06,
            debt_tenor_years=15,
            sponsor_support_capacity=10.0,
            contingency_facility=0.0,
        ),
        constraints=case.constraints,
        case_name="Constant Leverage Test",
    )
    result = run_case(case, "capex", 0.20)
    assert np.isclose(result.funding_state.total_debt, 96.0)
    assert np.isclose(result.funding_state.total_equity_required, 24.0)


def test_funding_architecture_facility_then_sponsor():
    case = build_synthetic_case()
    case = case.__class__(
        project=case.project,
        financing=case.financing.__class__(
            funding_rule="facility_then_sponsor",
            debt_share=0.70,
            committed_debt=70.0,
            annual_interest_rate=0.06,
            debt_tenor_years=15,
            sponsor_support_capacity=10.0,
            contingency_facility=10.0,
        ),
        constraints=case.constraints,
        case_name="Facility Test",
    )
    result = run_case(case, "capex", 0.20)
    assert np.isclose(result.funding_state.contingency_draw, 10.0)
    assert np.isclose(result.funding_state.required_sponsor_support, 10.0)
    assert np.isclose(result.funding_state.funding_shortfall, 0.0)
