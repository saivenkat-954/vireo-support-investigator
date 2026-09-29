import pandas as pd

tickets = pd.read_csv("data/tickets_canonical.csv")

# Convert timestamps
tickets["created_at"] = pd.to_datetime(tickets["created_at"])
tickets["first_response_at"] = pd.to_datetime(
    tickets["first_response_at"]
)
tickets["resolved_at"] = pd.to_datetime(
    tickets["resolved_at"]
)

# Resolution time:
# created -> resolved
tickets["resolution_hours"] = (
    tickets["resolved_at"] - tickets["created_at"]
).dt.total_seconds() / 3600

# Only completed tickets with valid resolution timestamps
completed = tickets[
    tickets["status"].isin(["resolved", "closed"])
    & tickets["resolved_at"].notna()
].copy()

print("=== RESOLUTION OVERVIEW ===")

print("\nCompleted tickets:")
print(len(completed))

print("\nMedian resolution hours:")
print(
    round(completed["resolution_hours"].median(), 2)
)

print("\nAverage resolution hours:")
print(
    round(completed["resolution_hours"].mean(), 2)
)

print("\n90th percentile:")
print(
    round(completed["resolution_hours"].quantile(0.90), 2)
)

print("\n95th percentile:")
print(
    round(completed["resolution_hours"].quantile(0.95), 2)
)


print("\n=== RESOLUTION BY TEAM ===")

team_resolution = (
    completed
    .groupby("assigned_team")
    .agg(
        tickets=("ticket_id", "count"),
        median_hours=("resolution_hours", "median"),
        avg_hours=("resolution_hours", "mean"),
        p90_hours=("resolution_hours", lambda x: x.quantile(0.90))
    )
)

team_resolution = team_resolution.round(2)

print(
    team_resolution
    .sort_values("median_hours", ascending=False)
)


print("\n=== RESOLUTION BY CATEGORY ===")

category_resolution = (
    completed
    .groupby("category")
    .agg(
        tickets=("ticket_id", "count"),
        median_hours=("resolution_hours", "median"),
        avg_hours=("resolution_hours", "mean"),
        p90_hours=("resolution_hours", lambda x: x.quantile(0.90))
    )
)

category_resolution = category_resolution.round(2)

print(
    category_resolution
    .sort_values("median_hours", ascending=False)
)