import pandas as pd

tickets = pd.read_csv("data/tickets_canonical.csv")

print("=== SAMPLE CUSTOMER MESSAGES ===")

sample = tickets[
    ["ticket_id", "category", "channel", "customer_message"]
].sample(20, random_state=42)

for _, row in sample.iterrows():
    print("\n--------------------------------")
    print("Ticket:", row["ticket_id"])
    print("Category:", row["category"])
    print("Channel:", row["channel"])
    print("Message:")
    print(row["customer_message"])


print("\n=== SAMPLE AGENT NOTES ===")

sample_notes = tickets[
    ["ticket_id", "category", "agent_notes"]
].sample(20, random_state=42)

for _, row in sample_notes.iterrows():
    print("\n--------------------------------")
    print("Ticket:", row["ticket_id"])
    print("Category:", row["category"])
    print("Agent notes:")
    print(row["agent_notes"])