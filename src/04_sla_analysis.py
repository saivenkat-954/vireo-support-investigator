import pandas as pd

# Load canonical data
tickets = pd.read_csv("data/tickets_canonical.csv")

# Convert timestamps
tickets["created_at"] = pd.to_datetime(tickets["created_at"])
tickets["first_response_at"] = pd.to_datetime(tickets["first_response_at"])

# Calculate response time in minutes
tickets["response_minutes"] = (
    tickets["first_response_at"] - tickets["created_at"]
).dt.total_seconds() / 60

# SLA targets from Support Policy v3.2
sla_targets = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480
}

tickets["sla_target_minutes"] = tickets["channel"].map(sla_targets)

# Determine SLA breach
tickets["sla_breach"] = (
    tickets["response_minutes"] > tickets["sla_target_minutes"]
)

print("=== SLA OVERVIEW ===")

print("\nTotal tickets:")
print(len(tickets))

print("\nSLA breaches:")
print(tickets["sla_breach"].sum())

print("\nSLA breach rate:")
print(
    round(tickets["sla_breach"].mean() * 100, 2),
    "%"
)

print("\n=== SLA BY CHANNEL ===")

sla_by_channel = (
    tickets
    .groupby("channel")
    .agg(
        tickets=("ticket_id", "count"),
        avg_response_minutes=("response_minutes", "mean"),
        breaches=("sla_breach", "sum"),
        breach_rate=("sla_breach", "mean")
    )
)

sla_by_channel["breach_rate"] = (
    sla_by_channel["breach_rate"] * 100
).round(2)

sla_by_channel["avg_response_minutes"] = (
    sla_by_channel["avg_response_minutes"]
).round(2)

print(sla_by_channel.sort_values("breach_rate", ascending=False))