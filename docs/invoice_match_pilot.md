# Invoice Match pilot

Invoice Match checks a text-based vendor invoice against one USD purchase order and its receiving records. It generates a human-readable decision, exceptions and a proposed journal when the documents match, plus a downloadable JSON report. It does not approve, post or pay vendor bills, consult a vendor master or detect duplicate invoices against a ledger.

The pilot hypothesis is **$5 USD for one report** (not a subscription). Test it with an invited bookkeeper who already has PO and receipt data. Measure how many prepared reports are purchased, chargebacks/refunds, and the time saved versus manual review before offering a bulk plan or claiming a return on investment.

## No-charge demo

```sh
uv sync --frozen
uv run --frozen gunicorn --bind 127.0.0.1:8765 --timeout 60 'app.pilot:create_app()'
```

Open the app at `http://127.0.0.1:8765`. Use the built-in sample or download and upload both sample files, simulate payment, and download the report. The preview accepts only the provided invoice PDF, with preseeded extraction; it does not call Stripe or a model. To exercise the review outcome, reduce any received quantity in the sample JSON and upload it with the sample invoice. Do not upload real invoices to an evaluation or sandbox.

For a public synthetic demo, use `PILOT_MODE=demo PILOT_PUBLIC_DEMO=1` on an HTTPS host. It serves one reusable sample report without storing per-visitor reports. Uploads, Stripe and model calls are disabled. Keep its runtime data separate from the pilot.

For stable, free hosting of the **sample walkthrough only**, select **GitHub Actions** in the repository's **Settings → Pages** and run **Publish Invoice Match demo** against `main`. The workflow publishes static pages, sample downloads and a precomputed report from the matcher. It has no runtime, uploads, accounts or payments. The simulated checkout illustrates the pilot flow; it does not restrict access to the public sample report.

To build the same site locally into a new directory: `uv run --locked python -m scripts.export_invoice_match_demo /path/to/demo`.

## Stripe sandbox and invite-only production

1. On a host with persistent storage, serve the app behind HTTPS using the Gunicorn command above, with the port/interface appropriate to the host. Forward the HTTPS origin to the app, preserve the webhook body, limit upload size and rate-limit access and report routes at the proxy. Use a runtime and data directory restricted to the app's service account; reports contain invoice data. Do not use a private Devin preview URL for Stripe webhooks.
2. Start with `PILOT_MODE=stripe-test`. Set a stable random `PILOT_SESSION_KEY` (at least 32 characters), `PILOT_ACCESS_CODE` (at least 24), `PILOT_BASE_URL` (canonical HTTPS origin, no path), and `PILOT_DB` (SQLite path on the private, persistent volume). Use unique values and isolated databases per environment. Use one server instance; the pilot does not support a shared multi-instance database.
3. Supply `STRIPE_SECRET_KEY` from the sandbox via the host's secret store, preferably a restricted key with Checkout Sessions access. In the Stripe dashboard, register the sandbox endpoint `POST /stripe/webhook` for `checkout.session.completed` and store its signing secret as `STRIPE_WEBHOOK_SECRET`. Use a Stripe test card to verify the charge amount, cancellation/resume, payment after a lost browser redirect, webhook retries and re-opening the download. The app only exposes the report after matching its order, Checkout session, amount, currency and mode against a paid session from Stripe.
4. Before collecting money, an authorized representative must [activate the Stripe merchant account](https://dashboard.stripe.com/account/onboarding), configure payouts, and approve the hosting, extraction provider and any customer-facing release. Review sales tax, refund/support and privacy notice obligations for the actual business and users. Configure a reachable OpenAI-compatible vLLM endpoint via `VLLM_BASE_URL`, `VLLM_API_KEY` (if required) and `MODEL_NAME`; it must support the repository's structured-output settings. Validate extraction against representative invoices before inviting users. Existing project accuracy numbers are from synthetic records, not production invoices.
5. Only then switch the production environment to `PILOT_MODE=live` with the live key and live webhook signing secret. Use approved, scoped invitations, a published support/refund contact and a clearly disclosed data-processing policy. No live mode or merchant account is provisioned by this repository.

PDF and PO/receipt files are not intentionally retained by the app. In live mode, extracted invoice text is sent to the configured model endpoint and finished reports are retained for up to seven days. Install a daily job with the same runtime environment to run `uv run --frozen flask --app app.pilot purge-reports` even when no reports are prepared. Apply the retention policy to backups and provider logs too. Report history is available only in the same browser with current pilot access; there is no login or cross-device recovery. When the same browser submits identical documents, the pilot offers to reopen the existing report instead of paying again. The server limits live report attempts and copies across the pilot to 25 per UTC day. Support can handle suspected duplicate charges or refunds in the Stripe Dashboard; the app does not issue refunds.
