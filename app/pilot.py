"""Invite-only invoice match pilot and hosted checkout."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import time
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import stripe
from flask import Flask, abort, redirect, render_template, request, send_file, session, url_for
from pypdf.errors import PdfReadError

from app.pilot_match import (
    MAX_CONTEXT_BYTES,
    MAX_PDF_BYTES,
    PilotInputError,
    build_report,
    read_context,
    sample_context,
    sample_pdf,
)
from app.pilot_present import present_checks

PRICE = 500
CURRENCY = "usd"
RETENTION = 7 * 24 * 60 * 60
CHECKOUT_WINDOW = 2 * 60 * 60


def _persisted_session_key(database: Path) -> str:
    key_file = database.with_name(database.name + ".session-key")
    try:
        return key_file.read_text()
    except FileNotFoundError:
        pass
    database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = key_file.with_name(key_file.name + "." + secrets.token_hex(16))
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(secrets.token_hex(32))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, key_file)
        except FileExistsError:
            pass
    finally:
        temporary.unlink()
    return key_file.read_text()


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="pilot_templates", static_folder="pilot_static")
    mode = os.getenv("PILOT_MODE", "demo")
    app.config.update(
        PILOT_MODE=mode,
        PILOT_PUBLIC_DEMO=os.getenv("PILOT_PUBLIC_DEMO") == "1",
        SECRET_KEY=os.getenv("PILOT_SESSION_KEY"),
        PILOT_ACCESS_CODE=os.getenv("PILOT_ACCESS_CODE", ""),
        PILOT_BASE_URL=os.getenv("PILOT_BASE_URL", ""),
        PILOT_DB=os.getenv("PILOT_DB", str(Path(app.instance_path) / f"pilot-{mode}.db")),
        STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY", ""),
        STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(seconds=RETENTION),
        MAX_CONTENT_LENGTH=MAX_PDF_BYTES + MAX_CONTEXT_BYTES + 32 * 1024,
        MAX_FORM_PARTS=8,
    )
    app.config.update(config or {})
    mode = app.config["PILOT_MODE"]
    if mode not in {"demo", "stripe-test", "live"}:
        raise ValueError("PILOT_MODE must be demo, stripe-test or live.")
    demo, live = mode == "demo", mode == "live"
    public_demo = app.config["PILOT_PUBLIC_DEMO"]
    if public_demo and not demo:
        raise ValueError("PILOT_PUBLIC_DEMO requires demo mode.")
    if public_demo:
        app.config["MAX_CONTENT_LENGTH"] = 8 * 1024
    public_report = (
        json.dumps(build_report(sample_pdf(), read_context(sample_context()), demo=True))
        if public_demo else None
    )
    app.config["SESSION_COOKIE_SECURE"] = (
        not demo or public_demo or os.getenv("PILOT_SECURE_COOKIE") == "1"
    )
    app.config["SESSION_COOKIE_NAME"] = f"invoice_pilot_{mode}"
    access = app.config["PILOT_ACCESS_CODE"].encode()
    base_url = app.config["PILOT_BASE_URL"].rstrip("/")
    webhook_secret = app.config["STRIPE_WEBHOOK_SECRET"]
    checkout = None
    if demo:
        app.secret_key = app.secret_key or _persisted_session_key(Path(app.config["PILOT_DB"]))
    else:
        key = app.config["STRIPE_SECRET_KEY"]
        key_mode = "live" if live else "test"
        origin = urlsplit(base_url)
        if (
            len(app.secret_key or "") < 32
            or len(access) < 24
            or origin.scheme != "https"
            or not origin.hostname
            or origin.username is not None
            or origin.path
            or origin.query
            or origin.fragment
            or not key.startswith((f"sk_{key_mode}_", f"rk_{key_mode}_"))
            or not webhook_secret.startswith("whsec_")
        ):
            raise ValueError("Configure the pilot's HTTPS origin, access code, session key and matching Stripe credentials.")
        if live and not all(os.getenv(name) for name in ("VLLM_BASE_URL", "MODEL_NAME")):
            raise ValueError("Live mode requires a configured invoice extraction endpoint and model.")
        checkout = stripe.StripeClient(
            key, http_client=stripe.RequestsClient(timeout=8), max_network_retries=0
        ).v1.checkout.sessions
    access_tag = hmac.new(app.secret_key.encode(), access, hashlib.sha256).hexdigest()

    database = Path(app.config["PILOT_DB"])
    database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    def connect():
        db = sqlite3.connect(database)
        db.row_factory = sqlite3.Row
        return closing(db)

    with connect() as db, db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, mode TEXT NOT NULL,
                created INTEGER NOT NULL, report TEXT NOT NULL,
                checkout_id TEXT UNIQUE, paid INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS pilot_usage (day INTEGER PRIMARY KEY, attempts INTEGER NOT NULL);
        """)

    def now():
        return int(time.time())

    def purge(db):
        db.execute("DELETE FROM reports WHERE created <= ?", (now() - RETENTION,))
        db.execute("DELETE FROM pilot_usage WHERE day < ?", (now() // 86400,))

    @app.cli.command("purge-reports")
    def purge_reports():
        with connect() as db, db:
            purge(db)

    @app.after_request
    def privacy(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'self'; img-src 'self'; "
            "form-action 'self' https://checkout.stripe.com; base-uri 'none'; frame-ancestors 'self'"
        )
        return response

    @app.before_request
    def protect():
        if request.endpoint in {"static", "webhook", None}:
            return
        if public_demo and request.method == "POST" and request.mimetype != "application/x-www-form-urlencoded":
            abort(415)
        if "owner" not in session:
            session.update(owner=secrets.token_urlsafe(24), csrf=secrets.token_urlsafe(32))
            session.permanent = True
        if request.method == "POST" and not hmac.compare_digest(
            request.form.get("csrf", "").encode(), session["csrf"].encode()
        ):
            error = "Your session expired or the page was out of date. Please try again; no payment was taken."
            if access and session.get("access") != access_tag:
                return page("locked", error=error), 400
            return home_page(error, 400)
        if access and request.endpoint != "unlock" and session.get("access") != access_tag:
            return page("locked"), 403

    def page(screen, **kwargs):
        return render_template(
            "pilot.html", screen=screen, mode=mode, public_demo=public_demo,
            price=f"${PRICE / 100:.2f}", **kwargs,
        )

    def home_page(error=None, status=200):
        return page("home", error=error), status

    @app.post("/unlock")
    def unlock():
        if not hmac.compare_digest(request.form.get("code", "").encode(), access):
            return page("locked", error="That pilot code did not match."), 403
        session["access"] = access_tag
        return redirect(url_for("home"), 303)

    @app.get("/")
    def home():
        return home_page()

    @app.get("/sample/<kind>")
    def sample(kind):
        if kind == "context":
            return send_file(io.BytesIO(sample_context()), download_name="sample-po-and-receipts.json", as_attachment=True)
        if kind == "invoice" and not live:
            return send_file(io.BytesIO(sample_pdf()), download_name="sample-invoice.pdf", as_attachment=True)
        abort(404)

    @app.post("/reports")
    def prepare():
        if public_demo:
            if request.form.get("source") != "sample":
                abort(415)
            session.update(recent_report="sample", public_report_paid=False)
            return redirect(url_for("view_order", report_id="sample"), 303)
        try:
            if not live and request.form.get("source") == "sample":
                pdf, context_data = sample_pdf(), sample_context()
            else:
                invoice, context = request.files.get("invoice"), request.files.get("context")
                if invoice is None or not invoice.filename or context is None or not context.filename:
                    raise PilotInputError("Choose both an invoice PDF and a PO and receipts JSON file.")
                pdf = invoice.read(MAX_PDF_BYTES + 1)
                context_data = context.read(MAX_CONTEXT_BYTES + 1)
            context = read_context(context_data)
            if live:
                with connect() as db, db:
                    purge(db)
                    usage = db.execute(
                        "INSERT INTO pilot_usage VALUES (?, 1) ON CONFLICT(day) DO UPDATE "
                        "SET attempts = attempts + 1 WHERE attempts < 25",
                        (now() // 86400,),
                    )
                    if not usage.rowcount:
                        return home_page("The pilot has reached today's report limit. Try again tomorrow.", 429)
            report = build_report(pdf, context, demo=not live)
        except (PilotInputError, PdfReadError, ValueError) as exc:
            error = str(exc) if isinstance(exc, PilotInputError) else "Could not read the files. Check the formats and try again."
            return home_page(error, 422)
        except Exception as exc:
            app.logger.warning("Report generation failed (%s)", type(exc).__name__)
            return home_page("The report could not be prepared. No payment was taken.", 503)
        report_id = secrets.token_urlsafe(24)
        with connect() as db, db:
            purge(db)
            db.execute(
                "INSERT INTO reports (id, owner, mode, created, report) VALUES (?, ?, ?, ?, ?)",
                (report_id, session["owner"], mode, now(), json.dumps(report)),
            )
        session["recent_report"] = report_id
        return redirect(url_for("view_order", report_id=report_id), 303)

    def get_report(report_id):
        if public_demo:
            if report_id != "sample" or session.get("recent_report") != report_id:
                abort(404)
            return {"id": report_id, "report": public_report, "paid": session.get("public_report_paid", False)}
        with connect() as db:
            row = db.execute(
                "SELECT * FROM reports WHERE id = ? AND owner = ? AND mode = ? AND created > ?",
                (report_id, session["owner"], mode, now() - RETENTION),
            ).fetchone()
        if row is None:
            abort(404)
        return row

    def mark_paid(payment):
        if (
            payment.get("mode") != "payment"
            or payment.get("status") != "complete"
            or payment.get("payment_status") != "paid"
            or payment.get("livemode") is not live
            or payment.get("currency") != CURRENCY
            or payment.get("amount_total") != PRICE
            or not isinstance(payment.get("client_reference_id"), str)
            or not isinstance(payment.get("id"), str)
        ):
            return
        with connect() as db, db:
            db.execute(
                "UPDATE reports SET paid = 1 WHERE id = ? AND checkout_id = ? AND mode = ?",
                (payment["client_reference_id"], payment["id"], mode),
            )

    def checkout_page(row, error=None):
        invoice = json.loads(row["report"])["extracted_invoice"]
        return page(
            "checkout",
            report_id=row["id"],
            invoice=invoice,
            error=error,
            expired=not demo and now() >= row["created"] + CHECKOUT_WINDOW - (0 if row["checkout_id"] else 1810),
        )

    @app.get("/reports/<report_id>")
    def view_order(report_id):
        row = get_report(report_id)
        error = None
        if checkout is not None and row["checkout_id"] and not row["paid"]:
            try:
                mark_paid(checkout.retrieve(row["checkout_id"]))
                row = get_report(report_id)
            except stripe.StripeError:
                error = "Payment status is unavailable. Refresh this page shortly."
        if row["paid"]:
            report = json.loads(row["report"])
            if "display_checks" not in report:
                report["display_checks"] = present_checks(report)
            return page("result", report_id=report_id, report=report)
        return checkout_page(row, error)

    @app.post("/reports/<report_id>/checkout")
    def start_checkout(report_id):
        row = get_report(report_id)
        order_path = url_for("view_order", report_id=report_id)
        if row["paid"]:
            return redirect(order_path, 303)
        if public_demo:
            session["public_report_paid"] = True
            return redirect(order_path, 303)
        if demo:
            with connect() as db, db:
                db.execute("UPDATE reports SET paid = 1 WHERE id = ? AND mode = 'demo'", (report_id,))
            return redirect(order_path, 303)

        expiration = row["created"] + CHECKOUT_WINDOW
        if now() >= expiration - (0 if row["checkout_id"] else 1810):
            return redirect(order_path, 303)
        try:
            if row["checkout_id"]:
                payment = checkout.retrieve(row["checkout_id"])
            else:
                payment = checkout.create(
                    {
                        "mode": "payment",
                        "client_reference_id": report_id,
                        "success_url": base_url + order_path,
                        "cancel_url": base_url + order_path,
                        "expires_at": expiration,
                        "payment_method_types": ["card"],
                        "line_items": [{
                            "price_data": {
                                "currency": CURRENCY,
                                "unit_amount": PRICE,
                                "product_data": {"name": "Invoice Match — one report"},
                            },
                            "quantity": 1,
                        }],
                    },
                    options={"idempotency_key": f"invoice-pilot-{mode}-{report_id}"},
                )
                with connect() as db, db:
                    db.execute(
                        "UPDATE reports SET checkout_id = ? WHERE id = ? AND checkout_id IS NULL",
                        (payment.id, report_id),
                    )
        except stripe.StripeError:
            return checkout_page(row, "Stripe is unavailable. Try again shortly."), 503
        if payment.status != "open" or not payment.url:
            return redirect(order_path, 303)
        link = urlsplit(payment.url)
        if link.scheme != "https" or link.netloc != "checkout.stripe.com":
            abort(502)
        return redirect(payment.url, 303)

    @app.post("/stripe/webhook")
    def webhook():
        if demo:
            abort(404)
        try:
            event = stripe.Webhook.construct_event(
                request.get_data(), request.headers.get("Stripe-Signature", ""), webhook_secret
            )
        except (ValueError, stripe.SignatureVerificationError):
            abort(400)
        if event.type == "checkout.session.completed":
            mark_paid(event.data.object)
        return "", 204

    @app.get("/reports/<report_id>/download")
    def download(report_id):
        row = get_report(report_id)
        if not row["paid"]:
            abort(403)
        return send_file(
            io.BytesIO(row["report"].encode()), mimetype="application/json",
            download_name="invoice-match-report.json", as_attachment=True,
        )

    @app.errorhandler(413)
    def oversized(_error):
        return home_page("The upload is too large. Use a PDF up to 5 MB and JSON up to 128 KB.", 413)

    return app
