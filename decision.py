from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .boundaries import first_boundary
from .financial_core import run_case
from .models import DelayAssumptions, ProjectCase, Scenario
from .scenario import DelayResult, run_delay_transmission

_CHANNELS = {
    "capex": "Investment Cost",
    "revenue": "Revenue",
    "opex": "Operating Cost",
    "interest_rate": "Financing Cost",
}
_THRESHOLD_LABELS = {
    "DSCR": "Minimum DSCR Threshold",
    "Equity IRR": "Required Equity Return",
    "Sponsor Support": "Sponsor / Liquidity Support Capacity",
}


@dataclass
class DecisionProfile:
    model_status: str
    primary_vulnerability: str
    first_financial_threshold_reached: str
    base_dscr: float
    base_equity_irr: float
    delay_adjusted_equity_irr: float
    scenario_sponsor_headroom: float
    scenario_funding_shortfall: float
    resilience_profile: pd.DataFrame
    schedule_profile: pd.DataFrame
    why_trace: pd.DataFrame


def _status(current: float, boundary: float, tol: float = 1e-9) -> str:
    if current > boundary + tol:
        return "BREACHED"
    if abs(current - boundary) <= tol:
        return "BOUNDARY"
    return "WITHIN"


def build_decision_profile(case: ProjectCase, scenario: Scenario, delay: DelayAssumptions) -> DecisionProfile:
    base = run_case(case)
    delay_result: DelayResult = run_delay_transmission(case, scenario.schedule_delay_pct, delay)
    effective_capex = scenario.capex_overrun_pct + delay_result.equivalent_capex_stress

    stresses = {
        "capex": effective_capex,
        "revenue": scenario.revenue_reduction_pct,
        "opex": scenario.operating_cost_increase_pct,
        "interest_rate": scenario.financing_cost_increase,
    }

    rows = []
    ranked = []
    statuses = []
    for driver, stress in stresses.items():
        boundary = first_boundary(case, driver)
        b = boundary.boundary_magnitude
        util = stress / b if b > 0 else float("inf")
        s = _status(stress, b)
        statuses.append(s)
        ranked.append((util, driver, boundary))
        rows.append(
            {
                "Financial Channel": _CHANNELS[driver],
                "Current Stress": stress,
                "Intervention Boundary": b,
                "Remaining Stress Capacity": b - stress,
                "Stress Capacity Used": util,
                "Status": s,
                "First Financial Threshold Reached": _THRESHOLD_LABELS[boundary.constraint_name],
            }
        )

    if "BREACHED" in statuses:
        model_status = "INTERVENTION THRESHOLD BREACHED"
    elif "BOUNDARY" in statuses:
        model_status = "AT INTERVENTION BOUNDARY"
    else:
        model_status = "WITHIN TESTED LIMITS"

    max_util, primary_driver, primary_boundary = max(ranked, key=lambda x: x[0])
    any_stress = any(v > 0 for v in stresses.values()) or scenario.schedule_delay_pct > 0
    primary_vulnerability = _CHANNELS[primary_driver] if any_stress else "No active scenario vulnerability"
    first_threshold = _THRESHOLD_LABELS[primary_boundary.constraint_name]

    investment_case = run_case(case, driver="capex", magnitude=effective_capex)

    resilience = pd.DataFrame(rows)
    schedule = pd.DataFrame(
        [
            ("Baseline Schedule", delay.baseline_schedule_months),
            ("Schedule Delay", scenario.schedule_delay_pct),
            ("Incremental Delay Months", delay_result.incremental_delay_months),
            ("Stressed Schedule Months", delay_result.stressed_schedule_months),
            ("Additional IDC", delay_result.additional_idc),
            ("Additional Construction Overhead", delay_result.additional_construction_overhead),
            ("Total Delay Cost", delay_result.total_delay_cost),
            ("Equivalent Investment Cost Stress", delay_result.equivalent_capex_stress),
            ("Delay-Adjusted Equity IRR", delay_result.delay_adjusted_equity_irr),
        ],
        columns=["Metric", "Value"],
    )

    why = pd.DataFrame(
        [
            (1, "Project Inputs", "Base project economics, capital structure and user-defined thresholds establish the starting capital state."),
            (2, "Scenario", "The selected adverse scenario is translated into standard financial stress channels."),
            (3, "Schedule Transmission", "Delay creates incremental IDC and any explicit construction overhead, which increase investment cost and shift equity cash-flow timing."),
            (4, "Capital Resilience", f"Primary scenario vulnerability: {primary_vulnerability}."),
            (5, "Intervention Boundary", f"Relevant financial threshold: {first_threshold}."),
            (6, "CFE Model State", f"Deterministic model state: {model_status}. Final investment judgement remains human."),
        ],
        columns=["Step", "Layer", "Why"],
    )

    return DecisionProfile(
        model_status=model_status,
        primary_vulnerability=primary_vulnerability,
        first_financial_threshold_reached=first_threshold,
        base_dscr=float(base.financial_state.minimum_dscr),
        base_equity_irr=float(base.financial_state.equity_irr),
        delay_adjusted_equity_irr=float(delay_result.delay_adjusted_equity_irr),
        scenario_sponsor_headroom=float(investment_case.funding_state.sponsor_headroom),
        scenario_funding_shortfall=float(investment_case.funding_state.funding_shortfall),
        resilience_profile=resilience,
        schedule_profile=schedule,
        why_trace=why,
    )
