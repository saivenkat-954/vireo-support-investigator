import pandas as pd

tickets = pd.read_csv("data/tickets.csv")

print("Shape:", tickets.shape)

print("\nColumns:")
print(tickets.columns.tolist())

print("\nMissing values:")
print(tickets.isna().sum())

print("\nDuplicate ticket IDs:")
print(tickets["ticket_id"].duplicated().sum())
print("\nChannels:")
print(tickets["channel"].value_counts())

print("\nCategories:")
print(tickets["category"].value_counts())

print("\nStatus:")
print(tickets["status"].value_counts())

duplicates = tickets[tickets["ticket_id"].duplicated(keep=False)]

print("\nDuplicate records:")
print(
    duplicates[
        [
            "ticket_id",
            "created_at",
            "resolved_at",
            "status",
            "source_system",
            "customer_id",
            "product_sku",
            "agent_id"
        ]
    ].sort_values("ticket_id").head(30)
)

ticket_id = "TK-240001"

print("\nDetailed duplicate:")
print(
    tickets[tickets["ticket_id"] == ticket_id].T
)