# Launch Fix Checklist (P0/P1)

## P0 - Must Fix Before Production

- [ ] `backend/app/routers/auth.py`
  - `/api/auth/register/initiate`
  - `/api/auth/register`
  - `/api/auth/login`
  - `/api/auth/checkin`
  - Action: replace placeholder responses with real user lifecycle + persistent state.
  - Progress (2026-04-25): all listed endpoints above are now wired and contract-aligned with frontend (`initiate` email payload, `register` firebase_uid upsert, `login` JWT response, `checkin` daily idempotent credit grant).

- [ ] `backend/app/routers/billing.py`
  - `/api/billing/subscriptions/checkout`
  - `/api/billing/subscriptions/portal`
  - `/api/billing/subscriptions/current`
  - `/api/billing/credit-packs/checkout`
  - `/api/billing/history`
  - Action: remove mock URLs/status and connect to real billing provider data.
  - Progress (2026-04-25): all listed endpoints above are now wired; subscription + credit-pack checkout + history placeholders removed.

- [ ] `backend/app/routers/support.py`
  - `/api/billing/support`
  - `/api/billing/support/feedback`
  - `/admin/support-tickets`
  - Action: persist tickets, add admin workflow, and notification hooks.
  - Progress (2026-04-25): ticket persistence + admin resolve workflow now wired, endpoint contracts aligned to frontend payloads, Redis notification hooks added (`events:support` + `events:user:{id}`).

- [ ] `backend/app/routers/content.py` (legacy v1 placeholders)
  - `/api/v1/collections*`
  - Action: either deprecate/remove or bind to production-grade collection storage.
  - Progress (2026-04-25): deprecated with explicit `410 Gone` to prevent mock-success behavior in production; follow-up is v2 collection storage replacement.

- [ ] `backend/app/routers/story.py`
  - multiple story CRUD/start/resume placeholder returns
  - Action: align to `story_service` runtime state and remove static mock payloads.
  - Progress (2026-04-25): core read/start/resume/choice/progress and CRUD/node CRUD now wired to DB + `story_service`; added `story_service` replay/history helper methods (`get_play_history`, `get_next_play_index`, `increment_play_count`, `get_all_user_play_history`) to close runtime gaps.

- [ ] Frontend build blockers
  - `ScriptEditor / DagEditor / GroupChatPage / CreditsTab` TypeScript errors
  - Action: restore type-safe interfaces and ensure `npm run build` passes.
  - Progress (2026-04-25): blockers fixed; `npm run build` now passes (TS + Vite).

## P1 - High Priority

- [ ] TG Stars refund parity
  - Action: add Telegram Stars specific refund pipeline (not only Stripe `charge.refunded`).
  - Progress (2026-04-25): added Telegram refund terminal state + purchased-credit deduction path (`mark_telegram_stars_order_refunded`) and webhook mapping for `refunded/refund/chargeback/reversed`.

- [ ] Discover comments backend
  - `frontend/src/pages/DiscoverVideoFeedPage.tsx` currently UI preview mode.

- [ ] Full e2e customer journey test suite
  - auth -> create character -> chat -> media -> billing -> refund -> support.

## Done In This Iteration

- [x] Share reward feature (`+10 credit`) end-to-end
  - Backend claim API, idempotency table, migration script
  - Frontend share entry integration
  - Backend/frontend unit tests

- [x] Billing subscription API P0 subset
  - Replaced placeholder behavior for `/api/billing/subscriptions/checkout|portal|current|cancel|reactivate`
  - Aligned checkout payload with frontend contract (`tier + billing_period`)
  - Added focused backend tests: `backend/tests/test_billing_subscriptions.py` (6 passed)

- [x] Billing checkout/history P0 subset
  - Replaced placeholder behavior for `/api/billing/credit-packs/checkout|history`
  - Aligned credit-pack checkout payload with frontend contract (`pack_id`)
  - Added/extended focused backend tests: `backend/tests/test_billing_subscriptions.py` (8 passed)

- [x] Auth P0 subset
  - Replaced placeholder behavior for `/api/auth/register/initiate|register|login|checkin`
  - Added compatibility for `/api/auth/verify-email` (`token` payload) and `/api/auth/resend-verification`
  - Added focused backend tests: `backend/tests/test_auth_p0_flows.py` (7 passed)

- [x] Support ticket P0 subset
  - Replaced placeholder behavior for `/api/billing/support|/api/billing/support/feedback|/admin/support-tickets`
  - Added persistent service + table migration (`support_tickets`) and admin resolve action
  - Added focused backend tests: `backend/tests/test_support_p0.py` (6 passed)

- [x] Legacy v1 collections deprecation
  - Deprecated `/api/v1/collections*` endpoints with explicit `410 Gone`
  - Updated content tests for deprecation contract (`backend/tests/test_content.py -k collection` passed)
