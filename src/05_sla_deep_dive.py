import pandas as pd

tickets = pd.read_csv("data/tickets_canonical.csv")

tickets["created_at"] = pd.to_datetime(tickets["created_at"])
tickets["first_response_at"] = pd.to_datetime(
    tickets["first_response_at"]
)

tickets["response_minutes"] = (
    tickets["first_response_at"] - tickets["created_at"]
).dt.total_seconds() / 60

sla_targets = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480
}

tickets["sla_target_minutes"] = tickets["channel"].map(
    sla_targets
)

tickets["sla_breach"] = (
    tickets["response_minutes"]
    > tickets["sla_target_minutes"]
)

print("=== RESPONSE TIME PERCENTILES ===")

for channel in tickets["channel"].unique():

    data = tickets.loc[
        tickets["channel"] == channel,
        "response_minutes"
    ]

    print(f"\n{channel.upper()}")

    print("Median:", round(data.median(), 2), "minutes")
    print("75th percentile:", round(data.quantile(0.75), 2), "minutes")
    print("90th percentile:", round(data.quantile(0.90), 2), "minutes")
    print("95th percentile:", round(data.quantile(0.95), 2), "minutes")
    print("Maximum:", round(data.max(), 2), "minutes")


print("\n=== BREACHES BY TEAM ===")

team_breaches = (
    tickets
    .groupby("assigned_team")
    .agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breach", "sum"),
        breach_rate=("sla_breach", "mean")
    )
)

team_breaches["breach_rate"] = (
    team_breaches["breach_rate"] * 100
).round(2)

print(
    team_breaches
    .sort_values("breach_rate", ascending=False)
)


print("\n=== BREACHES BY PRIORITY ===")

priority_breaches = (
    tickets
    .groupby("priority")
    .agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breach", "sum"),
        breach_rate=("sla_breach", "mean")
    )
)

priority_breaches["breach_rate"] = (
    priority_breaches["breach_rate"] * 100
).round(2)

print(
    priority_breaches
    .sort_values("breach_rate", ascending=False)
)