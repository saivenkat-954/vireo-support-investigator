import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)

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

ticket = """
Writing again because the issue is back.
I ordered the Orbit smart speaker and got something else,
I want a replacement.
"""

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=PROMPT + "\n\nTICKET:\n" + ticket,
    config={
        "response_mime_type": "application/json"
    }
)

result = json.loads(response.text)

print("\n===== GEMINI RESULT =====")
print(json.dumps(result, indent=2, ensure_ascii=False))