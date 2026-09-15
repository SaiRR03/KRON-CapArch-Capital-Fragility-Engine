from __future__ import annotations

import numpy as np

from .models import CaseResult, ConstraintResult


def classify_status(headroom: float, active: bool = True, tolerance: float = 1e-9) -> str:
    if not active or not np.isfinite(headroom):
        return "NOT ACTIVE"
    if headroom < -tolerance:
        return "BREACHED"
    if abs(headroom) <= tolerance:
        return "BOUNDARY"
    return "HEADROOM"


def evaluate_constraints(result: CaseResult) -> dict[str, ConstraintResult]:
    c = result.case.constraints
    f = result.stressed_financing
    fs = result.financial_state
    funding = result.funding_state

    dscr_headroom = fs.minimum_dscr - c.minimum_dscr
    irr_headroom = fs.equity_irr - c.equity_irr_hurdle if np.isfinite(fs.equity_irr) else np.nan

    sponsor_active = f.funding_rule in {"fixed_debt", "facility_then_sponsor"} and np.isfinite(f.sponsor_support_capacity)
    sponsor_headroom = funding.sponsor_headroom if sponsor_active else np.inf

    # In fixed-debt and facility-then-sponsor cases the funding shortfall is mechanically
    # downstream of the same available support capacity, so it is reported but marked
    # non-independent to avoid double-counting the same intervention boundary.
    funding_headroom = -funding.funding_shortfall if funding.funding_shortfall > 0 else sponsor_headroom

    return {
        "DSCR": ConstraintResult(
            name="DSCR",
            boundary_type="FINANCIAL",
            metric_value=float(fs.minimum_dscr),
            threshold_value=float(c.minimum_dscr),
            headroom=float(dscr_headroom),
            status=classify_status(dscr_headroom),
            independent=True,
        ),
        "Equity IRR": ConstraintResult(
            name="Equity IRR",
            boundary_type="ECONOMIC",
            metric_value=float(fs.equity_irr),
            threshold_value=float(c.equity_irr_hurdle),
            headroom=float(irr_headroom),
            status=classify_status(irr_headroom),
            independent=True,
        ),
        "Sponsor Support": ConstraintResult(
            name="Sponsor Support",
            boundary_type="FUNDING",
            metric_value=float(funding.required_sponsor_support),
            threshold_value=float(f.sponsor_support_capacity),
            headroom=float(sponsor_headroom),
            status=classify_status(sponsor_headroom, sponsor_active),
            independent=sponsor_active,
        ),
        "Total Funding": ConstraintResult(
            name="Total Funding",
            boundary_type="FUNDING",
            metric_value=float(funding.funding_shortfall),
            threshold_value=0.0,
            headroom=float(funding_headroom),
            status="BREACHED" if funding.funding_shortfall > 1e-9 else "HEADROOM",
            independent=False,
        ),
    }
