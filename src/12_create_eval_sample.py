import pandas as pd

tickets = pd.read_csv("data/tickets_canonical.csv")

# Recreate our baseline signal
tickets["text"] = (
    tickets["customer_message"].fillna("")
    + " "
    + tickets["agent_notes"].fillna("")
).str.lower()

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

tickets["baseline_signal"] = tickets["text"].str.contains(
    pattern,
    regex=True,
    na=False
)

# Take a balanced sample:
# 50 flagged + 50 not flagged
flagged = tickets[tickets["baseline_signal"]].sample(
    50,
    random_state=42
)

not_flagged = tickets[
    ~tickets["baseline_signal"]
].sample(
    50,
    random_state=42
)

evaluation = pd.concat(
    [flagged, not_flagged]
).sample(
    frac=1,
    random_state=42
)

evaluation[
    [
        "ticket_id",
        "category",
        "channel",
        "customer_message",
        "baseline_signal"
    ]
].to_csv(
    "data/evaluation_sample.csv",
    index=False
)

print("Evaluation sample created.")
print("Rows:", len(evaluation))
print("\nBaseline signal distribution:")
print(evaluation["baseline_signal"].value_counts())