"""
Connects to the dedicated inbox, pulls unread Wells Fargo purchase-alert
emails, parses out merchant/amount/date, and inserts them into the local
database as pending purchases.

IMPORTANT: The regex in parse_alert_email() is a starting guess. Wells
Fargo's real alert email wording varies by alert type. Once you receive
a real alert, update PATTERNS below to match its actual text. Run
`python mail_fetcher.py --debug` to print the raw email body so you can
see exactly what you're working with.
"""

import re
import imaplib
import email
from email.header import decode_header
from datetime import datetime

import config
import db

# Starting-point patterns for common WF alert phrasings. Adjust these
# once you see your real alert emails -- run with --debug to inspect.
PATTERNS = {
    "amount": re.compile(r"\$([0-9,]+\.[0-9]{2})"),
    "merchant": re.compile(r"at\s+([A-Za-z0-9 &\-\.\'*]+?)(?:\son|\sfor|\.|\n|$)"),
}


def _decode(value):
    if value is None:
        return ""
    parts = decode_header(value)
    out = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="ignore")
        else:
            out += text
    return out


def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="ignore")
        # fall back to html if no plain text part
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="ignore")
        return ""
    else:
        payload = msg.get_payload(decode=True)
        return payload.decode(errors="ignore") if payload else ""


def parse_alert_email(subject, body):
    """Extract (merchant, amount) from an alert email's text. Returns
    None if it doesn't look like a purchase alert we can parse."""
    text = f"{subject}\n{body}"

    amount_match = PATTERNS["amount"].search(text)
    if not amount_match:
        return None
    amount = float(amount_match.group(1).replace(",", ""))

    merchant_match = PATTERNS["merchant"].search(text)
    merchant = merchant_match.group(1).strip() if merchant_match else "Unknown merchant"

    return merchant, amount


def fetch_new_purchases(debug=False):
    """Connects via IMAP, scans unread mail from the alert sender, parses
    each one, and inserts new pending purchases into the DB. Returns the
    number of new purchases inserted."""
    if not config.IMAP_USER or not config.IMAP_PASSWORD:
        raise RuntimeError(
            "WF_IMAP_USER / WF_IMAP_PASSWORD not set. See .env.example."
        )

    inserted = 0
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    try:
        imap.login(config.IMAP_USER, config.IMAP_PASSWORD)
        imap.select(config.IMAP_FOLDER)

        status, data = imap.search(
            None, f'(UNSEEN FROM "{config.ALERT_SENDER_FILTER}")'
        )
        if status != "OK":
            return 0

        ids = data[0].split()
        for eid in ids:
            status, msg_data = imap.fetch(eid, "(RFC822)")
            if status != "OK":
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            subject = _decode(msg.get("Subject"))
            body = _get_body(msg)
            message_id = msg.get("Message-ID", eid.decode())

            if debug:
                print("--- RAW EMAIL ---")
                print("Subject:", subject)
                print(body[:1000])
                print("-----------------")

            parsed = parse_alert_email(subject, body)
            if parsed is None:
                continue
            merchant, amount = parsed
            purchased_at = datetime.now().isoformat(timespec="minutes")

            db.insert_purchase(merchant, amount, purchased_at, message_id)
            inserted += 1

        return inserted
    finally:
        imap.logout()


if __name__ == "__main__":
    import sys

    db.init_db()
    debug = "--debug" in sys.argv
    count = fetch_new_purchases(debug=debug)
    print(f"Inserted {count} new pending purchase(s).")
