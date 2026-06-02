import requests
import json

def ollama_classify(text):

    prompt = f"""
Classify this hotel guest message.

Valid intents:

booking
cancellation
faq
complaint
wakeup

IMPORTANT:
Reply with EXACTLY one word.
No explanation.
No punctuation.
No JSON.

Examples:

book room tomorrow
booking

cancel my reservation
cancellation

wifi password
faq

room is dirty
complaint

wake me at 6am
wakeup

Message:
{text}
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5-coder:7b",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )

        raw = response.json()["response"].strip()

        print("OLLAMA RAW:", raw)

        intent = raw.lower().strip()

        VALID_INTENTS = {
            "booking",
            "cancellation",
            "faq",
            "complaint",
            "wakeup"
        }

        if intent not in VALID_INTENTS:
            return ("faq", 0.0)

        return (intent, 0.90)

    except Exception as e:

        print("OLLAMA ERROR:", e)

        return "faq", 0.0