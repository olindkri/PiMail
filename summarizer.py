import subprocess
import json

SUMMARY_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "1-2 sentence summary, under 30 words"
        },
        "verification_code": {
            "type": "string",
            "description": "Verification/OTP/login/security code if present, empty string if none"
        }
    },
    "required": ["summary", "verification_code"]
})

PROMPT = (
    "Summarize the following email in 1-2 short sentences (under 30 words total). "
    "If the email contains any verification code, OTP, login code, confirmation code, "
    "or security code, you MUST extract it exactly and put it in verification_code. "
    "If there is no code, set verification_code to empty string. "
    "Do not include greetings or sign-offs in the summary."
)


def summarize_email(sender, subject, body_text, model="haiku"):
    """Call Claude CLI to summarize an email. Returns {summary, verification_code}."""
    email_text = f"From: {sender}\nSubject: {subject}\n\n{body_text[:2000]}"

    try:
        result = subprocess.run(
            [
                "claude",
                "--model", model,
                "-p",
                "--output-format", "json",
                "--json-schema", SUMMARY_SCHEMA,
                PROMPT,
            ],
            input=email_text,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"[PiMail] Claude CLI error: {result.stderr}")
            return {"summary": subject[:80], "verification_code": ""}

        envelope = json.loads(result.stdout)
        # The structured output is in the "result" field of the JSON envelope
        structured = envelope.get("result", envelope)
        if isinstance(structured, str):
            # Try parsing if it's a JSON string
            try:
                structured = json.loads(structured)
            except json.JSONDecodeError:
                return {"summary": structured[:80], "verification_code": ""}

        return {
            "summary": structured.get("summary", subject[:80]),
            "verification_code": structured.get("verification_code", ""),
        }

    except subprocess.TimeoutExpired:
        print("[PiMail] Claude CLI timed out")
        return {"summary": subject[:80], "verification_code": ""}
    except Exception as e:
        print(f"[PiMail] Summarizer error: {e}")
        return {"summary": subject[:80], "verification_code": ""}
