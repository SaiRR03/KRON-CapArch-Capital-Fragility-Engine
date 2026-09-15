# KRON Capital Fragility Engine™ v1.0 Alpha

**Deterministic capital resilience analysis for capital-intensive projects.**

KRON Capital Fragility Engine™ (CFE) asks one practical question:

> **How much adverse movement can a project's capital structure absorb before a defined financial intervention threshold is reached?**

This public Alpha is deliberately narrow. It exposes the generic deterministic financial engine, funding architecture, constraint engine, intervention-boundary solver, scenario layer and a synthetic example. It does **not** include KRON's private empirical research, proprietary datasets, reference-class construction, calibration, future exposure mapping, proprietary transmission coefficients, commercial response ranking or unreleased research.

## What the Alpha does

CFE translates five adverse scenario dimensions into a capital-resilience decision profile:

- Capital Expenditure overrun
- Schedule delay
- Revenue reduction
- Operating Cost increase
- Financing Cost increase

It evaluates the resulting project state against user-defined financial thresholds such as minimum DSCR, required Equity IRR and sponsor/liquidity support capacity.

The current deterministic chain is:

```text
Project economics + capital structure
                ↓
        User-defined scenario
                ↓
        Financial transmission
                ↓
 CFADS / Debt Service / DSCR / Equity IRR
                ↓
 Funding headroom / funding shortfall
                ↓
       Intervention boundaries
                ↓
     Capital Resilience Profile
                ↓
        Human investment judgement
```

## Important terminology

**Intervention Boundary**: the level of a stress driver at which the first independent financial threshold is reached.

**Remaining Stress Capacity**: intervention boundary less current stress.

**Stress Capacity Used**: current stress divided by the intervention boundary.

**Stress Capacity Used is not a probability.**

This release does not estimate default probability, empirical exceedance probability or a universal Capital Fragility score.

## Included public modules

```text
KRON-Capital-Fragility-Engine/
├── app.py
├── kron_cfe/
│   ├── financial_core.py
│   ├── funding.py
│   ├── constraints.py
│   ├── boundaries.py
│   ├── scenario.py
│   ├── decision.py
│   ├── models.py
│   └── __init__.py
├── examples/
│   ├── __init__.py
│   └── synthetic_case.py
├── tests/
│   └── test_alpha.py
├── requirements.txt
├── README.md
├── DISCLAIMER.md
├── CITATION.cff
└── .gitignore
```

## Quick start

Python **3.11** is recommended because the Alpha was validated against the Python 3.11 numerical stack.

### 1. Create a clean environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the tests

```bash
python -m pytest -q
```

### 4. Launch the app

```bash
python -m streamlit run app.py
```

## Frozen synthetic validation case

The bundled example is **synthetic** and exists only to reproduce the public Alpha mechanics.

| Parameter | Synthetic value |
|---|---:|
| Base Capital Expenditure | £100m |
| Debt | £70m |
| Initial Equity | £30m |
| Annual Revenue | £20m |
| Annual Operating Cost | £6m |
| CFADS | £14m |
| Cost of Debt | 6.00% |
| Debt Tenor | 15 years |
| Operating Life | 20 years |
| Minimum DSCR Threshold | 1.20x |
| Required Equity Return | 8.00% |
| Sponsor / Liquidity Support Capacity | £10m |

The synthetic thresholds are **example inputs**, not proprietary KRON commercial decision rules.

Expected base outputs are approximately:

- Annual Debt Service: **£7.2074m**
- DSCR: **1.94245x**
- Equity IRR: **22.9761%**

Expected first deterministic boundaries for the fixed-debt synthetic case are approximately:

| Stress driver | First intervention boundary | First threshold |
|---|---:|---|
| Investment Cost | +10.00% | Sponsor / Liquidity Support Capacity |
| Revenue | -23.305% | Required Equity Return |
| Operating Cost | +77.684% | Required Equity Return |
| Financing Cost | +847 bps | Minimum DSCR Threshold |

## Schedule-delay treatment

In the current Alpha, schedule delay is financially active through a transparent deterministic mechanism:

```text
Schedule delay
    ↓
Incremental construction time
    ↓
Additional IDC + explicit construction overhead
    ↓
Additional investment cost / funding requirement
    ↓
Sponsor headroom and funding shortfall
    ↓
Later equity cash-flow timing
    ↓
Equity IRR
```

The public Alpha does **not** invent a permanent revenue loss or arbitrary DSCR penalty from delay.

## Funding architectures

Three generic architectures are implemented:

1. `fixed_debt`
2. `constant_leverage`
3. `facility_then_sponsor`

These are stylised analytical structures, not legal or financing advice.

## What is deliberately not included

The public repository excludes:

- proprietary empirical calibration
- Capital Intelligence datasets
- private project/reference-class datasets
- unreleased research notes and working papers
- proprietary transmission coefficients
- private asset-exposure mapping
- private commercial decision thresholds
- response-ranking / structuring playbooks
- credentials, API keys or personal paths
- employer/client information

## Scope of v1.0 Alpha

The public release is a deterministic research Alpha intended for testing, critique and reproducibility. It is **not**:

- investment advice
- a credit rating
- a default model
- an empirical probability engine
- a regulatory model
- a substitute for project-finance due diligence

See [DISCLAIMER.md](DISCLAIMER.md).

## Feedback

Useful critique includes:

- financial logic errors
- edge cases that produce incoherent behaviour
- numerical instability
- usability problems
- terminology that is unclear to an investment committee
- cases where the first intervention boundary is economically misleading

Please open a GitHub Issue with a reproducible example where possible.

## Intellectual-property posture

This is a **source-available Alpha release**, not a disclosure of KRON's full research stack. The repository intentionally publishes the generic deterministic layer while keeping empirical calibration, datasets, unreleased research and future commercial logic outside the public release.

KRON Capital Fragility Engine™, KRON Capital Fragility Framework™ and KRON CapArch are used as KRON marks. See [DISCLAIMER.md](DISCLAIMER.md) for the release notice.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).
