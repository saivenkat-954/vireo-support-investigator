import pandas as pd

tickets = pd.read_csv("data/tickets_canonical.csv")

tickets["created_at"] = pd.to_datetime(tickets["created_at"])
tickets["resolved_at"] = pd.to_datetime(tickets["resolved_at"])

# Keep tickets that have been resolved/closed
completed = tickets[
    tickets["status"].isin(["resolved", "closed"])
].copy()

# Sort by customer and issue
completed = completed.sort_values(
    ["customer_id", "category", "created_at"]
)

# Look at previous ticket for the same customer + category
completed["previous_resolved_at"] = (
    completed
    .groupby(["customer_id", "category"])["resolved_at"]
    .shift(1)
)

# Days since previous resolution
completed["days_since_previous"] = (
    completed["created_at"]
    - completed["previous_resolved_at"]
).dt.total_seconds() / (60 * 60 * 24)

# Repeat contact according to policy:
# same customer + same issue within 30 days
completed["repeat_contact"] = (
    completed["days_since_previous"].between(
        0, 30, inclusive="both"
    )
)

print("=== REPEAT CONTACT ANALYSIS ===")

print("\nCompleted tickets:")
print(len(completed))

print("\nRepeat contacts:")
print(completed["repeat_contact"].sum())

print("\nRepeat contact rate:")
print(
    round(
        completed["repeat_contact"].mean() * 100,
        2
    ),
    "%"
)

print("\n=== REPEAT CONTACTS BY CHANNEL ===")

by_channel = (
    completed
    .groupby("channel")
    .agg(
        tickets=("ticket_id", "count"),
        repeat_contacts=("repeat_contact", "sum"),
        repeat_rate=("repeat_contact", "mean")
    )
)

by_channel["repeat_rate"] = (
    by_channel["repeat_rate"] * 100
).round(2)

print(
    by_channel
    .sort_values("repeat_rate", ascending=False)
)

print("\n=== REPEAT CONTACTS BY CATEGORY ===")

by_category = (
    completed
    .groupby("category")
    .agg(
        tickets=("ticket_id", "count"),
        repeat_contacts=("repeat_contact", "sum"),
        repeat_rate=("repeat_contact", "mean")
    )
)

by_category["repeat_rate"] = (
    by_category["repeat_rate"] * 100
).round(2)

print(
    by_category
    .sort_values("repeat_rate", ascending=False)
)