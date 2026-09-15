from __future__ import annotations

from .models import FinancingInputs, FundingState


def _base_debt(base_capex: float, financing: FinancingInputs) -> float:
    return float(
        financing.committed_debt
        if financing.committed_debt is not None
        else base_capex * financing.debt_share
    )


def allocate_funding(base_capex: float, stressed_capex: float, financing: FinancingInputs) -> FundingState:
    base_debt = _base_debt(base_capex, financing)
    base_equity = base_capex - base_debt
    incremental_capex = max(stressed_capex - base_capex, 0.0)

    if financing.funding_rule == "constant_leverage":
        total_debt = stressed_capex * financing.debt_share
        total_equity = stressed_capex - total_debt
        return FundingState(
            total_debt=float(total_debt),
            total_equity_required=float(total_equity),
            base_equity=float(base_equity),
            incremental_capex=float(incremental_capex),
            contingency_draw=0.0,
            required_sponsor_support=max(total_equity - base_equity, 0.0),
            sponsor_headroom=float("inf"),
            funding_shortfall=0.0,
        )

    if financing.funding_rule == "fixed_debt":
        required_sponsor = incremental_capex
        headroom = financing.sponsor_support_capacity - required_sponsor
        shortfall = max(-headroom, 0.0)
        return FundingState(
            total_debt=float(base_debt),
            total_equity_required=float(stressed_capex - base_debt),
            base_equity=float(base_equity),
            incremental_capex=float(incremental_capex),
            contingency_draw=0.0,
            required_sponsor_support=float(required_sponsor),
            sponsor_headroom=float(headroom),
            funding_shortfall=float(shortfall),
        )

    if financing.funding_rule == "facility_then_sponsor":
        facility_draw = min(incremental_capex, financing.contingency_facility)
        required_sponsor = max(incremental_capex - facility_draw, 0.0)
        headroom = financing.sponsor_support_capacity - required_sponsor
        shortfall = max(-headroom, 0.0)
        total_debt = base_debt + facility_draw
        total_equity = stressed_capex - total_debt
        return FundingState(
            total_debt=float(total_debt),
            total_equity_required=float(total_equity),
            base_equity=float(base_equity),
            incremental_capex=float(incremental_capex),
            contingency_draw=float(facility_draw),
            required_sponsor_support=float(required_sponsor),
            sponsor_headroom=float(headroom),
            funding_shortfall=float(shortfall),
        )

    raise ValueError(f"Unknown funding rule: {financing.funding_rule}")
