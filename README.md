# Wells Fargo Purchase Tracker (local)

A local Flask app that watches an inbox for Wells Fargo purchase-alert
emails and, every time you refresh the page, pops up a quick "what was
this?" prompt for any new purchase so you can categorize it on the spot.

## How it works

1. Set up **free purchase/transaction alerts** in Wells Fargo online
   banking, sent to a **dedicated email address** (a fresh Gmail account,
   or a "+" alias if your provider supports it).
2. This app connects to that inbox via IMAP, looking for unread emails
   from Wells Fargo.
3. It parses merchant + amount out of each alert and stores it as a
   "pending" purchase.
4. When you open/refresh the page, any pending purchases pop up one at a
   time asking you to pick a category and add an optional note.
5. Once categorized, it shows up in your transaction list and category
   totals.

## Setup

```bash
cd wf-budget-tracker
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your inbox credentials, then
load it and run:

```bash
export $(cat .env | xargs)      # Windows: use `set` per line, or python-dotenv
python app.py
```

Visit **http://localhost:5050**.

## Try it without email set up yet

You don't need IMAP working to try the popup flow. With the server
running, in another terminal:

```bash
curl -X POST http://localhost:5050/api/mock-purchase \
  -H "Content-Type: application/json" \
  -d '{"merchant": "Trader Joe'\''s", "amount": 42.17}'
```

Then refresh the page (or click "Check for new purchases") — the popup
will appear asking you to categorize it.

## Important: the email parser needs tuning to YOUR real alerts

Wells Fargo's alert email wording isn't public/documented, and it varies
by alert type. `mail_fetcher.py` has a best-guess regex to pull out the
dollar amount and merchant name, but you'll very likely need to adjust
it once you see a real one. To help with that:

```bash
python mail_fetcher.py --debug
```

This prints the raw text of every unread alert email it finds, so you
can see exactly what Wells Fargo's wording looks like and tighten up the
`PATTERNS` regexes in `mail_fetcher.py` accordingly.

## Project structure

```
wf-budget-tracker/
├── app.py              # Flask routes / API
├── db.py                # SQLite schema + queries
├── mail_fetcher.py      # IMAP connection + email parsing
├── config.py             # Settings, loaded from environment variables
├── templates/
│   └── index.html       # Page + popup modal
├── static/
│   ├── style.css
│   └── app.js            # Popup queue logic, fetch calls
├── requirements.txt
└── .env.example
```

## Notes / next steps you might want

- **Duplicate protection** is already handled — each email's Message-ID
  is stored, so re-checking the inbox never double-inserts a purchase.
- **Categories** are defined in `config.py` (`DEFAULT_CATEGORIES`) —
  edit that list to match how you actually want to budget.
- **Skipped purchases** currently just get marked `skipped` and won't
  pop up again. If you want a way to review/re-open skipped ones later,
  that'd be a small addition to `db.py` + a new API route.
- **Auto-refresh** — right now checking for new purchases is manual
  (button click) as you asked. If you want it to check automatically
  every N minutes in the background, that's a small addition using
  `setInterval` in `app.js`.
