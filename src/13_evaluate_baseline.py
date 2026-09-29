import pandas as pd

df = pd.read_csv("data/evaluation_sample.csv")

# Make sure manual labels exist
if "manual_signal" not in df.columns:
    raise ValueError(
        "manual_signal column is missing. Add 0/1 labels to evaluation_sample.csv first."
    )

# Remove rows without a manual label
df = df.dropna(subset=["manual_signal"]).copy()

df["manual_signal"] = df["manual_signal"].astype(int)
df["baseline_signal"] = df["baseline_signal"].astype(int)

# Confusion matrix values
tp = ((df["manual_signal"] == 1) & (df["baseline_signal"] == 1)).sum()
fp = ((df["manual_signal"] == 0) & (df["baseline_signal"] == 1)).sum()
fn = ((df["manual_signal"] == 1) & (df["baseline_signal"] == 0)).sum()
tn = ((df["manual_signal"] == 0) & (df["baseline_signal"] == 0)).sum()

# Metrics
precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0
f1 = (
    2 * precision * recall / (precision + recall)
    if (precision + recall)
    else 0
)
accuracy = (tp + tn) / len(df)

print("\n===== BASELINE EVALUATION =====")
print(f"Evaluation rows : {len(df)}")

print("\nConfusion Matrix")
print(f"True Positives  : {tp}")
print(f"False Positives : {fp}")
print(f"False Negatives : {fn}")
print(f"True Negatives  : {tn}")

print("\nMetrics")
print(f"Accuracy  : {accuracy:.2%}")
print(f"Precision : {precision:.2%}")
print(f"Recall    : {recall:.2%}")
print(f"F1 Score  : {f1:.2%}")