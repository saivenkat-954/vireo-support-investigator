import os
import re
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "src")
)

from weekly_digest import calculate_weekly_digest
from dashboard_metrics import calculate_metrics


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash-lite"

PATTERNS = [
    r"\bthird time\b",
    r"\bsecond time\b",
    r"\balready called\b",
    r"\balready emailed\b",
    r"\bemailed twice\b",
    r"\balready contacted\b",
    r"\bagain\b",
    r"\bstill waiting\b",
    r"\bnothing changed\b",
    r"\bstill not\b",
    r"\bstill pending\b",
    r"\bno response\b",
    r"\bwaiting for your reply\b",
]


def detect_repeat_signal(text):
    text_lower = text.lower()
    matches = []

    for pattern in PATTERNS:
        match = re.search(pattern, text_lower)

        if match:
            matches.append(match.group(0))

    return len(matches) > 0, matches


def investigate_ticket(ticket_text):
    prompt = f"""
You are a customer-support quality investigator for Vireo Audio.

Analyze the following support ticket.

Determine whether there is evidence that the customer has already
attempted to get help or is experiencing a repeated/unresolved issue.

IMPORTANT:
- Use only evidence present in the ticket.
- Do not invent previous tickets, dates, actions, or customer history.
- Distinguish self-troubleshooting from previous contact with Vireo.
- If evidence is ambiguous, say so.
- Be concise and factual.

Return ONLY valid JSON:

{{
  "repeat_contact_signal": true,
  "confidence": "high",
  "evidence": [
    "short quote or specific evidence from the ticket"
  ],
  "reason": "brief explanation",
  "issue_theme": "short description",
  "recommended_action": "practical support action"
}}

Ticket:
{ticket_text}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return json.loads(response.text)


st.set_page_config(
    page_title="Vireo Support Investigator",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Vireo Support Investigator")

st.caption(
    "AI-assisted repeat-contact detection, investigation, and support performance dashboard."
)

st.subheader("🔎 Ticket Investigation")

ticket = st.text_area(
    "Paste customer support ticket",
    height=180,
    placeholder=(
        "Example:\n"
        "I have contacted support twice already and the issue "
        "still hasn't been fixed."
    )
)

if st.button("Analyze Ticket", type="primary"):

    if not ticket.strip():
        st.warning("Please enter a support ticket.")
        st.stop()

    baseline_signal, matches = detect_repeat_signal(ticket)

    st.subheader("1. Detection")

    if baseline_signal:
        st.error("⚠️ Repeat-contact signal detected")
    else:
        st.success("No repeat-contact keyword signal detected")

    if matches:
        st.write("Matched signals:")

        for match in matches:
            st.code(match)

    st.subheader("2. AI Investigation")

    with st.spinner("Gemini is investigating the ticket..."):

        try:
            result = investigate_ticket(ticket)

            col1, col2 = st.columns(2)

            with col1:
                st.write("**AI Signal**")
                st.write(
                    result.get(
                        "repeat_contact_signal"
                    )
                )

                st.write("**Confidence**")
                st.write(
                    result.get(
                        "confidence"
                    )
                )

                st.write("**Issue Theme**")
                st.write(
                    result.get(
                        "issue_theme"
                    )
                )

            with col2:
                st.write("**Reason**")
                st.write(
                    result.get(
                        "reason"
                    )
                )

                st.write("**Recommended Action**")
                st.info(
                    result.get(
                        "recommended_action",
                        "No recommendation provided."
                    )
                )

            st.write("**Evidence**")

            for evidence in result.get(
                "evidence",
                []
            ):
                st.code(evidence)

        except Exception as e:
            st.error(
                f"Gemini investigation failed: {e}"
            )


st.divider()

st.header("📊 Support Performance Dashboard")

st.write(
    "Management view of policy-period support performance, "
    "repeat contacts, SLA exposure, and resolution metrics."
)

if st.button(
    "Generate Support Dashboard",
    type="primary"
):

    try:
        metrics = calculate_metrics()

        st.subheader("Business KPIs")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Policy-Period Tickets",
            f"{metrics['policy_tickets']:,}"
        )

        col2.metric(
            "Completed Tickets",
            f"{metrics['completed_tickets']:,}"
        )

        col3.metric(
            "SLA Breach Rate",
            f"{metrics['sla_rate']:.2%}"
        )

        col4.metric(
            "Repeat-Contact Rate",
            f"{metrics['repeat_rate']:.2%}"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Repeat Contacts",
            f"{metrics['repeat_count']:,}"
        )

        col2.metric(
            "Repeat-Contact Cost",
            f"₹{metrics['repeat_cost']:,.0f}"
        )

        col3.metric(
            "Avg Cost / Repeat",
            f"₹{metrics['avg_repeat_cost']:,.2f}"
        )

        col4.metric(
            "SLA Credit Exposure",
            f"₹{metrics['sla_credit_exposure']:,.0f}"
        )

        st.subheader(
            "🎯 10% Repeat-Contact Reduction Scenario"
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Repeat Contacts Avoided",
            f"{metrics['avoided_repeats']:,}"
        )

        col2.metric(
            "Estimated Cost Avoided",
            f"₹{metrics['estimated_savings']:,.0f}"
        )

        st.caption(
            "Scenario based on a 10% reduction from the observed "
            "policy-period repeat-contact baseline."
        )

        st.subheader(
            "📈 SLA Performance by Channel"
        )

        channel_summary = metrics[
            "channel_summary"
        ].copy()

        channel_summary[
            "sla_breach_rate"
        ] = (
            channel_summary[
                "sla_breach_rate"
            ] * 100
        ).round(2)

        channel_summary = channel_summary.rename(
            columns={
                "channel": "Channel",
                "tickets": "Tickets",
                "sla_breaches": "SLA Breaches",
                "sla_breach_rate": "SLA Breach Rate (%)"
            }
        )

        st.dataframe(
            channel_summary,
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "🔥 Repeat-Contact Hotspots"
        )

        category_summary = metrics[
            "category_summary"
        ].copy()

        category_summary[
            "repeat_rate"
        ] = (
            category_summary[
                "repeat_rate"
            ] * 100
        ).round(2)

        category_summary = category_summary.rename(
            columns={
                "category": "Category",
                "completed": "Completed",
                "repeat_contacts": "Repeat Contacts",
                "repeat_rate": "Repeat Rate (%)"
            }
        )

        st.dataframe(
            category_summary,
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "💰 Repeat-Contact Cost by Channel"
        )

        channel_cost = metrics[
            "channel_cost"
        ].copy()

        channel_cost = channel_cost.rename(
            columns={
                "channel": "Channel",
                "repeat_contacts": "Repeat Contacts",
                "estimated_cost": "Estimated Cost (₹)"
            }
        )

        st.dataframe(
            channel_cost,
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "👥 Frontline Team Performance"
        )

        team_summary = metrics[
            "team_summary"
        ].copy()

        team_summary[
            "repeat_rate"
        ] = (
            team_summary[
                "repeat_rate"
            ] * 100
        ).round(2)

        team_summary[
            "sla_breach_rate"
        ] = (
            team_summary[
                "sla_breach_rate"
            ] * 100
        ).round(2)

        team_summary = team_summary.rename(
            columns={
                "assigned_team": "Team",
                "completed": "Completed",
                "repeat_contacts": "Repeat Contacts",
                "repeat_rate": "Repeat Rate (%)",
                "sla_breaches": "SLA Breaches",
                "sla_breach_rate": "SLA Breach Rate (%)"
            }
        )

        st.dataframe(
            team_summary,
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "🛠️ Tier 2 / Warranty Resolution"
        )

        tier2 = metrics[
            "tier2_resolution"
        ]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Tier 2 Tickets",
            f"{tier2['tickets']:,}"
        )

        col2.metric(
            "Median Resolution",
            f"{tier2['median_hours']:.2f} hrs"
        )

        col3.metric(
            "Average Resolution",
            f"{tier2['average_hours']:.2f} hrs"
        )

        st.metric(
            "P90 Resolution",
            f"{tier2['p90_hours']:.2f} hrs"
        )

        st.subheader(
            "📌 Management Takeaways"
        )

        st.write(
            f"• {metrics['repeat_count']:,} repeat contacts were identified "
            f"among {metrics['completed_tickets']:,} completed policy-period tickets."
        )

        st.write(
            f"• Repeat contacts represent "
            f"{metrics['repeat_rate']:.2%} of completed tickets."
        )

        st.write(
            f"• Estimated repeat-contact cost is "
            f"₹{metrics['repeat_cost']:,.0f}."
        )

        st.write(
            f"• A 10% reduction scenario represents approximately "
            f"{metrics['avoided_repeats']:,} fewer repeat contacts and "
            f"₹{metrics['estimated_savings']:,.0f} in estimated avoided contact cost."
        )

        st.write(
            f"• Potential SLA credit exposure from observed breaches is "
            f"₹{metrics['sla_credit_exposure']:,.0f}."
        )

        st.subheader(
            "ℹ️ Metric Definitions"
        )

        st.write(
            "Repeat contact is approximated using the same customer and "
            "same support category within 30 days of a previous resolution."
        )

        st.write(
            "The repeat-contact definition is a proxy because the dataset "
            "does not contain a dedicated issue ID."
        )

        st.write(
            "Tier 2 / Warranty is shown separately using resolution-time "
            "metrics rather than frontline ticket-volume comparison."
        )

    except Exception as e:
        st.error(
            f"Could not generate dashboard: {e}"
        )


st.divider()

st.header("🗓️ Weekly Support Digest")

st.write(
    "Weekly operating view of support volume, SLA performance, "
    "repeat contacts, and the frontline ticket-closure leaderboard."
)

try:

    tickets_for_weeks = pd.read_csv(
        "data/tickets_canonical.csv"
    )

    tickets_for_weeks[
        "created_at"
    ] = pd.to_datetime(
        tickets_for_weeks[
            "created_at"
        ],
        errors="coerce"
    )

    tickets_for_weeks = tickets_for_weeks[
        tickets_for_weeks[
            "created_at"
        ].notna()
        & (
            tickets_for_weeks[
                "created_at"
            ] >= pd.Timestamp("2025-04-01")
        )
    ].copy()

    tickets_for_weeks[
        "week_start"
    ] = (
        tickets_for_weeks[
            "created_at"
        ]
        .dt.to_period("W-SUN")
        .apply(lambda x: x.start_time)
    )

    week_options = sorted(
        tickets_for_weeks[
            "week_start"
        ].unique(),
        reverse=True
    )

    if len(week_options) > 0:

        selected_week = st.selectbox(
            "Select week",
            week_options,
            format_func=lambda x: (
                f"{x.strftime('%d %b %Y')} - "
                f"{(
                    x + pd.Timedelta(days=6)
                ).strftime('%d %b %Y')}"
            )
        )

        if st.button(
            "Generate Weekly Digest",
            type="primary"
        ):

            digest = calculate_weekly_digest(
                selected_week
            )

            st.subheader(
                f"Week of "
                f"{digest['week_start'].strftime('%d %b %Y')}"
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Tickets",
                f"{digest['tickets']:,}"
            )

            col2.metric(
                "Tickets Closed",
                f"{digest['completed']:,}"
            )

            col3.metric(
                "SLA Breach Rate",
                f"{digest['sla_rate']:.2%}"
            )

            col4.metric(
                "Repeat-Contact Rate",
                f"{digest['repeat_rate']:.2%}"
            )

            st.subheader(
                "🔥 Repeat-Contact Categories"
            )

            weekly_categories = digest[
                "category_summary"
            ].copy()

            weekly_categories[
                "repeat_rate"
            ] = (
                weekly_categories[
                    "repeat_rate"
                ] * 100
            ).round(2)

            weekly_categories = weekly_categories.rename(
                columns={
                    "category": "Category",
                    "completed": "Completed",
                    "repeat_contacts": "Repeat Contacts",
                    "repeat_rate": "Repeat Rate (%)"
                }
            )

            st.dataframe(
                weekly_categories,
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "🏆 Frontline Agent Leaderboard"
            )

            st.caption(
                "Ranked by tickets closed during the selected week. "
                "Tier 2 / Warranty is excluded from this volume leaderboard."
            )

            leaderboard = digest[
                "leaderboard"
            ].copy()

            leaderboard = leaderboard.rename(
                columns={
                    "rank": "Rank",
                    "agent_id": "Agent ID",
                    "name": "Agent",
                    "tickets_closed": "Tickets Closed"
                }
            )

            st.dataframe(
                leaderboard,
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "👥 Frontline Team Summary"
            )

            weekly_team = digest[
                "team_summary"
            ].copy()

            weekly_team[
                "repeat_rate"
            ] = (
                weekly_team[
                    "repeat_rate"
                ] * 100
            ).round(2)

            weekly_team = weekly_team.rename(
                columns={
                    "assigned_team": "Team",
                    "tickets_closed": "Tickets Closed",
                    "repeat_contacts": "Repeat Contacts",
                    "repeat_rate": "Repeat Rate (%)"
                }
            )

            st.dataframe(
                weekly_team,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.warning(
            "No policy-period weeks were found."
        )

except Exception as e:
    st.error(
        f"Could not generate weekly digest: {e}"
    )