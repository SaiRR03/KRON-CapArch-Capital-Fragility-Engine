from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.optimize import brentq

from .financial_core import build_operating_schedule, run_case
from .models import DelayAssumptions, ProjectCase, Scenario


@dataclass(frozen=True)
class DelayResult:
    stressed_schedule_months: float
    incremental_delay_months: float
    additional_idc: float
    additional_construction_overhead: float
    total_delay_cost: float
    equivalent_capex_stress: float
    sponsor_headroom: float
    funding_shortfall: float
    base_equity_irr: float
    funding_only_equity_irr: float
    delay_adjusted_equity_irr: float


def _fractional_irr(times: Sequence[float], cashflows: Sequence[float]) -> float:
    def npv(rate: float) -> float:
        return sum(cf / (1.0 + rate) ** t for t, cf in zip(times, cashflows))

    grid = np.concatenate([np.linspace(-0.99, 1.0, 500), np.linspace(1.01, 10.0, 300)])
    left = float(grid[0])
    f_left = npv(left)
    for right in grid[1:]:
        right = float(right)
        f_right = npv(right)
        if np.isfinite(f_left) and np.isfinite(f_right) and f_left * f_right < 0:
            return float(brentq(npv, left, right, xtol=1e-12))
        left, f_left = right, f_right
    return np.nan


def run_delay_transmission(case: ProjectCase, schedule_delay_pct: float, assumptions: DelayAssumptions) -> DelayResult:
    if schedule_delay_pct < 0:
        raise ValueError("schedule_delay_pct must be >= 0")
    if assumptions.baseline_schedule_months <= 0:
        raise ValueError("baseline_schedule_months must be > 0")
    if not 0 <= assumptions.debt_balance_exposure_share <= 1:
        raise ValueError("debt_balance_exposure_share must be between 0 and 1")

    base = run_case(case)
    stressed_schedule = assumptions.baseline_schedule_months * (1.0 + schedule_delay_pct)
    incremental_months = stressed_schedule - assumptions.baseline_schedule_months
    delay_years = incremental_months / 12.0

    exposed_debt = base.funding_state.total_debt * assumptions.debt_balance_exposure_share
    additional_idc = exposed_debt * case.financing.annual_interest_rate * delay_years
    additional_overhead = assumptions.annual_construction_overhead * delay_years
    total_delay_cost = additional_idc + additional_overhead
    equivalent_capex_stress = total_delay_cost / case.project.base_capex

    funding_only = run_case(case, driver="capex", magnitude=equivalent_capex_stress)
    schedule = build_operating_schedule(funding_only.stressed_project)
    ads = funding_only.financial_state.annual_debt_service

    times = [0.0]
    cashflows = [-funding_only.funding_state.total_equity_required]
    for year, (_, _, cfads) in enumerate(schedule, start=1):
        debt_service = ads if year <= case.financing.debt_tenor_years else 0.0
        times.append(float(year) + delay_years)
        cashflows.append(cfads - debt_service)

    return DelayResult(
        stressed_schedule_months=float(stressed_schedule),
        incremental_delay_months=float(incremental_months),
        additional_idc=float(additional_idc),
        additional_construction_overhead=float(additional_overhead),
        total_delay_cost=float(total_delay_cost),
        equivalent_capex_stress=float(equivalent_capex_stress),
        sponsor_headroom=float(funding_only.funding_state.sponsor_headroom),
        funding_shortfall=float(funding_only.funding_state.funding_shortfall),
        base_equity_irr=float(base.financial_state.equity_irr),
        funding_only_equity_irr=float(funding_only.financial_state.equity_irr),
        delay_adjusted_equity_irr=float(_fractional_irr(times, cashflows)),
    )
