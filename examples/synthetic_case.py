from kron_cfe import ConstraintInputs, DelayAssumptions, FinancingInputs, ProjectCase, ProjectInputs, Scenario


def build_synthetic_case() -> ProjectCase:
    """Synthetic Action 2-style example used for public testing only."""
    return ProjectCase(
        project=ProjectInputs(
            base_capex=100.0,
            annual_revenue=20.0,
            annual_opex=6.0,
            operating_years=20,
        ),
        financing=FinancingInputs(
            funding_rule="fixed_debt",
            debt_share=0.70,
            committed_debt=70.0,
            annual_interest_rate=0.06,
            debt_tenor_years=15,
            sponsor_support_capacity=10.0,
            contingency_facility=0.0,
        ),
        constraints=ConstraintInputs(
            minimum_dscr=1.20,
            equity_irr_hurdle=0.08,
        ),
        case_name="Synthetic BESS Example",
    )


def base_scenario() -> Scenario:
    return Scenario(name="Base Case")


def combined_breach_scenario() -> Scenario:
    return Scenario(name="Combined Breach", capex_overrun_pct=0.10, schedule_delay_pct=0.20)


def default_delay_assumptions() -> DelayAssumptions:
    return DelayAssumptions(
        baseline_schedule_months=24.0,
        debt_balance_exposure_share=1.0,
        annual_construction_overhead=0.0,
    )
