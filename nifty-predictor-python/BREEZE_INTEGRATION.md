# Breeze market data

The dashboard uses the read-only [ICICI Breeze REST API](https://api.icicidirect.com/breezeapi/documents/index.html): customer details to exchange the daily `apisession`, signed quotes and option chain, and historical charts v2. It does **not** subscribe to Breeze tick-by-tick WebSocket streams; quotes are fetched on demand and cached for five seconds. The broker's last trade time, when supplied, is shown on Connect. A quote returned outside market hours may be the last traded price rather than a current trade.

Configure `BREEZE_API_KEY` and `BREEZE_SECRET_KEY` as server secrets, then use the dashboard's Breeze login and Connect controls. Never paste credentials or tokens into logs, issues, or chat. A successfully authenticated session is held in one worker's memory and is lost on restart, redeploy, or replacement; reconnect after that happens. This deployment is configured for one worker. A multi-worker deployment requires a secure shared session mechanism, which is not provided here.

The Python SDK 1.0.69 downloads SecurityMaster.zip on import, before `generate_session()` runs. The dashboard's Breeze REST client avoids importing that SDK because quotes/history/option chain don't require the security master. Other standalone scripts may still use the SDK. All HTTP calls use a requests socket timeout; this is not a guarantee of a total wall-clock deadline.

Login success does not necessarily imply quote success. The Connect dialog explicitly warns if the quote probe failed, and `/readyz` reports the actual source used by the hybrid price path. Demo mode takes priority over all real feeds. Neither local mocked tests nor a successful deployment verifies a live broker session: confirm a fresh quote and its last-trade time during market hours.

Run offline contract tests from this directory:

```sh
python -m unittest discover -s tests -p 'test_breeze_rest_integration.py' -v
```
