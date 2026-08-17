# Careem's AI Challenge-1 — Risk Radar

A small AI workflow that turns messy project updates into an early-warning project delivery view.

## What it does

Risk Radar analyzes project notes and produces:

- Project health: GREEN / AMBER / RED
- Risks with severity and evidence
- Current blockers
- Cross-team dependencies
- Likely timeline impact
- Prioritized next actions

The prototype supports two modes:

1. **LLM mode** — calls any OpenAI-compatible chat-completions endpoint configured through environment variables.
2. **Demo mode** — deterministic sample output so the workflow can still be reviewed without exposing an API key.

The full production prompt is included in `prompt.md`.

## Why this challenge

Project updates often contain warning signals before they become visible in a status report. Risk Radar converts unstructured updates into structured delivery signals so teams can escalate dependencies and blockers earlier.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL printed by Streamlit.

## Optional LLM configuration

Set these environment variables before starting the app:

```bash
LLM_API_URL=https://YOUR_PROVIDER/v1/chat/completions
LLM_API_KEY=YOUR_KEY
LLM_MODEL=YOUR_MODEL
```

The code uses a standard chat-completions JSON request. If these variables are missing, the app automatically uses Demo mode.

## Files

- `app.py` — Streamlit prototype
- `sample_updates.csv` — self-created dummy project data
- `prompt.md` — structured AI prompt
- `submission_summary.txt` — short Careem's challenge submission summary

## Example workflow

```text
Project Updates
      |
      v
Risk Radar Prompt
      |
      v
Structured JSON
      |
      +--> Risks
      +--> Blockers
      +--> Dependencies
      +--> Timeline impact
      +--> Recommended actions
      |
      v
Project Health Dashboard
```

## Design choices

- Structured JSON makes the AI output easy to validate and render.
- Each risk includes evidence to reduce unsupported conclusions.
- Risks, blockers, and dependencies are kept separate.
- Human validation is expected for high-impact recommendations.
- Dummy data is used; no confidential company data is required.

## Future improvements

- Monitor Jira/Slack/project updates automatically.
- Compare today's signals with previous days.
- Add owner escalation and due dates.
- Track risk trends over time.
- Add confidence scores and human feedback.