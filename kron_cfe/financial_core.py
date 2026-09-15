from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Sequence

import numpy as np
from scipy.optimize import brentq

from .models import (
    CaseResult,
    FinancialState,
    FinancingInputs,
    ProjectCase,
    ProjectInputs,
    StressDriver,
)
from .funding import allocate_funding


def validate_case(case: ProjectCase) -> None:
    p, f, c = case.project, case.financing, case.constraints
    if p.base_capex <= 0:
        raise ValueError("base_capex must be > 0")
    if p.annual_revenue < 0 or p.annual_opex < 0:
        raise ValueError("revenue and opex must be >= 0")
    if p.operating_years <= 0:
        raise ValueError("operating_years must be > 0")
    if not 0 <= f.debt_share <= 1:
        raise ValueError("debt_share must be between 0 and 1")
    if f.committed_debt is not None and f.committed_debt < 0:
        raise ValueError("committed_debt must be >= 0")
    if f.annual_interest_rate < 0:
        raise ValueError("annual_interest_rate must be >= 0")
    if f.debt_tenor_years <= 0:
        raise ValueError("debt_tenor_years must be > 0")
    if f.sponsor_support_capacity < 0 or f.contingency_facility < 0:
        raise ValueError("support capacities must be >= 0")
    if c.minimum_dscr <= 0 or c.equity_irr_hurdle < 0:
        raise ValueError("invalid constraint threshold")


def annual_debt_service(debt: float, rate: float, tenor_years: int) -> float:
    if debt <= 0:
        return 0.0
    if rate == 0:
        return debt / tenor_years
    return debt * rate / (1.0 - (1.0 + rate) ** (-tenor_years))


def calculate_irr(cashflows: Sequence[float]) -> float:
    """IRR using the first economically valid NPV root on a broad rate grid."""
    if len(cashflows) < 2 or not any(x < 0 for x in cashflows) or not any(x > 0 for x in cashflows):
        return np.nan

    def npv(rate: float) -> float:
        return sum(cf / (1.0 + rate) ** t for t, cf in enumerate(cashflows))

    grid = np.concatenate([np.linspace(-0.99, 1.0, 500), np.linspace(1.01, 10.0, 300)])
    left = float(grid[0])
    f_left = npv(left)
    for right in grid[1:]:
        right = float(right)
        f_right = npv(right)
        if np.isclose(f_right, 0.0, atol=1e-12):
            return right
        if np.isfinite(f_left) and np.isfinite(f_right) and f_left * f_right < 0:
            return float(brentq(npv, left, right, xtol=1e-12))
        left, f_left = right, f_right
    return np.nan


def build_operating_schedule(project: ProjectInputs) -> list[tuple[float, float, float]]:
    rows: list[tuple[float, float, float]] = []
    for year in range(1, project.operating_years + 1):
        revenue = project.annual_revenue * (1.0 + project.annual_revenue_growth) ** (year - 1)
        opex = project.annual_opex * (1.0 + project.annual_opex_growth) ** (year - 1)
        rows.append((revenue, opex, revenue - opex))
    return rows


def calculate_financial_state(
    project: ProjectInputs,
    financing: FinancingInputs,
    total_debt: float,
    total_equity_required: float,
) -> FinancialState:
    schedule = build_operating_schedule(project)
    ads = annual_debt_service(total_debt, financing.annual_interest_rate, financing.debt_tenor_years)

    dscr_values = []
    for idx, (_, _, cfads) in enumerate(schedule, start=1):
        if idx <= financing.debt_tenor_years and ads > 0:
            dscr_values.append(cfads / ads)
    minimum_dscr = min(dscr_values) if dscr_values else np.inf

    equity_cashflows = [-float(total_equity_required)]
    for idx, (_, _, cfads) in enumerate(schedule, start=1):
        debt_service = ads if idx <= financing.debt_tenor_years else 0.0
        equity_cashflows.append(cfads - debt_service)

    return FinancialState(
        cfads_year_1=float(schedule[0][2]),
        annual_debt_service=float(ads),
        minimum_dscr=float(minimum_dscr),
        equity_irr=float(calculate_irr(equity_cashflows)),
    )


def apply_stress(case: ProjectCase, driver: StressDriver, magnitude: float) -> tuple[ProjectInputs, FinancingInputs]:
    if magnitude < 0:
        raise ValueError("adverse stress magnitude must be >= 0")
    p, f = case.project, case.financing
    if driver == "none":
        return p, f
    if driver == "capex":
        return replace(p, base_capex=p.base_capex * (1.0 + magnitude)), f
    if driver == "revenue":
        return replace(p, annual_revenue=p.annual_revenue * (1.0 - magnitude)), f
    if driver == "opex":
        return replace(p, annual_opex=p.annual_opex * (1.0 + magnitude)), f
    if driver == "interest_rate":
        return p, replace(f, annual_interest_rate=f.annual_interest_rate + magnitude)
    raise ValueError(f"Unknown stress driver: {driver}")


def run_case(case: ProjectCase, driver: StressDriver = "none", magnitude: float = 0.0) -> CaseResult:
    validate_case(case)
    stressed_project, stressed_financing = apply_stress(case, driver, magnitude)
    funding = allocate_funding(
        base_capex=case.project.base_capex,
        stressed_capex=stressed_project.base_capex,
        financing=stressed_financing,
    )
    financial = calculate_financial_state(
        stressed_project,
        stressed_financing,
        total_debt=funding.total_debt,
        total_equity_required=funding.total_equity_required,
    )
    return CaseResult(
        case=case,
        stressed_project=stressed_project,
        stressed_financing=stressed_financing,
        funding_state=funding,
        financial_state=financial,
        driver=driver,
        magnitude=float(magnitude),
    )
