import pandas as pd
import re

tickets = pd.read_csv("data/tickets_canonical.csv")

# Combine customer message and agent notes
tickets["text"] = (
    tickets["customer_message"].fillna("")
    + " "
    + tickets["agent_notes"].fillna("")
).str.lower()

# Simple baseline patterns
patterns = [
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
    r"\bwaiting for your reply\b"
]

pattern = "|".join(patterns)

tickets["repeat_signal"] = tickets["text"].str.contains(
    pattern,
    regex=True,
    na=False
)

print("=== REPEAT SIGNAL BASELINE ===")

print("\nTickets with signal:")
print(tickets["repeat_signal"].sum())

print("\nSignal rate:")
print(
    round(
        tickets["repeat_signal"].mean() * 100,
        2
    ),
    "%"
)

print("\n=== SIGNAL BY CATEGORY ===")

category_signal = (
    tickets
    .groupby("category")
    .agg(
        tickets=("ticket_id", "count"),
        signals=("repeat_signal", "sum"),
        signal_rate=("repeat_signal", "mean")
    )
)

category_signal["signal_rate"] = (
    category_signal["signal_rate"] * 100
).round(2)

print(
    category_signal
    .sort_values("signal_rate", ascending=False)
)

print("\n=== SIGNAL BY CHANNEL ===")

channel_signal = (
    tickets
    .groupby("channel")
    .agg(
        tickets=("ticket_id", "count"),
        signals=("repeat_signal", "sum"),
        signal_rate=("repeat_signal", "mean")
    )
)

channel_signal["signal_rate"] = (
    channel_signal["signal_rate"] * 100
).round(2)

print(
    channel_signal
    .sort_values("signal_rate", ascending=False)
)

print("\n=== EXAMPLES ===")

examples = tickets[
    tickets["repeat_signal"]
][
    ["ticket_id", "category", "channel", "customer_message"]
].head(20)

for _, row in examples.iterrows():
    print("\n-------------------------")
    print(row["ticket_id"])
    print(row["category"])
    print(row["channel"])
    print(row["customer_message"])