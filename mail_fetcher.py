import imaplib
import email
import email.header
import re
from config import config


def _decode_header(raw):
    if raw is None:
        return ""
    parts = email.header.decode_header(raw)
    decoded = []
    for data, charset in parts:
        if isinstance(data, bytes):
            decoded.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(data)
    return " ".join(decoded)


def _extract_body(msg):
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html = payload.decode(charset, errors="replace")
                    return re.sub(r"<[^>]+>", " ", html)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                return re.sub(r"<[^>]+>", " ", text)
            return text
    return ""


def _extract_sender_name(from_header):
    """Extract just the name or short email from the From header."""
    decoded = _decode_header(from_header)
    # Try to get name before <email>
    match = re.match(r"^(.+?)\s*<", decoded)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        if name:
            return name
    # Fall back to email username
    match = re.search(r"<?([^<@]+)@", decoded)
    if match:
        return match.group(1).strip()
    return decoded[:20]


def fetch_recent_emails(n=10):
    """Fetch the N most recent emails from IMAP. Returns list of dicts."""
    try:
        imap = imaplib.IMAP4_SSL(config["IMAP_SERVER"], config["IMAP_PORT"])
        imap.login(config["IMAP_USER"], config["IMAP_PASSWORD"])
        imap.select(config["IMAP_FOLDER"], readonly=True)

        _, data = imap.search(None, "ALL")
        msg_nums = data[0].split()
        if not msg_nums:
            imap.close()
            imap.logout()
            return []

        # Take the last N message numbers
        recent = msg_nums[-n:]
        emails = []

        for num in reversed(recent):
            _, msg_data = imap.fetch(num, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            message_id = msg.get("Message-ID", f"unknown-{num.decode()}")
            sender = _extract_sender_name(msg.get("From"))
            subject = _decode_header(msg.get("Subject")) or "(no subject)"
            date_str = msg.get("Date", "")
            body = _extract_body(msg)[:2000]

            emails.append({
                "message_id": message_id,
                "sender": sender,
                "subject": subject,
                "date": date_str,
                "body_text": body,
            })

        imap.close()
        imap.logout()
        return emails

    except Exception as e:
        print(f"[PiMail] IMAP error: {e}")
        return []
