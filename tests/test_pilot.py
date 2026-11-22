from __future__ import annotations

import hashlib
import hmac
import io
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import stripe

from app import pilot


@pytest.fixture
def demo(tmp_path):
    return pilot.create_app({"TESTING": True, "PILOT_DB": str(tmp_path / "demo.db")})


def csrf(browser):
    with browser.session_transaction() as session:
        return session["csrf"]


def sample_order(browser):
    response = browser.post("/reports", data={"source": "sample", "csrf": csrf(browser)})
    assert response.status_code == 303
    return response.location


def test_demo_session_survives_app_restart(tmp_path, monkeypatch):
    monkeypatch.delenv("PILOT_SESSION_KEY", raising=False)
    config = {"TESTING": True, "PILOT_MODE": "demo", "PILOT_DB": str(tmp_path / "demo.db")}
    first = pilot.create_app(config)
    browser = first.test_client()
    browser.get("/")
    order = sample_order(browser)
    token = csrf(browser)
    second = pilot.create_app(config)
    assert first.secret_key == second.secret_key
    key_file = tmp_path / "demo.db.session-key"
    assert key_file.read_text() == first.secret_key
    assert len(first.secret_key) == 64
    assert key_file.stat().st_mode & 0o777 == 0o600
    restarted = second.test_client()
    cookie_name = first.config["SESSION_COOKIE_NAME"]
    restarted.set_cookie(cookie_name, browser.get_cookie(cookie_name).value)
    assert b"Open your latest report" in restarted.get("/").data
    assert restarted.get(order).status_code == 200
    assert restarted.post(f"{order}/checkout", data={"csrf": token}).status_code == 303


def test_concurrent_session_key_creation(tmp_path):
    database = tmp_path / "data" / "demo.db"
    with ThreadPoolExecutor(max_workers=8) as workers:
        keys = list(workers.map(pilot._persisted_session_key, [database] * 16))
    assert len(set(keys)) == 1
    assert len(keys[0]) == 64
    assert list(database.parent.iterdir()) == [database.with_name("demo.db.session-key")]


@pytest.mark.parametrize("explicit", [False, True])
def test_configured_session_key_wins(tmp_path, monkeypatch, explicit):
    config = {"PILOT_MODE": "demo", "PILOT_DB": str(tmp_path / "demo.db")}
    monkeypatch.delenv("PILOT_SESSION_KEY", raising=False)
    pilot.create_app(config)
    key_file = tmp_path / "demo.db.session-key"
    generated = key_file.read_text()
    monkeypatch.setenv("PILOT_SESSION_KEY", "environment-key")
    if explicit:
        config["SECRET_KEY"] = "explicit-key"
    app = pilot.create_app(config)
    assert app.secret_key == ("explicit-key" if explicit else "environment-key")
    assert key_file.read_text() == generated


@pytest.mark.parametrize("token", [None, "", "bad-token"])
@pytest.mark.parametrize("fresh_session", [False, True])
def test_csrf_failure_is_friendly(demo, token, fresh_session):
    browser = demo.test_client()
    if not fresh_session:
        browser.get("/")
    data = {"source": "sample"}
    if token is not None:
        data["csrf"] = token
    response = browser.post("/reports", data=data)
    assert response.status_code == 400
    assert (
        b"Your session expired or the page was out of date. Please try again; no payment was taken."
        in response.data
    )
    assert b"Try the upload flow" in response.data
    with sqlite3.connect(demo.config["PILOT_DB"]) as db:
        assert db.execute("SELECT count(*) FROM reports").fetchone() == (0,)


@pytest.mark.parametrize("invite", [None, "stale", "valid"])
@pytest.mark.parametrize("endpoint", ["/reports", "/unlock"])
def test_csrf_failure_respects_invite(tmp_path, invite, endpoint):
    access_code = "test-invite-code"
    app = pilot.create_app({
        "TESTING": True,
        "PILOT_MODE": "demo",
        "PILOT_DB": str(tmp_path / "demo.db"),
        "PILOT_ACCESS_CODE": access_code,
    })
    browser = app.test_client()
    assert browser.get("/").status_code == 403
    if invite == "valid":
        assert browser.post("/unlock", data={"csrf": csrf(browser), "code": access_code}).status_code == 303
    elif invite is not None:
        with browser.session_transaction() as session:
            session["access"] = invite
    response = browser.post(endpoint, data={"csrf": "bad-token", "source": "sample", "code": access_code})
    assert response.status_code == 400
    assert (
        b"Your session expired or the page was out of date. Please try again; no payment was taken."
        in response.data
    )
    assert (b"Enter your invite code" in response.data) is (invite != "valid")
    assert (b"Try the upload flow" in response.data) is (invite == "valid")
    if invite != "valid":
        assert browser.post("/unlock", data={"csrf": csrf(browser), "code": access_code}).status_code == 303
        assert browser.get("/").status_code == 200


def test_sample_upload_and_report_access(demo):
    browser = demo.test_client()
    assert b"Try the upload flow" in browser.get("/").data
    order = browser.post(
        "/reports",
        data={
            "csrf": csrf(browser),
            "invoice": (io.BytesIO(browser.get("/sample/invoice").data), "invoice.pdf"),
            "context": (io.BytesIO(browser.get("/sample/context").data), "context.json"),
        },
    ).location
    checkout = browser.get(order).data
    assert b"Simulate payment" in checkout and b"Invoice INV-2026001" in checkout
    assert b"Documents match." not in checkout
    assert browser.get(f"{order}/download").status_code == 403
    assert browser.post(f"{order}/checkout").status_code == 400
    other = demo.test_client()
    assert other.get(order).status_code == 404
    assert other.post(f"{order}/checkout", data={"csrf": csrf(other)}).status_code == 404
    response = browser.post(f"{order}/checkout", data={"csrf": csrf(browser)}, follow_redirects=True)
    assert b"Documents match." in response.data and b"Simulated payment confirmed" in response.data
    assert b"Quantity within purchase order" in response.data
    assert b"SKU-1001: within tolerance" in response.data
    assert b"Purchase order is open" in response.data
    assert b"Qty rcv" not in response.data
    download = browser.get(f"{order}/download")
    assert download.headers["Cache-Control"] == "no-store"
    report = download.json
    assert report["decision"] == "READY_FOR_DRAFT"
    assert report["proposed_journal"]["balanced"] is True
    assert not ({"DUPLICATE_INVOICE", "VENDOR_ACTIVE"} & {check["code"] for check in report["control_checks"]})
    assert other.get(f"{order}/download").status_code == 404


def test_review_and_non_fixture_upload(demo):
    browser = demo.test_client()
    context = json.loads(browser.get("/sample/context").data)
    context["receipts"][0]["lines"][0]["quantity_received"] = "0"
    for pdf, status in [(b"%PDF- non-fixture", 422), (browser.get("/sample/invoice").data, 303)]:
        response = browser.post(
            "/reports",
            data={
                "csrf": csrf(browser),
                "invoice": (io.BytesIO(pdf), "invoice.pdf"),
                "context": (io.BytesIO(json.dumps(context).encode()), "context.json"),
            },
        )
        assert response.status_code == status
    order = response.location
    result = browser.post(f"{order}/checkout", data={"csrf": csrf(browser)}, follow_redirects=True)
    assert b"Review needed." in result.data
    assert b"Invoiced quantity exceeds the amount received" in result.data
    assert b"SKU-1001: invoiced 3, received 0" in result.data
    assert "QUANTITY_EXCEEDS_RECEIPT" in browser.get(f"{order}/download").json["exception_codes"]


def test_po_with_blank_account_is_rejected(demo):
    browser = demo.test_client()
    context = json.loads(browser.get("/sample/context").data)
    context["purchase_order"]["lines"][0]["gl_account"] = "  "
    response = browser.post(
        "/reports",
        data={
            "csrf": csrf(browser),
            "invoice": (io.BytesIO(browser.get("/sample/invoice").data), "invoice.pdf"),
            "context": (io.BytesIO(json.dumps(context).encode()), "context.json"),
        },
    )
    assert response.status_code == 422
    assert b"Enter a GL account" in response.data


def test_upload_guidance_and_inline_rejection(demo):
    browser = demo.test_client()
    home = browser.get("/")
    for text in (b"only the provided sample PDF", b"No OCR", b"JSON field-by-field",
                 b"quantity_received", b"gl_account", b"No reports yet."):
        assert text in home.data
    assert browser.get("/sample/context").json == json.loads(pilot.sample_context())
    response = browser.post("/reports", data={
        "csrf": csrf(browser),
        "invoice": (io.BytesIO(b"%PDF- scanned invoice"), "scan.pdf"),
        "context": (io.BytesIO(pilot.sample_context()), "context.json"),
    })
    assert response.status_code == 422
    assert b'role="alert"' in response.data
    assert b"only accepts the provided sample PDF" in response.data
    assert b"Download the supported sample PDF" in response.data
    assert b'name="invoice"' in response.data and b'name="context"' in response.data
    assert b"No reports yet." in response.data


def test_history_duplicate_confirmation(demo):
    browser = demo.test_client()
    browser.get("/")
    first = sample_order(browser)
    browser.post(f"{first}/checkout", data={"csrf": csrf(browser)})
    duplicate = browser.post("/reports", data={"source": "sample", "csrf": csrf(browser)})
    assert duplicate.status_code == 200
    assert b"These documents already have a report" in duplicate.data
    assert first.encode() in duplicate.data
    assert b"new $5.00 USD checkout" in duplicate.data
    with sqlite3.connect(demo.config["PILOT_DB"]) as db:
        assert db.execute("SELECT count(*) FROM reports").fetchone()[0] == 1
    assert browser.post(f"{first}/copy").status_code == 400
    second = browser.post(f"{first}/copy", data={"csrf": csrf(browser)}).location
    assert second != first
    history = browser.get("/").data
    assert first.encode() in history and second.encode() in history
    assert b"Paid (simulated)" in history and b"Unpaid (simulated)" in history
    assert b"Created " in history and b" UTC" in history
    other = demo.test_client()
    assert first.encode() not in other.get("/").data
    assert other.post(f"{first}/copy", data={"csrf": csrf(other)}).status_code == 404
    assert b"Documents match." in browser.get(first).data
    with sqlite3.connect(demo.config["PILOT_DB"]) as db:
        db.execute("UPDATE reports SET created = ?", (int(time.time()) - pilot.RETENTION - 1,))
    assert b"No reports yet." in browser.get("/").data
    assert browser.post(f"{first}/copy", data={"csrf": csrf(browser)}).status_code == 404


def test_duplicate_prefers_most_recent_paid_report(demo):
    browser = demo.test_client()
    browser.get("/")
    first = sample_order(browser)
    second = browser.post(f"{first}/copy", data={"csrf": csrf(browser)}).location
    third = browser.post(f"{first}/copy", data={"csrf": csrf(browser)}).location

    def suggested_report():
        response = browser.post("/reports", data={"source": "sample", "csrf": csrf(browser)})
        assert response.status_code == 200
        return response.data

    assert third.encode() in suggested_report()
    browser.post(f"{first}/checkout", data={"csrf": csrf(browser)})
    assert first.encode() in suggested_report()
    assert third.encode() not in suggested_report()
    browser.post(f"{second}/checkout", data={"csrf": csrf(browser)})
    assert second.encode() in suggested_report()
    assert first.encode() not in suggested_report()


@pytest.mark.parametrize("invite", ["valid", "missing", "revoked"])
@pytest.mark.parametrize("oversized", [False, True])
def test_history_requires_current_invite(tmp_path, invite, oversized):
    config = {
        "TESTING": True, "PILOT_MODE": "demo",
        "PILOT_DB": str(tmp_path / "private.db"),
        "PILOT_ACCESS_CODE": "original-invite", "SECRET_KEY": "stable-test-key",
    }
    app = pilot.create_app(config)
    browser = app.test_client()
    browser.get("/")
    browser.post("/unlock", data={"csrf": csrf(browser), "code": "original-invite"})
    order = sample_order(browser)
    assert b"Northwind Office Supply LLC" in browser.get("/").data
    if invite == "missing":
        with browser.session_transaction() as session:
            session.pop("access")
    elif invite == "revoked":
        config["PILOT_ACCESS_CODE"] = "replacement-invite"
        restarted = pilot.create_app(config).test_client()
        name = app.config["SESSION_COOKIE_NAME"]
        restarted.set_cookie(name, browser.get_cookie(name).value)
        browser = restarted
    if oversized:
        response = browser.post("/reports", data=b"x" * (app.config["MAX_CONTENT_LENGTH"] + 1),
                                content_type="application/x-www-form-urlencoded")
        assert response.status_code == 413
    else:
        response = browser.post("/reports", data={"csrf": "stale-token"})
        assert response.status_code == 400
    if invite == "valid":
        assert b"Northwind Office Supply LLC" in response.data
        assert order.encode() in response.data
    else:
        assert b"Enter your invite code" in response.data
        assert b"INV-2026001" not in response.data
        assert b"Northwind Office Supply LLC" not in response.data
        assert order.encode() not in response.data
        assert b"report-history" not in response.data


def test_retention(demo):
    browser = demo.test_client()
    browser.get("/")
    order = sample_order(browser)
    with sqlite3.connect(demo.config["PILOT_DB"]) as db:
        db.execute("UPDATE reports SET created = ?", (int(time.time()) - pilot.RETENTION - 1,))
    assert browser.get(order).status_code == 404
    assert demo.test_cli_runner().invoke(args=["purge-reports"]).exit_code == 0
    with sqlite3.connect(demo.config["PILOT_DB"]) as db:
        assert db.execute("SELECT count(*) FROM reports").fetchone() == (0,)


def test_public_demo_disables_uploads(tmp_path):
    app = pilot.create_app({"PILOT_PUBLIC_DEMO": True, "PILOT_DB": str(tmp_path / "public.db")})
    browser = app.test_client()
    home = browser.get("/")
    assert b"Public demo" in home.data and b'type="file"' not in home.data
    assert b'id="report-history"' not in home.data
    response = browser.post(
        "/reports",
        data={"csrf": csrf(browser), "invoice": (io.BytesIO(b"%PDF- private"), "invoice.pdf")},
    )
    assert response.status_code == 415
    assert b"Simulate payment" in browser.get(sample_order(browser)).data


def test_public_demo_reuses_sample_without_storing_reports(tmp_path):
    db_path = tmp_path / "public.db"
    app = pilot.create_app({"PILOT_PUBLIC_DEMO": True, "PILOT_DB": str(db_path)})
    first, second = app.test_client(), app.test_client()
    for browser in (first, second):
        browser.get("/")
        assert sample_order(browser) == "/reports/sample"
        assert sample_order(browser) == "/reports/sample"
        assert browser.get("/reports/sample/download").status_code == 403
    first.post("/reports/sample/checkout", data={"csrf": csrf(first)})
    assert first.get("/reports/sample/download").json["demo"] is True
    assert sample_order(first) == "/reports/sample"
    assert first.get("/reports/sample/download").status_code == 200
    assert second.get("/reports/sample/download").status_code == 403
    assert first.post("/reports/sample/copy", data={"csrf": csrf(first)}).status_code == 404
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT count(*) FROM reports").fetchone() == (0,)


def test_live_report_copy_uses_daily_quota(tmp_path, monkeypatch):
    monkeypatch.setenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    monkeypatch.setenv("MODEL_NAME", "test-model")
    db_path = tmp_path / "live.db"
    code = "test-only-access-code-for-invoice-match"
    app = pilot.create_app({
        "TESTING": True, "PILOT_MODE": "live", "PILOT_DB": str(db_path),
        "PILOT_ACCESS_CODE": code, "PILOT_BASE_URL": "https://pilot.example.com",
        "SECRET_KEY": "test-only-session-key-for-invoice-match",
        "STRIPE_SECRET_KEY": "sk_live_example", "STRIPE_WEBHOOK_SECRET": "whsec_example",
    })
    browser = app.test_client()
    browser.get("/")
    assert browser.post("/unlock", data={"csrf": csrf(browser), "code": code}).status_code == 303
    with browser.session_transaction() as session:
        owner = session["owner"]
    report = pilot.build_report(pilot.sample_pdf(), pilot.read_context(pilot.sample_context()), demo=True)
    now = int(time.time())
    with sqlite3.connect(db_path) as db:
        db.execute("INSERT INTO pilot_usage VALUES (?, 24)", (now // 86400,))
        db.execute(
            "INSERT INTO reports (id, owner, mode, created, report) VALUES (?, ?, ?, ?, ?)",
            ("example", owner, "live", now, json.dumps(report)),
        )
    assert browser.post("/reports/example/copy", data={"csrf": csrf(browser)}).status_code == 303
    assert browser.post("/reports/example/copy", data={"csrf": csrf(browser)}).status_code == 429
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT count(*) FROM reports").fetchone() == (2,)


@pytest.fixture
def stripe_pilot(tmp_path, monkeypatch):
    access_code = "pilot-access-example-for-tests"
    webhook_secret = "whsec_example"

    class Checkout:
        creations = 0

        def create(self, params, options):
            self.creations += 1
            self.params = params
            self.options = options
            self.payment = stripe.StripeObject.construct_from(
                {
                    "id": "cs_test_order",
                    "mode": "payment",
                    "status": "open",
                    "payment_status": "unpaid",
                    "livemode": False,
                    "amount_total": pilot.PRICE,
                    "currency": pilot.CURRENCY,
                    "client_reference_id": params["client_reference_id"],
                    "url": "https://checkout.stripe.com/example",
                },
                None,
            )
            return self.payment

        def retrieve(self, id):
            assert id == self.payment.id
            return self.payment

    checkout = Checkout()
    monkeypatch.setattr(
        stripe, "StripeClient", lambda *a, **kw: SimpleNamespace(
            v1=SimpleNamespace(checkout=SimpleNamespace(sessions=checkout))
        )
    )
    app = pilot.create_app(
        {
            "TESTING": True,
            "PILOT_DB": str(tmp_path / "stripe.db"),
            "PILOT_MODE": "stripe-test",
            "PILOT_ACCESS_CODE": access_code,
            "PILOT_BASE_URL": "https://pilot.example.com",
            "SECRET_KEY": "app-key-for-tests-not-for-production",
            "STRIPE_SECRET_KEY": "sk_test_example",
            "STRIPE_WEBHOOK_SECRET": webhook_secret,
        }
    )
    browser = app.test_client()
    assert browser.get("/").status_code == 403
    assert browser.post("/unlock", data={"csrf": csrf(browser), "code": access_code}).status_code == 303
    return app, browser, checkout, webhook_secret


def test_stripe_return_verifies_payment(stripe_pilot):
    _, browser, checkout, _ = stripe_pilot
    order = sample_order(browser)
    checkout_path = f"{order}/checkout"
    form = {"csrf": csrf(browser)}
    assert browser.get(f"{order}?session_id=cs_test_forged").status_code == 200
    assert browser.get(f"{order}/download").status_code == 403
    assert browser.post(checkout_path, data=form).location == "https://checkout.stripe.com/example"
    assert checkout.params["success_url"] == "https://pilot.example.com" + order
    assert checkout.params["cancel_url"] == checkout.params["success_url"]
    assert checkout.params["line_items"][0]["price_data"]["unit_amount"] == 500
    assert checkout.options["idempotency_key"].endswith(order.split("/")[-1])
    assert browser.post(checkout_path, data=form).status_code == 303
    assert checkout.creations == 1
    checkout.payment.update({"status": "complete", "payment_status": "paid", "amount_total": 499})
    assert b"Unlock your match report." in browser.get(order).data
    assert browser.get(f"{order}/download").status_code == 403
    checkout.payment.update({"amount_total": 500, "livemode": True})
    assert b"Unlock your match report." in browser.get(order).data
    checkout.payment.update({"livemode": False})
    assert b"Test payment confirmed" in browser.get(order).data
    assert browser.get(f"{order}/download").status_code == 200
    assert browser.post(checkout_path, data=form).location == order


@pytest.mark.parametrize("checkout_started", [False, True])
@pytest.mark.parametrize("paid", [False, True])
def test_duplicate_report_handles_expired_checkout(stripe_pilot, checkout_started, paid):
    app, browser, checkout, _ = stripe_pilot
    previous = sample_order(browser)
    if checkout_started:
        browser.post(f"{previous}/checkout", data={"csrf": csrf(browser)})
        if paid:
            checkout.payment.update({"status": "complete", "payment_status": "paid"})
            assert b"Test payment confirmed" in browser.get(previous).data
    with sqlite3.connect(app.config["PILOT_DB"]) as db:
        age = pilot.CHECKOUT_WINDOW if checkout_started else pilot.CHECKOUT_WINDOW - 1810
        db.execute(
            "UPDATE reports SET created = ?, paid = ? WHERE id = ?",
            (int(time.time()) - age, paid, previous.split("/")[-1]),
        )

    response = browser.post("/reports", data={"source": "sample", "csrf": csrf(browser)})
    if paid:
        assert response.status_code == 200
        assert b"These documents already have a report" in response.data
        assert previous.encode() in response.data
    else:
        assert b"This checkout expired." in browser.get(previous).data
        assert response.status_code == 303
        assert response.location != previous
        assert b"Unlock your match report." in browser.get(response.location).data


def test_signed_webhook_unlocks_without_browser_return(stripe_pilot):
    app, browser, checkout, webhook_secret = stripe_pilot
    order = sample_order(browser)
    browser.post(f"{order}/checkout", data={"csrf": csrf(browser)})
    payload = json.dumps(
        {
            "id": "evt_test",
            "object": "event",
            "type": "checkout.session.completed",
            "data": {"object": {**checkout.payment, "status": "complete", "payment_status": "paid"}},
        }
    )
    timestamp = int(time.time())
    signature = hmac.new(webhook_secret.encode(), f"{timestamp}.{payload}".encode(), hashlib.sha256).hexdigest()
    webhook = app.test_client()
    assert webhook.post("/stripe/webhook", data=payload).status_code == 400
    assert browser.get(f"{order}/download").status_code == 403
    for _ in range(2):
        assert webhook.post(
            "/stripe/webhook", data=payload, headers={"Stripe-Signature": f"t={timestamp},v1={signature}"}
        ).status_code == 204
    assert browser.get(f"{order}/download").status_code == 200
