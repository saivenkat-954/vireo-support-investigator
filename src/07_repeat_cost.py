import pandas as pd

tickets = pd.read_csv("data/tickets_canonical.csv")

tickets["created_at"] = pd.to_datetime(tickets["created_at"])
tickets["resolved_at"] = pd.to_datetime(tickets["resolved_at"])

completed = tickets[
    tickets["status"].isin(["resolved", "closed"])
].copy()

completed = completed.sort_values(
    ["customer_id", "category", "created_at"]
)

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

# Policy contact costs
contact_costs = {
    "chat": 210,
    "email": 260,
    "voice": 520,
    "social": 240
}

completed["contact_cost"] = (
    completed["channel"].map(contact_costs)
)

repeat = completed[
    completed["repeat_contact"]
].copy()

print("=== REPEAT CONTACT COST ===")

print("\nRepeat contacts:")
print(len(repeat))

print("\nCost by channel:")

cost_by_channel = (
    repeat
    .groupby("channel")
    .agg(
        repeat_contacts=("ticket_id", "count"),
        cost_per_contact=("contact_cost", "first"),
        estimated_cost=("contact_cost", "sum")
    )
)

print(cost_by_channel)

print("\nTotal repeat-contact cost:")

total_cost = repeat["contact_cost"].sum()

print(f"₹{total_cost:,.0f}")

print("\nAverage cost per repeat contact:")

print(
    f"₹{repeat['contact_cost'].mean():,.2f}"
)