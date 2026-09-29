# Vireo Support Investigator

A lightweight AI-assisted customer-support investigation and management dashboard for Vireo Audio.

## Problem

Vireo wants a simple weekly support digest and a way to identify customers who appear to be returning with unresolved issues. The solution combines deterministic repeat-contact detection with Gemini-assisted investigation.

## Business Goal

**Target: reduce repeat contacts by 10% from the observed policy-period baseline.**

Policy period: **1 April 2025 onward**.

| Metric | Baseline |
|---|---:|
| Policy-period tickets | 10,867 |
| Completed tickets | 10,322 |
| Repeat contacts | 1,286 |
| Repeat-contact rate | 12.46% |
| Estimated repeat-contact cost | ₹332,810 |
| SLA breach rate | 8.81% |
| Potential SLA credit exposure | ₹334,950 |

A 10% reduction scenario is approximately **129 fewer repeat contacts** and **₹33,281 estimated contact cost avoided**. This is a scenario, not a guaranteed saving.

## Architecture

```text
Ticket
  ↓
Deterministic repeat-contact signal
  ↓
Gemini investigation
  ↓
Evidence + reason + issue theme + recommended action
  ↓
Management dashboard
```

Gemini is deliberately used as an investigation/reasoning layer, not as the primary binary classifier.

## Evaluation

100-ticket labelled evaluation:

| Approach | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Deterministic baseline | 95.00% | 94.00% | 95.92% | 94.95% |
| Gemini binary classifier | 60.00% | 69.57% | 32.65% | 44.44% |

The deterministic baseline performed better for the binary classification task, so Gemini was repositioned to provide evidence, reasoning, issue themes and recommended actions.

## Repeat-contact definition

The policy defines repeat contact as the same customer and same issue within 30 days. The dataset has no dedicated issue ID, so this project uses **same customer + same category + previous resolution within 30 days** as an approximation.

## Data cleaning

The export contains duplicate ticket IDs related to migration/re-import history. The canonical dataset prioritizes the current `helpdesk` record over `legacy_fd` and retains one record per ticket ID. The raw source is not modified.

## Policy metrics

Policy v3.2 defines first-response targets:

- Chat: 15 minutes
- Voice: 2 hours
- Social: 4 hours
- Email: 8 hours

Planning contact costs:

- Chat ₹210
- Email ₹260
- Voice ₹520
- Social ₹240
- Blended ₹290

Each missed first-response target generates a ₹350 store-credit exposure.

Tier-2/Warranty work is reported separately using resolution time rather than ticket-volume comparison.

## Key findings

Policy-period repeat rates include:

- Delivery & Shipping: 15.88%
- Audio Quality: 14.63%
- Charging & Battery: 14.59%
- Connectivity: 13.80%
- Returns & Refunds: 13.59%

These are descriptive findings and do not establish causation.

## AI prompt design

The investigator is instructed to use only ticket evidence, avoid inventing history, distinguish self-troubleshooting from previous Vireo contact, identify ambiguity, and return structured JSON containing:

- `repeat_contact_signal`
- `confidence`
- `evidence`
- `reason`
- `issue_theme`
- `recommended_action`

## Discarded approaches

1. **Gemini as the primary binary classifier:** evaluated and discarded because F1 was 44.44% versus 94.95% for the deterministic baseline.
2. **OpenAI API test:** attempted, but the available account returned an insufficient-quota/exhausted-credit response, so Gemini was used for the working AI layer.
3. **Full LLM processing of the historical dataset:** not used; the deterministic layer handles scalable screening and Gemini is used selectively for investigation.

## AI usage and cost disclosure

AI assistance was used during development for prompt design, coding/debugging, Gemini integration, evaluation workflow design, disagreement analysis and documentation.

The application uses Gemini through the Google GenAI Python SDK. The API key is loaded from `.env` and must not be committed to Git.

No unverified API billing amount is claimed.

## Limitations

- No dedicated issue ID; category is used as an issue proxy.
- Keyword signals can produce false positives from self-troubleshooting.
- Migration/re-import history affects some records.
- Gemini output is not treated as ground truth.
- The 10% saving figure is a scenario, not a guarantee.
- SLA credit exposure is potential exposure, not realized savings.

## Project structure

```text
vireo-support/
├── app/app.py
├── data/
│   ├── tickets.csv
│   ├── tickets_canonical.csv
│   ├── evaluation_sample.csv
│   ├── gemini_evaluation_results.csv
│   └── gemini_disagreements.csv
├── src/
│   ├── 01_explore.py
│   ├── 02_clean.py
│   ├── 03_eda.py
│   ├── 04_sla_analysis.py
│   ├── 05_sla_deep_dive.py
│   ├── 06_repeat_contacts.py
│   ├── 07_repeat_cost.py
│   ├── 08_resolution_analysis.py
│   ├── 09_repeat_vs_resolution.py
│   ├── 10_text_exploration.py
│   ├── 11_repeat_signal_baseline.py
│   ├── 12_create_eval_sample.py
│   ├── 13_evaluate_baseline.py
│   ├── 14_test_gemini.py
│   ├── 15_ai_investigator.py
│   ├── 16_evaluate_gemini.py
│   ├── 17_compare_models.py
│   ├── 18_business_metrics.py
│   └── dashboard_metrics.py
├── .env
├── .gitignore
└── README.md
```

## Run

```powershell
pip install pandas streamlit python-dotenv google-genai
python -m streamlit run app/app.py
```

`.env`:

```text
GEMINI_API_KEY=YOUR_KEY
```

Never commit the real key.

## Demo flow

```text
Problem → Dashboard → Repeat hotspot → Ticket investigation
→ Deterministic signal → Gemini evidence/reasoning
→ Recommended action → Evaluation → 10% business scenario
```
