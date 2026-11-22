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
    response = browser.post(
        "/reports",
        data={"csrf": csrf(browser), "invoice": (io.BytesIO(b"%PDF- private"), "invoice.pdf")},
    )
    assert response.status_code == 415
    assert b"Simulate payment" in browser.get(sample_order(browser)).data


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
