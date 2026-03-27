import threading
import time
from datetime import datetime, timezone

from email.utils import parsedate_to_datetime
from flask import Flask, jsonify, render_template

from config import config
from store import init_db, has_email, store_email, get_recent_emails, cleanup_old
from mail_fetcher import fetch_recent_emails
from summarizer import summarize_email

app = Flask(__name__)

# Shared state for error reporting
poll_status = {"last_check": None, "error": None}


def time_ago(date_str):
    """Convert email date string to a human-readable 'Xm ago' string."""
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "now"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except Exception:
        return ""


def poll_loop():
    """Background thread: fetch emails, summarize new ones, store results."""
    while True:
        try:
            cleanup_old(24)
            raw_emails = fetch_recent_emails(config["MAX_EMAILS"])

            for em in raw_emails:
                if not has_email(em["message_id"]):
                    print(f"[PiMail] Summarizing: {em['subject'][:50]}")
                    result = summarize_email(
                        em["sender"],
                        em["subject"],
                        em["body_text"],
                        model=config["CLAUDE_MODEL"],
                    )
                    store_email(
                        em["message_id"],
                        em["sender"],
                        em["subject"],
                        em["date"],
                        result["summary"],
                        result["verification_code"],
                    )

            poll_status["last_check"] = datetime.now(timezone.utc).isoformat()
            poll_status["error"] = None

        except Exception as e:
            print(f"[PiMail] Poll error: {e}")
            poll_status["error"] = str(e)

        time.sleep(config["POLL_INTERVAL_SEC"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/emails")
def api_emails():
    emails = get_recent_emails(config["MAX_EMAILS"])
    result = []
    for em in emails:
        result.append({
            "sender": em["sender"],
            "subject": em["subject"],
            "time_ago": time_ago(em["date"]),
            "summary": em["summary"],
            "verification_code": em["verification_code"] or "",
        })
    return jsonify({
        "emails": result,
        "last_check": poll_status["last_check"],
        "error": poll_status["error"],
    })


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
