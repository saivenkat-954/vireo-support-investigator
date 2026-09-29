import pandas as pd


POLICY_START = pd.Timestamp("2025-04-01")

SLA_TARGETS = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}


def load_data():
    tickets = pd.read_csv("data/tickets_canonical.csv")
    agents = pd.read_csv("data/agents.csv")

    for column in [
        "created_at",
        "first_response_at",
        "resolved_at",
    ]:
        tickets[column] = pd.to_datetime(
            tickets[column],
            errors="coerce"
        )

    for column in [
        "from_date",
        "to_date",
    ]:
        agents[column] = pd.to_datetime(
            agents[column],
            errors="coerce"
        )

    return tickets, agents


def calculate_weekly_digest(week_start):
    tickets, agents = load_data()

    week_start = pd.Timestamp(week_start)
    week_end = week_start + pd.Timedelta(days=7)

    weekly = tickets[
        (tickets["created_at"] >= week_start)
        & (tickets["created_at"] < week_end)
    ].copy()

    weekly["response_minutes"] = (
        weekly["first_response_at"]
        - weekly["created_at"]
    ).dt.total_seconds() / 60

    weekly["sla_target_minutes"] = (
        weekly["channel"].map(SLA_TARGETS)
    )

    weekly["sla_breach"] = (
        weekly["response_minutes"]
        > weekly["sla_target_minutes"]
    )

    responded = weekly[
        weekly["first_response_at"].notna()
    ]

    sla_breaches = int(
        responded["sla_breach"].sum()
    )

    sla_rate = (
        sla_breaches / len(responded)
        if len(responded)
        else 0
    )

    completed = weekly[
        weekly["resolved_at"].notna()
    ].copy()

    completed = completed.sort_values(
        ["customer_id", "category", "resolved_at"]
    )

    all_completed = tickets[
        tickets["resolved_at"].notna()
    ].copy()

    all_completed = all_completed.sort_values(
        ["customer_id", "category", "resolved_at"]
    )

    all_completed["previous_resolution"] = (
        all_completed
        .groupby(
            ["customer_id", "category"]
        )["resolved_at"]
        .shift(1)
    )

    all_completed["days_since_previous"] = (
        all_completed["resolved_at"]
        - all_completed["previous_resolution"]
    ).dt.total_seconds() / 86400

    all_completed["repeat_contact"] = (
        all_completed["previous_resolution"].notna()
        & (
            all_completed["days_since_previous"] <= 30
        )
    )

    repeat_lookup = all_completed[
        [
            "ticket_id",
            "repeat_contact"
        ]
    ]

    completed = completed.merge(
        repeat_lookup,
        on="ticket_id",
        how="left"
    )

    completed["repeat_contact"] = (
        completed["repeat_contact"].fillna(False)
    )

    repeat_contacts = int(
        completed["repeat_contact"].sum()
    )

    repeat_rate = (
        repeat_contacts / len(completed)
        if len(completed)
        else 0
    )

    frontline = completed[
        completed["assigned_team"]
        != "Escalations & Warranty"
    ].copy()

    leaderboard = (
        frontline
        .groupby("agent_id")
        .agg(
            tickets_closed=("ticket_id", "count")
        )
        .reset_index()
    )

    agent_names = (
        agents[
            ["agent_id", "name"]
        ]
        .drop_duplicates("agent_id")
    )

    leaderboard = leaderboard.merge(
        agent_names,
        on="agent_id",
        how="left"
    )

    leaderboard["name"] = (
        leaderboard["name"]
        .fillna(leaderboard["agent_id"])
    )

    leaderboard = leaderboard[
        [
            "agent_id",
            "name",
            "tickets_closed"
        ]
    ].sort_values(
        "tickets_closed",
        ascending=False
    )

    leaderboard.insert(
        0,
        "rank",
        range(1, len(leaderboard) + 1)
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

    team_summary = (
        frontline
        .groupby("assigned_team")
        .agg(
            tickets_closed=("ticket_id", "count"),
            repeat_contacts=("repeat_contact", "sum")
        )
        .reset_index()
    )

    team_summary["repeat_rate"] = (
        team_summary["repeat_contacts"]
        / team_summary["tickets_closed"]
    )

    return {
        "week_start": week_start,
        "week_end": week_end - pd.Timedelta(days=1),
        "tickets": len(weekly),
        "completed": len(completed),
        "sla_breaches": sla_breaches,
        "sla_rate": sla_rate,
        "repeat_contacts": repeat_contacts,
        "repeat_rate": repeat_rate,
        "leaderboard": leaderboard,
        "category_summary": category_summary,
        "team_summary": team_summary,
    }