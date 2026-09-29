import pandas as pd

# Load raw data
tickets = pd.read_csv("data/tickets.csv")

print("Raw rows:", len(tickets))
print("Raw unique ticket IDs:", tickets["ticket_id"].nunique())

# Identify migration duplicates
duplicate_mask = tickets["ticket_id"].duplicated(keep=False)

duplicates = tickets[duplicate_mask]

print("\nDuplicate rows:", len(duplicates))
print("Duplicate ticket IDs:", duplicates["ticket_id"].nunique())

# Count source combinations
source_check = (
    duplicates
    .groupby("ticket_id")["source_system"]
    .agg(lambda x: sorted(x.tolist()))
    .value_counts()
)

print("\nDuplicate source combinations:")
print(source_check)

# Keep helpdesk record when a ticket exists in both systems
tickets_sorted = tickets.copy()

tickets_sorted["source_priority"] = tickets_sorted["source_system"].map({
    "helpdesk": 1,
    "legacy_fd": 2
})

canonical = (
    tickets_sorted
    .sort_values(["ticket_id", "source_priority"])
    .drop_duplicates("ticket_id", keep="first")
    .drop(columns="source_priority")
)

print("\nCanonical rows:", len(canonical))
print("Canonical unique ticket IDs:", canonical["ticket_id"].nunique())

# Save cleaned dataset
canonical.to_csv("data/tickets_canonical.csv", index=False)

print("\nSaved: data/tickets_canonical.csv")