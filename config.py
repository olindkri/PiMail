import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "IMAP_SERVER": os.getenv("IMAP_SERVER", "imap.gmail.com"),
    "IMAP_PORT": int(os.getenv("IMAP_PORT", "993")),
    "IMAP_USER": os.getenv("IMAP_USER", ""),
    "IMAP_PASSWORD": os.getenv("IMAP_PASSWORD", ""),
    "IMAP_FOLDER": os.getenv("IMAP_FOLDER", "INBOX"),
    "POLL_INTERVAL_SEC": int(os.getenv("POLL_INTERVAL_SEC", "60")),
    "MAX_EMAILS": int(os.getenv("MAX_EMAILS", "8")),
    "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL", "haiku"),
}
