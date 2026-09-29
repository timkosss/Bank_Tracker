import os

# --- Email / IMAP settings ---
# Point these at the dedicated inbox that receives your Wells Fargo
# purchase alert emails. Using a Gmail "app password" (not your real
# password) is strongly recommended if IMAP_HOST is Gmail.
IMAP_HOST = os.environ.get("WF_IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.environ.get("WF_IMAP_PORT", "993"))
IMAP_USER = os.environ.get("WF_IMAP_USER", "")
IMAP_PASSWORD = os.environ.get("WF_IMAP_PASSWORD", "")
IMAP_FOLDER = os.environ.get("WF_IMAP_FOLDER", "INBOX")

# Only pull emails whose "From" contains this (adjust once you see a
# real Wells Fargo alert email address).
ALERT_SENDER_FILTER = os.environ.get("WF_ALERT_SENDER", "wellsfargo.com")

# --- App settings ---
DB_PATH = os.environ.get("WF_DB_PATH", "budget.db")
DEFAULT_CATEGORIES = [
    "Groceries",
    "Dining",
    "Gas/Transport",
    "Shopping",
    "Bills/Subscriptions",
    "Entertainment",
    "Health",
    "Other",
]
