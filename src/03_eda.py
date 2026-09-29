import pandas as pd

# Load canonical ticket data
tickets = pd.read_csv("data/tickets_canonical.csv")

print("Canonical dataset:", tickets.shape)

# -----------------------------
# 1. Ticket volume by channel
# -----------------------------

print("\n=== CHANNEL VOLUME ===")

channel_counts = tickets["channel"].value_counts()

print(channel_counts)

print("\nChannel percentages:")

channel_percent = (
    tickets["channel"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

print(channel_percent)


# -----------------------------
# 2. Category volume
# -----------------------------

print("\n=== CATEGORY VOLUME ===")

category_counts = tickets["category"].value_counts()

print(category_counts)


# -----------------------------
# 3. Team volume
# -----------------------------

print("\n=== TEAM VOLUME ===")

team_counts = tickets["assigned_team"].value_counts()

print(team_counts)


# -----------------------------
# 4. Product volume
# -----------------------------

print("\n=== PRODUCT VOLUME ===")

product_counts = tickets["product_sku"].value_counts()

print(product_counts.head(15))


# -----------------------------
# 5. Priority
# -----------------------------

print("\n=== PRIORITY ===")

print(tickets["priority"].value_counts())


# -----------------------------
# 6. Status
# -----------------------------

print("\n=== STATUS ===")

print(tickets["status"].value_counts())