import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)

INPUT_FILE = "data/evaluation_sample.csv"
OUTPUT_FILE = "data/gemini_evaluation_results.csv"

MODEL = "gemini-3.5-flash-lite"

PROMPT = """
You are a customer-support quality investigator for Vireo Audio.

Analyze ONE support ticket and determine whether there is evidence that
the customer has already attempted to get help or is experiencing a
repeated/unresolved support issue.

IMPORTANT:
- Do not assume "again", "still", or "nothing changed" automatically
  means previous support contact.
- Distinguish troubleshooting attempts from previous contact with Vireo.
- Use only evidence present in the ticket.
- Do not invent previous tickets, dates, actions, or customer history.
- If evidence is ambiguous, say so.
- Be concise and factual.

Return ONLY valid JSON:

{
  "repeat_contact_signal": true,
  "confidence": "high",
  "evidence": [
    "short quote or specific evidence from the ticket"
  ],
  "reason": "brief explanation",
  "issue_theme": "short description of the underlying issue",
  "recommended_action": "practical support action"
}

Definitions:

repeat_contact_signal:
- true = clear evidence of previous contact, previous resolution attempt,
  repeated complaint, or unresolved prior support interaction.
- false = no clear evidence of previous Vireo support contact.

confidence:
- high = explicit evidence
- medium = strong but indirect evidence
- low = ambiguous evidence
"""


# --------------------------------------------------
# Load input
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

# --------------------------------------------------
# Load previous results if they exist
# --------------------------------------------------

if os.path.exists(OUTPUT_FILE):
    results_df = pd.read_csv(OUTPUT_FILE)

    completed_ids = set(
        results_df.loc[
            results_df["gemini_signal"].notna(),
            "ticket_id"
        ]
    )

    print(f"Existing successful results: {len(completed_ids)}")

else:
    results_df = pd.DataFrame(columns=[
        "ticket_id",
        "manual_signal",
        "baseline_signal",
        "gemini_signal",
        "gemini_confidence",
        "evidence",
        "reason",
        "issue_theme",
        "recommended_action"
    ])

    completed_ids = set()


# --------------------------------------------------
# Process only missing tickets
# --------------------------------------------------

remaining = df[~df["ticket_id"].isin(completed_ids)].copy()

print(f"Total evaluation tickets : {len(df)}")
print(f"Already completed        : {len(completed_ids)}")
print(f"Remaining                : {len(remaining)}")
print()

for _, row in remaining.iterrows():

    ticket_id = row["ticket_id"]
    ticket = str(row["customer_message"])

    while True:

        try:

            response = client.models.generate_content(
                model=MODEL,
                contents=PROMPT + "\n\nTICKET:\n" + ticket,
                config={
                    "response_mime_type": "application/json"
                }
            )

            result = json.loads(response.text)

            new_row = {
                "ticket_id": ticket_id,
                "manual_signal": int(row["manual_signal"]),
                "baseline_signal": bool(row["baseline_signal"]),
                "gemini_signal": bool(result["repeat_contact_signal"]),
                "gemini_confidence": result.get("confidence", ""),
                "evidence": " | ".join(result.get("evidence", [])),
                "reason": result.get("reason", ""),
                "issue_theme": result.get("issue_theme", ""),
                "recommended_action": result.get(
                    "recommended_action", ""
                )
            }

            results_df = pd.concat(
                [results_df, pd.DataFrame([new_row])],
                ignore_index=True
            )

            # Save immediately
            results_df.to_csv(
                OUTPUT_FILE,
                index=False
            )

            print(
                f"{ticket_id} ✓ "
                f"({len(results_df)}/{len(df)})"
            )

            # IMPORTANT:
            # Stay safely below the 15 requests/minute limit.
            time.sleep(5)

            break

        except Exception as e:

            error_text = str(e)

            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:

                print(
                    f"{ticket_id} → quota limit reached."
                )

                print(
                    "Waiting 50 seconds before retrying..."
                )

                time.sleep(50)

            else:

                print(
                    f"{ticket_id} → ERROR: {error_text}"
                )

                break


# --------------------------------------------------
# Final status
# --------------------------------------------------

results_df = pd.read_csv(OUTPUT_FILE)

successful = results_df["gemini_signal"].notna().sum()

print()
print("===== GEMINI EVALUATION STATUS =====")
print(f"Total tickets      : {len(df)}")
print(f"Successful results : {successful}")
print(f"Remaining          : {len(df) - successful}")
print(f"Saved to           : {OUTPUT_FILE}")