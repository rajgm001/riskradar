import os
import json
import csv
from io import StringIO

import requests
import streamlit as st

st.set_page_config(page_title="Careem's AI challenge-1 Risk Radar", page_icon="📡", layout="wide")

SYSTEM_PROMPT = """
You are Risk Radar, an AI project-delivery analyst.

Inspect project updates and identify risks, blockers, dependencies, timeline impact,
and next actions early.

Rules:
1. Do not invent facts unsupported by the updates.
2. Risk = possible future problem.
3. Blocker = something currently preventing progress.
4. Dependency = one task/team/output another depends on.
5. Give each risk severity: LOW, MEDIUM, HIGH, CRITICAL.
6. Include concise evidence for every risk/blocker.
7. Infer timeline impact only when evidence supports it.
8. Return valid JSON only.

Return exactly this schema:
{
  "project_health": "GREEN | AMBER | RED",
  "health_reason": "short explanation",
  "risks": [
    {
      "title": "string",
      "severity": "LOW | MEDIUM | HIGH | CRITICAL",
      "evidence": "string",
      "impact": "string"
    }
  ],
  "blockers": [
    {
      "title": "string",
      "owner_or_team": "string",
      "evidence": "string"
    }
  ],
  "dependencies": [
    {
      "from": "string",
      "depends_on": "string",
      "reason": "string"
    }
  ],
  "timeline_impact": "string",
  "recommended_actions": [
    {
      "priority": 1,
      "action": "string",
      "owner_or_team": "string"
    }
  ]
}
""".strip()

SAMPLE_NOTES = """2026-08-10 | Payments | Rahul | Payment API development is 80% complete and on track.
2026-08-11 | Security | Aisha | Production credentials approval is still pending.
2026-08-12 | Vendor | External | Vendor API change may be delayed until Friday.
2026-08-13 | QA | John | Payment testing cannot start until production credentials are available.
2026-08-14 | Release | Sara | Production release is planned for Monday with very little test buffer."""

def demo_analysis():
    return {
        "project_health": "RED",
        "health_reason": "QA is currently blocked, a vendor change may slip, and the Monday release has very little testing buffer.",
        "risks": [
            {
                "title": "Vendor API change may be delayed",
                "severity": "HIGH",
                "evidence": "The vendor said the API change may move to Friday.",
                "impact": "Late delivery could compress integration and testing time before Monday."
            },
            {
                "title": "Insufficient test buffer before release",
                "severity": "HIGH",
                "evidence": "The release is planned for Monday with very little test buffer.",
                "impact": "Any additional delay could push the release or increase production risk."
            }
        ],
        "blockers": [
            {
                "title": "QA cannot start payment testing",
                "owner_or_team": "Security / QA",
                "evidence": "Testing cannot start until production credentials are available."
            }
        ],
        "dependencies": [
            {
                "from": "Payment testing",
                "depends_on": "Production credentials",
                "reason": "QA explicitly stated testing cannot start without the credentials."
            },
            {
                "from": "Production credentials",
                "depends_on": "Security approval",
                "reason": "Security approval is still pending."
            },
            {
                "from": "Monday release",
                "depends_on": "Payment testing",
                "reason": "The release has very little testing buffer."
            }
        ],
        "timeline_impact": "The Monday release is at risk. A Friday vendor delivery leaves little room for integration and QA.",
        "recommended_actions": [
            {
                "priority": 1,
                "action": "Escalate production credential approval today.",
                "owner_or_team": "Security"
            },
            {
                "priority": 2,
                "action": "Request a firm vendor delivery commitment and fallback plan.",
                "owner_or_team": "Vendor / Payments"
            },
            {
                "priority": 3,
                "action": "Prepare a release contingency if testing cannot complete safely.",
                "owner_or_team": "Release / QA"
            }
        ]
    }

def call_llm(project_updates):
    url = os.getenv("LLM_API_URL")
    key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    if not (url and key and model):
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Analyze the following project updates and return Risk Radar JSON only:\n\n{project_updates}",
            },
        ],
        "temperature": 0.2,
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()

    return json.loads(content)

def csv_to_notes(file_bytes):
    text = file_bytes.decode("utf-8")
    rows = list(csv.DictReader(StringIO(text)))
    lines = []
    for row in rows:
        lines.append(
            f'{row.get("date","")} | {row.get("team","")} | {row.get("owner","")} | {row.get("update","")}'
        )
    return "\n".join(lines)

def severity_icon(severity):
    return {
        "CRITICAL": "🛑",
        "HIGH": "🔴",
        "MEDIUM": "🟠",
        "LOW": "🟡",
    }.get(severity, "⚪")

st.title("📡 Risk Radar")
st.caption("Careem's AI Challenge-1 — early warning for project delivery risks, blockers and dependencies")

with st.sidebar:
    st.header("Prototype mode")
    has_llm = all([
        os.getenv("LLM_API_URL"),
        os.getenv("LLM_API_KEY"),
        os.getenv("LLM_MODEL"),
    ])
    if has_llm:
        st.success("LLM mode configured")
    else:
        st.info("Demo mode active")
    st.markdown(
        "The same structured prompt is used for LLM mode. Demo mode keeps the prototype reviewable without exposing an API key."
    )

uploaded = st.file_uploader("Optional: upload project updates CSV", type=["csv"])

if uploaded is not None:
    project_updates = csv_to_notes(uploaded.getvalue())
else:
    project_updates = SAMPLE_NOTES

project_updates = st.text_area(
    "Project updates",
    value=project_updates,
    height=220,
)

if st.button("Analyze project risk", type="primary", use_container_width=True):
    with st.spinner("Analyzing updates..."):
        try:
            result = call_llm(project_updates)
            source = "LLM"
            if result is None:
                result = demo_analysis()
                source = "Demo"
        except Exception as exc:
            st.warning(f"LLM call failed, so the prototype switched to Demo mode. Details: {exc}")
            result = demo_analysis()
            source = "Demo"

    health = result.get("project_health", "UNKNOWN")
    health_icon = {"GREEN": "🟢", "AMBER": "🟠", "RED": "🔴"}.get(health, "⚪")

    st.subheader(f"{health_icon} Project Health: {health}")
    st.write(result.get("health_reason", ""))
    st.caption(f"Analysis source: {source}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Risks", len(result.get("risks", [])))
    c2.metric("Blockers", len(result.get("blockers", [])))
    c3.metric("Dependencies", len(result.get("dependencies", [])))

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("⚠️ Risks")
        for risk in result.get("risks", []):
            sev = risk.get("severity", "")
            with st.container(border=True):
                st.markdown(f"**{severity_icon(sev)} {risk.get('title','')} — {sev}**")
                st.write(f"**Evidence:** {risk.get('evidence','')}")
                st.write(f"**Impact:** {risk.get('impact','')}")

        st.subheader("⛔ Blockers")
        for blocker in result.get("blockers", []):
            with st.container(border=True):
                st.markdown(f"**{blocker.get('title','')}**")
                st.write(f"**Owner/team:** {blocker.get('owner_or_team','')}")
                st.write(f"**Evidence:** {blocker.get('evidence','')}")

    with right:
        st.subheader("🔗 Dependencies")
        for dep in result.get("dependencies", []):
            with st.container(border=True):
                st.markdown(f"**{dep.get('from','')} → {dep.get('depends_on','')}**")
                st.write(dep.get("reason", ""))

        st.subheader("⏱️ Timeline impact")
        st.info(result.get("timeline_impact", "No timeline impact identified."))

        st.subheader("✅ Recommended actions")
        actions = sorted(result.get("recommended_actions", []), key=lambda x: x.get("priority", 999))
        for action in actions:
            st.markdown(
                f"**{action.get('priority','')}. {action.get('action','')}**  \n"
                f"Owner/team: {action.get('owner_or_team','')}"
            )

    with st.expander("View structured JSON"):
        st.json(result)

with st.expander("What the AI is asked to do"):
    st.code(SYSTEM_PROMPT, language="text")