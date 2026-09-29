import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

df = pd.read_csv("data/gemini_evaluation_results.csv")

# Convert to numeric
df["manual_signal"] = pd.to_numeric(df["manual_signal"], errors="coerce")
df["gemini_signal"] = pd.to_numeric(df["gemini_signal"], errors="coerce")

# Keep only successfully evaluated rows
eval_df = df.dropna(subset=["manual_signal", "gemini_signal"]).copy()

y_true = eval_df["manual_signal"].astype(int)
y_pred = eval_df["gemini_signal"].astype(int)

print("\n===== GEMINI MODEL EVALUATION =====")
print(f"Evaluated tickets : {len(eval_df)}")

print(f"Accuracy  : {accuracy_score(y_true, y_pred):.2%}")
print(f"Precision : {precision_score(y_true, y_pred):.2%}")
print(f"Recall    : {recall_score(y_true, y_pred):.2%}")
print(f"F1 Score  : {f1_score(y_true, y_pred):.2%}")

tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

print("\nConfusion Matrix")
print(f"TP: {tp}")
print(f"FP: {fp}")
print(f"FN: {fn}")
print(f"TN: {tn}")

print("\n===== COMPARISON =====")
print("Baseline F1 : 94.95%")
print(f"Gemini F1   : {f1_score(y_true, y_pred):.2%}")

print("\n===== CONFIDENCE =====")
if "confidence" in eval_df.columns:
    print(eval_df["confidence"].value_counts(dropna=False))

print("\n===== MODEL AGREEMENT =====")
eval_df["agreement"] = y_true == y_pred
print(f"Agreement: {eval_df['agreement'].mean():.2%}")

# Save disagreements for inspection
disagreements = eval_df[eval_df["agreement"] == False]

disagreements.to_csv(
    "data/gemini_disagreements.csv",
    index=False
)

print(f"\nDisagreements saved: {len(disagreements)}")
print("Saved to: data/gemini_disagreements.csv")