import pandas as pd


POLICY_START = pd.Timestamp("2025-04-01")

SLA_TARGETS = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}

CONTACT_COSTS = {
    "chat": 210,
    "email": 260,
    "voice": 520,
    "social": 240,
}


def load_tickets():
    tickets = pd.read_csv("data/tickets_canonical.csv")

    for column in [
        "created_at",
        "first_response_at",
        "resolved_at",
    ]:
        tickets[column] = pd.to_datetime(
            tickets[column],
            errors="coerce"
        )

    return tickets


def calculate_metrics():
    tickets = load_tickets()

    policy_tickets = tickets[
        tickets["created_at"] >= POLICY_START
    ].copy()

    policy_tickets["response_minutes"] = (
        policy_tickets["first_response_at"]
        - policy_tickets["created_at"]
    ).dt.total_seconds() / 60

    policy_tickets["sla_target_minutes"] = (
        policy_tickets["channel"].map(SLA_TARGETS)
    )

    policy_tickets["sla_breach"] = (
        policy_tickets["response_minutes"]
        > policy_tickets["sla_target_minutes"]
    )

    responded = policy_tickets[
        policy_tickets["first_response_at"].notna()
    ]

    sla_breaches = int(
        responded["sla_breach"].sum()
    )

    sla_rate = (
        sla_breaches / len(responded)
        if len(responded)
        else 0
    )

    sla_credit_exposure = sla_breaches * 350

    completed = policy_tickets[
        policy_tickets["resolved_at"].notna()
    ].copy()

    completed = completed.sort_values(
        ["customer_id", "category", "resolved_at"]
    )

    completed["previous_resolution"] = (
        completed
        .groupby(
            ["customer_id", "category"]
        )["resolved_at"]
        .shift(1)
    )

    completed["days_since_previous"] = (
        completed["resolved_at"]
        - completed["previous_resolution"]
    ).dt.total_seconds() / 86400

    completed["repeat_contact"] = (
        completed["previous_resolution"].notna()
        & (completed["days_since_previous"] <= 30)
    )

    repeat_contacts = completed[
        completed["repeat_contact"]
    ].copy()

    repeat_count = len(repeat_contacts)

    repeat_rate = (
        repeat_count / len(completed)
        if len(completed)
        else 0
    )

    repeat_contacts["contact_cost"] = (
        repeat_contacts["channel"].map(CONTACT_COSTS)
    )

    repeat_cost = repeat_contacts[
        "contact_cost"
    ].sum()

    avg_repeat_cost = (
        repeat_cost / repeat_count
        if repeat_count
        else 0
    )

    category_summary = (
        completed
        .groupby("category")
        .agg(
            completed=("ticket_id", "count"),
            repeat_contacts=("repeat_contact", "sum")
        )
        .reset_index()
    )

    category_summary["repeat_rate"] = (
        category_summary["repeat_contacts"]
        / category_summary["completed"]
    )

    category_summary = category_summary.sort_values(
        "repeat_rate",
        ascending=False
    )

    channel_cost = (
        repeat_contacts
        .groupby("channel")
        .agg(
            repeat_contacts=("ticket_id", "count"),
            estimated_cost=("contact_cost", "sum")
        )
        .reset_index()
    )

    frontline = completed[
        ~completed["assigned_team"].eq(
            "Escalations & Warranty"
        )
    ].copy()

    frontline["sla_breach"] = (
        frontline["first_response_at"]
        - frontline["created_at"]
    ).dt.total_seconds() / 60 > frontline[
        "channel"
    ].map(SLA_TARGETS)

    team_summary = (
        frontline
        .groupby("assigned_team")
        .agg(
            completed=("ticket_id", "count"),
            repeat_contacts=("repeat_contact", "sum"),
            sla_breaches=("sla_breach", "sum")
        )
        .reset_index()
    )

    team_summary["repeat_rate"] = (
        team_summary["repeat_contacts"]
        / team_summary["completed"]
    )

    team_summary["sla_breach_rate"] = (
        team_summary["sla_breaches"]
        / team_summary["completed"]
    )

    team_summary = team_summary.sort_values(
        "completed",
        ascending=False
    )

    tier2 = completed[
        completed["assigned_team"].eq(
            "Escalations & Warranty"
        )
    ].copy()

    tier2["resolution_hours"] = (
        tier2["resolved_at"]
        - tier2["first_response_at"]
    ).dt.total_seconds() / 3600

    tier2_resolution = {
        "tickets": len(tier2),
        "median_hours": tier2["resolution_hours"].median(),
        "average_hours": tier2["resolution_hours"].mean(),
        "p90_hours": tier2["resolution_hours"].quantile(0.90),
    }

    channel_summary = (
        policy_tickets
        .groupby("channel")
        .agg(
            tickets=("ticket_id", "count"),
            sla_breaches=("sla_breach", "sum")
        )
        .reset_index()
    )

    channel_summary["sla_breach_rate"] = (
        channel_summary["sla_breaches"]
        / channel_summary["tickets"]
    )

    channel_summary = channel_summary.sort_values(
        "sla_breach_rate",
        ascending=False
    )

    target_reduction = 0.10

    avoided_repeats = round(
        repeat_count * target_reduction
    )

    estimated_savings = (
        repeat_cost * target_reduction
    )

    return {
        "policy_tickets": len(policy_tickets),
        "completed_tickets": len(completed),
        "responded_tickets": len(responded),
        "sla_breaches": sla_breaches,
        "sla_rate": sla_rate,
        "sla_credit_exposure": sla_credit_exposure,
        "repeat_count": repeat_count,
        "repeat_rate": repeat_rate,
        "repeat_cost": repeat_cost,
        "avg_repeat_cost": avg_repeat_cost,
        "category_summary": category_summary,
        "channel_cost": channel_cost,
        "channel_summary": channel_summary,
        "team_summary": team_summary,
        "tier2_resolution": tier2_resolution,
        "avoided_repeats": avoided_repeats,
        "estimated_savings": estimated_savings,
    }


if __name__ == "__main__":
    metrics = calculate_metrics()

    print("\n===== DASHBOARD METRICS =====")

    print(
        f"Policy tickets : "
        f"{metrics['policy_tickets']:,}"
    )

    print(
        f"Completed      : "
        f"{metrics['completed_tickets']:,}"
    )

    print(
        f"SLA breach     : "
        f"{metrics['sla_rate']:.2%}"
    )

    print(
        f"SLA exposure   : "
        f"₹{metrics['sla_credit_exposure']:,.0f}"
    )

    print(
        f"Repeat rate    : "
        f"{metrics['repeat_rate']:.2%}"
    )

    print(
        f"Repeat contacts: "
        f"{metrics['repeat_count']:,}"
    )

    print(
        f"Repeat cost    : "
        f"₹{metrics['repeat_cost']:,.0f}"
    )

    print(
        f"Avg repeat     : "
        f"₹{metrics['avg_repeat_cost']:,.2f}"
    )

    print(
        f"10% avoided    : "
        f"{metrics['avoided_repeats']:,}"
    )

    print(
        f"10% savings    : "
        f"₹{metrics['estimated_savings']:,.0f}"
    )