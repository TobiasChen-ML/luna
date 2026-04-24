# Roxy Production Runbook

Last updated: 2026-04-24

## 1. Pre-Release

- Confirm CI is green on target commit (`backend-test`, `frontend-test`, `frontend-e2e-smoke`, `docker-build`).
- Freeze release artifacts (image tags and frontend static build version).
- Verify production environment variables are complete and non-default.
- Confirm DB backup exists and can be restored.
- Confirm on-call rotation and communication channel are active.

## 2. Deployment Steps

1. Announce deployment start in the on-call channel.
2. Deploy backend.
3. Run database migrations.
4. Deploy frontend.
5. Validate health checks:
   - `GET /health`
   - `GET /api/inference/system/health`
   - `GET /api/images/callbacks/health`
6. Run smoke script:
   - `powershell -ExecutionPolicy Bypass -File scripts/go-live-smoke.ps1 -BaseUrl https://<prod-domain>`
7. Run webhook reachability check:
   - `powershell -ExecutionPolicy Bypass -File scripts/webhook-reachability-check.ps1 -BaseUrl https://<prod-domain>`
8. Verify first user flows:
   - Login and session refresh.
   - Chat request/response.
   - One real payment callback end-to-end.

## 3. Rollback Steps

1. Announce rollback start.
2. Roll back frontend to previous version.
3. Roll back backend to previous image tag.
4. If migration is not backward compatible, execute DB rollback plan.
5. Re-run health checks and smoke script.
6. Post incident summary with timeline and root cause.

## 4. Incident Contacts

- Release owner: `TODO`
- Backend owner: `TODO`
- Frontend owner: `TODO`
- Billing owner: `TODO`
- On-call channel: `TODO`
