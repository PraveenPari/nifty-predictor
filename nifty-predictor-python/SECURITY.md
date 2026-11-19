# Security Policy — Secrets Handling (Pro Standard)

## The rule

**Secrets live ONLY in environment variables / the hosting provider's
Secrets dashboard. They NEVER appear in code, logs, API responses, or git.**

This repo previously contained a hardcoded Breeze API key. It has been
removed. If you cloned the repo before the fix:

1. **Rotate immediately**: revoke the old key in the ICICI Direct developer
   portal and generate a new API key + secret. Anything once committed to git
   must be treated as compromised (it stays in history forever).
2. Pull the latest code and set secrets via `.env` (local) or your host's
   Secrets dashboard (production).

## How secrets flow

```
Hosting Secrets dashboard / .env (git-ignored)
        │
        ▼
secrets_manager.py  (single choke point: reads env, validates, masks)
        │
        ├── pro_config/api_config.py  (no hardcoded fallbacks)
        ├── breeze_manager.py         (masked logging only)
        └── app.py /api/status        (exposes booleans, never values)
```

## Guarantees

- `secrets_manager.get_secret()` returns `""` for missing **or placeholder**
  values (`your_breeze_api_key`, `changeme`, …).
- Nothing ever prints a secret: logging uses `mask()` → `1L99****445`.
- `/api/status` and `/healthz` never expose credential values. Status can include non-secret connection flags and the startup market quote.
- Missing Breeze secrets ⇒ Breeze features disable cleanly and the app falls
  back to Yahoo Finance. Nothing crashes.
- Breeze session tokens expire. When expired, update the token in server secrets and redeploy; status reports a safe error code.

## Local development

```bash
cd nifty-predictor-python
cp .env.example .env        # then edit .env with real values
python app.py
```

`.env` is covered by the root `.gitignore` (`**/.env`) — verify with
`git status` that it never shows up.

## Production hosting

Set `BREEZE_API_KEY`, `BREEZE_SECRET_KEY`, `BREEZE_SESSION_TOKEN`, and
`SECRET_KEY` in your provider's **Environment / Secrets** panel
(Render → Environment, Railway → Variables). Never bake them into the
Docker image or commit them. See `DEPLOYMENT_GUIDE.md`.
