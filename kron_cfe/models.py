from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

FundingRule = Literal["fixed_debt", "constant_leverage", "facility_then_sponsor"]
StressDriver = Literal["none", "capex", "revenue", "opex", "interest_rate"]


@dataclass(frozen=True)
class ProjectInputs:
    base_capex: float
    annual_revenue: float
    annual_opex: float
    operating_years: int = 20
    annual_revenue_growth: float = 0.0
    annual_opex_growth: float = 0.0


@dataclass(frozen=True)
class FinancingInputs:
    funding_rule: FundingRule
    debt_share: float
    committed_debt: Optional[float]
    annual_interest_rate: float
    debt_tenor_years: int
    sponsor_support_capacity: float
    contingency_facility: float = 0.0


@dataclass(frozen=True)
class ConstraintInputs:
    minimum_dscr: float = 1.20
    equity_irr_hurdle: float = 0.08


@dataclass(frozen=True)
class ProjectCase:
    project: ProjectInputs
    financing: FinancingInputs
    constraints: ConstraintInputs
    case_name: str = "CFE Case"


@dataclass(frozen=True)
class FundingState:
    total_debt: float
    total_equity_required: float
    base_equity: float
    incremental_capex: float
    contingency_draw: float
    required_sponsor_support: float
    sponsor_headroom: float
    funding_shortfall: float


@dataclass(frozen=True)
class FinancialState:
    cfads_year_1: float
    annual_debt_service: float
    minimum_dscr: float
    equity_irr: float


@dataclass(frozen=True)
class CaseResult:
    case: ProjectCase
    stressed_project: ProjectInputs
    stressed_financing: FinancingInputs
    funding_state: FundingState
    financial_state: FinancialState
    driver: StressDriver
    magnitude: float


@dataclass(frozen=True)
class ConstraintResult:
    name: str
    boundary_type: str
    metric_value: float
    threshold_value: float
    headroom: float
    status: str
    independent: bool = True


@dataclass(frozen=True)
class BoundaryResult:
    driver: str
    constraint_name: str
    boundary_type: str
    boundary_magnitude: float


@dataclass(frozen=True)
class Scenario:
    name: str = "Base Case"
    capex_overrun_pct: float = 0.0
    schedule_delay_pct: float = 0.0
    revenue_reduction_pct: float = 0.0
    operating_cost_increase_pct: float = 0.0
    financing_cost_increase: float = 0.0


@dataclass(frozen=True)
class DelayAssumptions:
    baseline_schedule_months: float = 24.0
    debt_balance_exposure_share: float = 1.0
    annual_construction_overhead: float = 0.0
