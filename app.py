from __future__ import annotations

import pandas as pd
import streamlit as st

from kron_cfe import (
    ConstraintInputs,
    DelayAssumptions,
    FinancingInputs,
    ProjectCase,
    ProjectInputs,
    Scenario,
    build_decision_profile,
)

st.set_page_config(page_title="KRON Capital Fragility Engine", layout="wide")


def pct(x: float) -> float:
    return float(x) / 100.0


def bps(x: float) -> float:
    return float(x) / 10000.0


def money(x: float) -> str:
    x = 0.0 if abs(float(x)) < 0.005 else float(x)
    return f"£{x:,.2f}m"


def percent(x: float) -> str:
    return f"{float(x) * 100:.2f}%"


def fmt_resilience(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["Current Stress", "Intervention Boundary", "Remaining Stress Capacity"]:
        out[col] = [f"{v*100:.2f}%" if ch != "Financing Cost" else f"{v*10000:.0f} bps" for v, ch in zip(out[col], out["Financial Channel"])]
    out["Stress Capacity Used"] = out["Stress Capacity Used"].map(lambda x: f"{x*100:.1f}%")
    return out


st.title("KRON Capital Fragility Engine™")
st.caption("CFE v1.0 Alpha | Deterministic Capital Resilience Analysis")
st.write("Test how much adverse movement a project's capital structure can absorb before a financial intervention threshold is reached.")

with st.sidebar.form("cfe_form"):
    st.header("Project economics")
    capex = st.number_input("Capital Expenditure (£m)", min_value=0.01, value=100.0, step=1.0)
    revenue = st.number_input("Annual Revenue (£m)", min_value=0.0, value=20.0, step=1.0)
    opex = st.number_input("Annual Operating Costs (£m)", min_value=0.0, value=6.0, step=0.5)
    life = st.number_input("Operating life (years)", min_value=1, value=20, step=1)

    st.header("Capital structure")
    funding_rule = st.selectbox("Funding rule", ["fixed_debt", "constant_leverage", "facility_then_sponsor"])
    debt_share = st.number_input("Debt / Total Capital (%)", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
    use_calculated_debt = st.checkbox("Calculate committed debt from leverage", value=False)
    committed_debt_input = st.number_input("Committed Debt (£m)", min_value=0.0, value=70.0, step=1.0, disabled=use_calculated_debt)
    rate = st.number_input("Cost of Debt (%)", min_value=0.0, value=6.0, step=0.25)
    tenor = st.number_input("Debt tenor (years)", min_value=1, value=15, step=1)
    sponsor_capacity = st.number_input("Sponsor / Liquidity Support Capacity (£m)", min_value=0.0, value=10.0, step=1.0)
    facility = st.number_input("Contingency Facility (£m)", min_value=0.0, value=0.0, step=1.0)

    st.header("Financial thresholds")
    min_dscr = st.number_input("Minimum DSCR Threshold (x)", min_value=0.01, value=1.20, step=0.05)
    irr_hurdle = st.number_input("Required Equity Return (%)", min_value=0.0, value=8.0, step=0.5)

    st.header("Schedule")
    baseline_months = st.number_input("Baseline construction schedule (months)", min_value=1.0, value=24.0, step=1.0)
    debt_exposed = st.number_input("Debt exposed during delay (%)", min_value=0.0, max_value=100.0, value=100.0, step=5.0)
    annual_overhead = st.number_input("Annual construction overhead during delay (£m)", min_value=0.0, value=0.0, step=0.5)

    st.header("Scenario")
    scenario_name = st.text_input("Scenario name", value="Base Case")
    s_capex = st.slider("Capital Expenditure Overrun (%)", 0.0, 100.0, 0.0, 1.0)
    s_delay = st.slider("Schedule Delay (%)", 0.0, 100.0, 0.0, 1.0)
    s_revenue = st.slider("Revenue Reduction (%)", 0.0, 100.0, 0.0, 1.0)
    s_opex = st.slider("Operating Cost Increase (%)", 0.0, 200.0, 0.0, 1.0)
    s_rate = st.slider("Financing Cost Increase (bps)", 0, 2000, 0, 25)
    run = st.form_submit_button("Run CFE Analysis", type="primary", use_container_width=True)

if not run:
    st.info("Set assumptions in the sidebar and click Run CFE Analysis.")
    st.stop()

has_stress = any([s_capex > 0, s_delay > 0, s_revenue > 0, s_opex > 0, s_rate > 0])
if has_stress and scenario_name.strip().lower() == "base case":
    scenario_name = "User Scenario"

case = ProjectCase(
    project=ProjectInputs(
        base_capex=float(capex),
        annual_revenue=float(revenue),
        annual_opex=float(opex),
        operating_years=int(life),
    ),
    financing=FinancingInputs(
        funding_rule=funding_rule,
        debt_share=pct(debt_share),
        committed_debt=None if use_calculated_debt else float(committed_debt_input),
        annual_interest_rate=pct(rate),
        debt_tenor_years=int(tenor),
        sponsor_support_capacity=float(sponsor_capacity),
        contingency_facility=float(facility),
    ),
    constraints=ConstraintInputs(minimum_dscr=float(min_dscr), equity_irr_hurdle=pct(irr_hurdle)),
    case_name="User Case",
)
scenario = Scenario(
    name=scenario_name,
    capex_overrun_pct=pct(s_capex),
    schedule_delay_pct=pct(s_delay),
    revenue_reduction_pct=pct(s_revenue),
    operating_cost_increase_pct=pct(s_opex),
    financing_cost_increase=bps(s_rate),
)
delay = DelayAssumptions(
    baseline_schedule_months=float(baseline_months),
    debt_balance_exposure_share=pct(debt_exposed),
    annual_construction_overhead=float(annual_overhead),
)

with st.spinner("Running CFE analysis..."):
    profile = build_decision_profile(case, scenario, delay)

st.subheader("Capital Resilience Decision Profile")
if profile.model_status == "INTERVENTION THRESHOLD BREACHED":
    st.error(profile.model_status)
elif profile.model_status == "AT INTERVENTION BOUNDARY":
    st.warning(profile.model_status)
else:
    st.success(profile.model_status)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Primary Vulnerability", profile.primary_vulnerability)
c2.metric("Base DSCR", f"{profile.base_dscr:.2f}x")
c3.metric("Base Equity IRR", percent(profile.base_equity_irr))
c4.metric("Delay-Adjusted Equity IRR", percent(profile.delay_adjusted_equity_irr))

c5, c6, c7 = st.columns(3)
c5.metric("Nearest / First Financial Threshold", profile.first_financial_threshold_reached)
c6.metric("Sponsor / Liquidity Headroom", money(profile.scenario_sponsor_headroom))
c7.metric("Funding Shortfall", money(profile.scenario_funding_shortfall))

st.subheader("Capital Resilience Profile")
st.markdown(fmt_resilience(profile.resilience_profile).to_html(index=False), unsafe_allow_html=True)

st.subheader("Schedule Transmission")
schedule = profile.schedule_profile.copy()
st.markdown(schedule.to_html(index=False), unsafe_allow_html=True)

with st.expander("Why did CFE reach this state?"):
    st.markdown(profile.why_trace.to_html(index=False), unsafe_allow_html=True)

st.divider()
st.caption(
    "CFE v1.0 Alpha is deterministic. Stress Capacity Utilisation is not a probability. "
    "No empirical calibration, default probability, or autonomous investment recommendation is included."
)
