import pandas as pd

tickets = pd.read_csv("data/tickets_canonical.csv")

tickets["created_at"] = pd.to_datetime(tickets["created_at"])
tickets["resolved_at"] = pd.to_datetime(tickets["resolved_at"])

tickets["resolution_hours"] = (
    tickets["resolved_at"] - tickets["created_at"]
).dt.total_seconds() / 3600

completed = tickets[
    tickets["status"].isin(["resolved", "closed"])
    & tickets["resolved_at"].notna()
].copy()

# Sort chronologically within customer + category
completed = completed.sort_values(
    ["customer_id", "category", "created_at"]
)

# Previous resolution for same customer + category
completed["previous_resolved_at"] = (
    completed
    .groupby(["customer_id", "category"])["resolved_at"]
    .shift(1)
)

completed["days_since_previous"] = (
    completed["created_at"]
    - completed["previous_resolved_at"]
).dt.total_seconds() / (60 * 60 * 24)

completed["repeat_contact"] = (
    completed["days_since_previous"].between(
        0, 30, inclusive="both"
    )
)

print("=== REPEAT VS RESOLUTION ===")

print("\nNON-REPEAT CONTACTS")

non_repeat = completed[
    ~completed["repeat_contact"]
]

print("Tickets:", len(non_repeat))
print(
    "Median resolution:",
    round(non_repeat["resolution_hours"].median(), 2),
    "hours"
)
print(
    "Average resolution:",
    round(non_repeat["resolution_hours"].mean(), 2),
    "hours"
)
print(
    "P90 resolution:",
    round(non_repeat["resolution_hours"].quantile(0.90), 2),
    "hours"
)


print("\nREPEAT CONTACTS")

repeat = completed[
    completed["repeat_contact"]
]

print("Tickets:", len(repeat))
print(
    "Median resolution:",
    round(repeat["resolution_hours"].median(), 2),
    "hours"
)
print(
    "Average resolution:",
    round(repeat["resolution_hours"].mean(), 2),
    "hours"
)
print(
    "P90 resolution:",
    round(repeat["resolution_hours"].quantile(0.90), 2),
    "hours"
)