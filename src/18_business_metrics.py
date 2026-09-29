import pandas as pd

# --------------------------------------------------
# Load canonical tickets
# --------------------------------------------------

tickets = pd.read_csv("data/tickets_canonical.csv")

tickets["created_at"] = pd.to_datetime(
    tickets["created_at"],
    errors="coerce"
)

tickets["first_response_at"] = pd.to_datetime(
    tickets["first_response_at"],
    errors="coerce"
)

tickets["resolved_at"] = pd.to_datetime(
    tickets["resolved_at"],
    errors="coerce"
)

print("\n===== VIREO BUSINESS METRICS =====")

# --------------------------------------------------
# POLICY-EFFECTIVE PERIOD
# Policy v3.2 effective: 1 Apr 2025
# --------------------------------------------------

policy_start = pd.Timestamp("2025-04-01")

policy_tickets = tickets[
    tickets["created_at"] >= policy_start
].copy()

print(f"\nPolicy-period tickets: {len(policy_tickets):,}")

# --------------------------------------------------
# SLA ANALYSIS
# --------------------------------------------------

sla_targets = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480
}

policy_tickets["response_minutes"] = (
    policy_tickets["first_response_at"]
    - policy_tickets["created_at"]
).dt.total_seconds() / 60

policy_tickets["sla_target_minutes"] = (
    policy_tickets["channel"].map(sla_targets)
)

policy_tickets["sla_breach"] = (
    policy_tickets["response_minutes"]
    > policy_tickets["sla_target_minutes"]
)

responded = policy_tickets[
    policy_tickets["first_response_at"].notna()
]

breaches = responded["sla_breach"].sum()

sla_rate = (
    breaches / len(responded)
    if len(responded) > 0
    else 0
)

sla_credit_exposure = breaches * 350

print("\n===== SLA =====")
print(f"Responded tickets       : {len(responded):,}")
print(f"SLA breaches            : {breaches:,}")
print(f"SLA breach rate         : {sla_rate:.2%}")
print(f"Potential SLA credits   : ₹{sla_credit_exposure:,.0f}")

# --------------------------------------------------
# POLICY REPEAT-CONTACT APPROXIMATION
#
# Policy definition:
# same customer + same issue within 30 days
#
# Dataset has no issue_id, so category is used
# as the issue proxy.
# --------------------------------------------------

completed = tickets[
    tickets["resolved_at"].notna()
    & (tickets["created_at"] >= policy_start)
].copy()

completed = completed.sort_values(
    ["customer_id", "category", "resolved_at"]
)

completed["previous_resolution"] = (
    completed
    .groupby(["customer_id", "category"])["resolved_at"]
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
    if len(completed) > 0
    else 0
)

print("\n===== REPEAT CONTACT =====")
print(f"Completed tickets       : {len(completed):,}")
print(f"Repeat contacts         : {repeat_count:,}")
print(f"Repeat-contact rate     : {repeat_rate:.2%}")

# --------------------------------------------------
# REPEAT CONTACT COST
# --------------------------------------------------

contact_costs = {
    "chat": 210,
    "email": 260,
    "voice": 520,
    "social": 240
}

repeat_contacts["contact_cost"] = (
    repeat_contacts["channel"]
    .map(contact_costs)
)

repeat_cost = repeat_contacts["contact_cost"].sum()

avg_repeat_cost = (
    repeat_cost / repeat_count
    if repeat_count > 0
    else 0
)

print("\n===== REPEAT CONTACT COST =====")
print(f"Estimated repeat cost   : ₹{repeat_cost:,.0f}")
print(f"Average cost/repeat     : ₹{avg_repeat_cost:,.2f}")

# --------------------------------------------------
# CHANNEL BREAKDOWN
# --------------------------------------------------

print("\n===== REPEAT COST BY CHANNEL =====")

channel_cost = (
    repeat_contacts
    .groupby("channel")
    .agg(
        repeat_contacts=("ticket_id", "count"),
        estimated_cost=("contact_cost", "sum")
    )
    .sort_values("estimated_cost", ascending=False)
)

print(channel_cost)

# --------------------------------------------------
# CATEGORY BREAKDOWN
# --------------------------------------------------

print("\n===== REPEAT RATE BY CATEGORY =====")

category_summary = (
    completed
    .groupby("category")
    .agg(
        completed=("ticket_id", "count"),
        repeat_contacts=("repeat_contact", "sum")
    )
)

category_summary["repeat_rate"] = (
    category_summary["repeat_contacts"]
    / category_summary["completed"]
)

print(
    category_summary
    .sort_values("repeat_rate", ascending=False)
)

# --------------------------------------------------
# POTENTIAL 10% IMPROVEMENT SCENARIO
# --------------------------------------------------

target_reduction = 0.10

avoided_repeats = repeat_count * target_reduction

estimated_savings = repeat_cost * target_reduction

print("\n===== 10% IMPROVEMENT SCENARIO =====")
print(
    f"Repeat contacts avoided : "
    f"{avoided_repeats:,.0f}"
)

print(
    f"Estimated cost avoided  : "
    f"₹{estimated_savings:,.0f}"
)

print("\n===== COMPLETE =====")