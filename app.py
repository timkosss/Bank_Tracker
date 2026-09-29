from flask import Flask, render_template, jsonify, request

import config
import db
import mail_fetcher

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", categories=config.DEFAULT_CATEGORIES)


@app.route("/api/refresh", methods=["POST"])
def refresh():
    """Checks the inbox for new purchase alerts. If IMAP isn't configured
    yet, fails quietly so the UI can still be used with mock data."""
    try:
        inserted = mail_fetcher.fetch_new_purchases()
        return jsonify({"ok": True, "inserted": inserted})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200


@app.route("/api/pending")
def pending():
    return jsonify(db.get_pending())


@app.route("/api/purchases/<int:purchase_id>/complete", methods=["POST"])
def complete(purchase_id):
    data = request.get_json(force=True)
    category = data.get("category", "Other")
    note = data.get("note", "")
    db.complete_purchase(purchase_id, category, note)
    return jsonify({"ok": True})


@app.route("/api/purchases/<int:purchase_id>/skip", methods=["POST"])
def skip(purchase_id):
    db.skip_purchase(purchase_id)
    return jsonify({"ok": True})


@app.route("/api/transactions")
def transactions():
    return jsonify(db.get_transactions())


@app.route("/api/totals")
def totals():
    return jsonify(db.get_totals_by_category())


# --- Dev helper: add a fake pending purchase without needing real email ---
@app.route("/api/mock-purchase", methods=["POST"])
def mock_purchase():
    import random
    from datetime import datetime

    merchant = request.get_json(silent=True) or {}
    name = merchant.get("merchant", "Test Merchant")
    amount = merchant.get("amount", round(random.uniform(5, 80), 2))
    db.insert_purchase(
        name, amount, datetime.now().isoformat(timespec="minutes"),
        f"mock-{datetime.now().timestamp()}",
    )
    return jsonify({"ok": True})


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True, port=5050)
