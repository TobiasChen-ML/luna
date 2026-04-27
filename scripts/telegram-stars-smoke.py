import argparse
import asyncio
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if not BACKEND_DIR.exists() and (REPO_ROOT / "app").exists():
    BACKEND_DIR = REPO_ROOT
sys.path.insert(0, str(BACKEND_DIR))


def _pass(message: str) -> None:
    print(f"[PASS] {message}")


def _info(message: str) -> None:
    print(f"[INFO] {message}")


def _fail(message: str) -> None:
    print(f"[FAIL] {message}")


def _telegram_api(bot_token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/{method}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if payload is not None else "GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Telegram API {method} failed: HTTP {exc.code} {body}") from exc
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 * attempt)
                continue
    raise RuntimeError(f"Telegram API {method} failed after retries: {last_error}") from last_error


def _signed_payload(payload: dict[str, Any], bot_token: str) -> dict[str, Any]:
    signed = dict(payload)
    sorted_items = sorted((key, value) for key, value in signed.items() if key != "hash" and value is not None)
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted_items)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    signed["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return signed


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Telegram Stars payment smoke test")
    parser.add_argument("--webhook-url", default="https://roxyclub.ai/api/billing/webhooks/telegram-stars")
    parser.add_argument("--bot-token", default=None)
    parser.add_argument("--webhook-secret", default=None)
    parser.add_argument("--keep-smoke-user", action="store_true")
    parser.add_argument("--skip-invoice-link", action="store_true")
    args = parser.parse_args()

    from app.core.config import get_config_value, get_settings
    from app.models.credit_transaction import CreditTransaction
    from app.models.user import User
    from app.routers import billing as billing_router
    from app.services.billing_service import BillingService
    from app.services.credit_service import credit_service

    settings = get_settings()
    bot_token = args.bot_token or await get_config_value("TELEGRAM_BOT_TOKEN") or settings.telegram_bot_token
    webhook_secret = (
        args.webhook_secret
        or await get_config_value("TELEGRAM_WEBHOOK_SECRET_TOKEN")
        or await get_config_value("TELEGRAM_STAR_GATEWAY_WEBHOOK_AUTH_TOKEN")
        or await get_config_value("TELEGRAM_BOT_WEBHOOK_SECRET")
    )

    if not bot_token:
        _fail("TELEGRAM_BOT_TOKEN is not configured")
        return 1

    webhook_info = _telegram_api(bot_token, "getWebhookInfo")
    if not webhook_info.get("ok"):
        _fail(f"getWebhookInfo returned not ok: {webhook_info}")
        return 1
    result = webhook_info.get("result", {})
    actual_url = result.get("url")
    if actual_url != args.webhook_url:
        _fail(f"Webhook URL mismatch: expected {args.webhook_url}, got {actual_url}")
        return 1
    if result.get("last_error_message"):
        _fail(f"Telegram reports webhook error: {result.get('last_error_message')}")
        return 1
    _pass(f"Telegram webhook configured: {actual_url}")
    _info(f"pending_update_count={result.get('pending_update_count', 0)}")

    billing = BillingService()
    user_id = f"smoke_telegram_stars_{uuid.uuid4().hex[:10]}"
    email = f"{user_id}@example.test"
    created_order_ids: list[str] = []

    with billing.db.transaction() as session:
        user = User(
            id=user_id,
            email=email,
            display_name="Telegram Stars Smoke",
            tier="free",
            credits=0.0,
            purchased_credits=0.0,
            monthly_credits=0.0,
        )
        session.add(user)
    _pass(f"Created smoke user {user_id}")

    class FakeRequest:
        def __init__(self, payload: dict[str, Any]):
            self._payload = payload

        async def json(self) -> dict[str, Any]:
            return self._payload

    async def post_webhook(payload: dict[str, Any]):
        body = payload
        secret_header = None
        if webhook_secret:
            secret_header = webhook_secret
        else:
            body = _signed_payload(payload, bot_token)
        return await billing_router.telegram_stars_webhook(
            FakeRequest(body),
            x_telegram_bot_api_secret_token=secret_header,
        )

    try:
        pack_order = await billing.create_telegram_stars_order(
            user_id=user_id,
            amount_stars=1,
            credits=7,
            pack_id="smoke_pack",
            product_type="credit_pack",
            title="Smoke Credit Pack",
            description="Smoke test credit pack",
            metadata={"source": "telegram-stars-smoke"},
        )
        pack_order_id = pack_order["order_id"]
        created_order_ids.append(pack_order_id)
        _pass(f"Created credit pack order {pack_order_id}")

        if not args.skip_invoice_link:
            invoice = await billing.create_telegram_stars_invoice_link(pack_order_id)
            if not invoice.get("invoice_link"):
                _fail("Invoice link response did not include invoice_link")
                return 1
            _pass("Generated Telegram Stars invoice link")
            _info(invoice["invoice_link"])

        subscription_order = await billing.create_telegram_stars_order(
            user_id=user_id,
            amount_stars=1,
            credits=11,
            pack_id="subscription_premium_1m",
            product_type="subscription",
            tier="premium",
            billing_period="1m",
            title="Smoke Subscription",
            description="Smoke test subscription",
            metadata={"source": "telegram-stars-smoke"},
        )
        subscription_order_id = subscription_order["order_id"]
        created_order_ids.append(subscription_order_id)

        failed_order = await billing.create_telegram_stars_order(
            user_id=user_id,
            amount_stars=1,
            credits=3,
            pack_id="smoke_failed",
            product_type="credit_pack",
        )
        failed_order_id = failed_order["order_id"]
        created_order_ids.append(failed_order_id)

        cancelled_order = await billing.create_telegram_stars_order(
            user_id=user_id,
            amount_stars=1,
            credits=3,
            pack_id="smoke_cancelled",
            product_type="credit_pack",
        )
        cancelled_order_id = cancelled_order["order_id"]
        created_order_ids.append(cancelled_order_id)

        billing_router.billing_svc = billing
        _pass("Created subscription, failed, and cancelled smoke orders")

        paid_payload = {
            "message": {
                "successful_payment": {
                    "telegram_payment_charge_id": f"smoke_charge_{pack_order_id}",
                    "invoice_payload": f"stars:{pack_order_id}",
                }
            },
            "auth_date": int(time.time()),
        }
        await post_webhook(paid_payload)
        balance = await credit_service.get_balance(user_id)
        if balance["purchased"] < 7 or balance["total"] < 7:
            _fail(f"credit pack paid webhook did not add credits: {balance}")
            return 1
        _pass(f"Paid webhook added purchased credits: total={balance['total']} purchased={balance['purchased']}")

        await post_webhook(
            {
                "status": "refunded",
                "order_id": pack_order_id,
                "auth_date": int(time.time()),
            }
        )
        balance = await credit_service.get_balance(user_id)
        if balance["purchased"] != 0 or balance["total"] != 0:
            _fail(f"refund webhook did not deduct purchased credits: {balance}")
            return 1
        _pass("Refunded webhook deducted purchased credits")

        await post_webhook(
            {
                "status": "paid",
                "order_id": subscription_order_id,
                "charge_id": f"smoke_charge_{subscription_order_id}",
                "auth_date": int(time.time()),
            }
        )
        balance = await credit_service.get_balance(user_id)
        current = await billing.get_current_subscription(user_id)
        if balance["monthly"] < 11 or current["tier"] != "premium" or not current["is_active"]:
            _fail(f"subscription paid webhook did not activate subscription: balance={balance}, current={current}")
            return 1
        _pass("Subscription paid webhook activated premium and added monthly credits")

        await post_webhook(
            {
                "status": "refunded",
                "order_id": subscription_order_id,
                "auth_date": int(time.time()),
            }
        )
        balance = await credit_service.get_balance(user_id)
        current = await billing.get_current_subscription(user_id)
        if balance["monthly"] != 0 or current["tier"] != "free" or current["is_active"]:
            _fail(f"subscription refund did not revoke subscription: balance={balance}, current={current}")
            return 1
        _pass("Subscription refunded webhook revoked premium and deducted monthly credits")

        await post_webhook(
            {
                "status": "failed",
                "order_id": failed_order_id,
                "auth_date": int(time.time()),
            }
        )
        failed_state = await billing.get_telegram_stars_order(failed_order_id)
        if failed_state.get("status") != "failed":
            _fail(f"failed webhook did not mark order failed: {failed_state}")
            return 1
        _pass("Failed webhook marked order failed")

        await post_webhook(
            {
                "status": "cancelled",
                "order_id": cancelled_order_id,
                "auth_date": int(time.time()),
            }
        )
        cancelled_state = await billing.get_telegram_stars_order(cancelled_order_id)
        if cancelled_state.get("status") != "cancelled":
            _fail(f"cancelled webhook did not mark order cancelled: {cancelled_state}")
            return 1
        _pass("Cancelled webhook marked order cancelled")

        _pass("Telegram Stars smoke test completed")
        return 0
    finally:
        if args.keep_smoke_user:
            _info(f"Keeping smoke user and orders for inspection: {user_id}")
        else:
            with billing.db.transaction() as session:
                session.query(CreditTransaction).filter(CreditTransaction.user_id == user_id).delete()
                session.query(User).filter(User.id == user_id).delete()
            for order_id in created_order_ids:
                try:
                    await billing.redis.delete(billing._telegram_stars_order_key(order_id))
                except Exception as exc:
                    _info(f"Could not delete Redis order {order_id}: {exc}")
            _pass("Cleaned smoke user, transactions, and Redis orders")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
