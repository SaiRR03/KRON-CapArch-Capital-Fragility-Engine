from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from .constraints import evaluate_constraints
from .financial_core import run_case
from .models import BoundaryResult, ProjectCase

_DRIVER_MAX = {
    "capex": 3.0,
    "revenue": 0.99,
    "opex": 5.0,
    "interest_rate": 0.50,
}


def _headroom(case: ProjectCase, driver: str, magnitude: float, constraint_name: str) -> float:
    result = run_case(case, driver=driver, magnitude=magnitude)
    return evaluate_constraints(result)[constraint_name].headroom


def solve_constraint_boundary(
    case: ProjectCase,
    driver: str,
    constraint_name: str,
    max_stress: float | None = None,
    grid_points: int = 80,
) -> BoundaryResult | None:
    constraints0 = evaluate_constraints(run_case(case))
    c0 = constraints0[constraint_name]
    if not c0.independent:
        return None
    if abs(c0.headroom) <= 1e-9:
        return BoundaryResult(driver, constraint_name, c0.boundary_type, 0.0)
    if c0.headroom < 0:
        return BoundaryResult(driver, constraint_name, c0.boundary_type, 0.0)

    upper = float(max_stress if max_stress is not None else _DRIVER_MAX[driver])
    grid = np.linspace(0.0, upper, grid_points + 1)
    left = 0.0
    f_left = c0.headroom

    for right in grid[1:]:
        right = float(right)
        f_right = _headroom(case, driver, right, constraint_name)
        if not np.isfinite(f_right):
            left, f_left = right, f_right
            continue
        if abs(f_right) <= 1e-9:
            root = right
            cr = evaluate_constraints(run_case(case, driver, root))[constraint_name]
            return BoundaryResult(driver, constraint_name, cr.boundary_type, float(root))
        if np.isfinite(f_left) and f_left * f_right < 0:
            root = brentq(
                lambda x: _headroom(case, driver, float(x), constraint_name),
                left,
                right,
                xtol=1e-12,
            )
            cr = evaluate_constraints(run_case(case, driver, root))[constraint_name]
            return BoundaryResult(driver, constraint_name, cr.boundary_type, float(root))
        left, f_left = right, f_right
    return None


def solve_driver_boundaries(case: ProjectCase, driver: str) -> list[BoundaryResult]:
    results = []
    for name in ("DSCR", "Equity IRR", "Sponsor Support"):
        boundary = solve_constraint_boundary(case, driver, name)
        if boundary is not None:
            results.append(boundary)
    return sorted(results, key=lambda x: x.boundary_magnitude)


def first_boundary(case: ProjectCase, driver: str) -> BoundaryResult:
    results = solve_driver_boundaries(case, driver)
    if not results:
        raise ValueError(f"No finite boundary found for {driver}")
    return results[0]
