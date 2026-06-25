# Operations

## Environment Notes

- `.env` is loaded with override behavior
- Required keys: `APP_ENV`, `DB_URI`, `MEZON_CLIENT_ID`, `MEZON_API_KEY`
- Optional S3 keys live in `app/core/settings/app.py`
- `APP_ENV=dev` enables Swagger and ReDoc

## Local Docker

Database only:

```bash
docker compose -f docker-compose.db.yml up -d db
```

Full stack:

```bash
docker compose up
```

Current compose facts:

- PostgreSQL database name: `ips-bot`
- app command runs migrations before server start
- app bind: `0.0.0.0:8000`

## Container Image Notes

`Dockerfile`:

- uses `uv sync --frozen --no-dev` in builder stage
- copies `.venv` into runtime image
- copies `app/`, `run.py`, `alembic.ini`, and `template/`
- default command does not auto-run migrations

If deployment needs schema migration on boot, add explicit migration step outside or before app start.

## HTTP Checks

- Health: `GET /api/v1/health`
- Bot status: `GET /api/v1/bot/status`

Expected health payload:

```json
{
  "status": "ok",
  "version": "0.0.1"
}
```

## Troubleshooting

### Bot not responding

- verify process started without Mezon login error
- verify bot added to target Mezon server/channel
- verify mention requirement setting
- verify command prefix or mention alias path

### Database mismatch

- confirm `DB_URI` database name matches real database
- local defaults in repo use `ips-bot`

### Word export issues

- verify `template/Template_HDCG.docx` exists
- verify `template/Template_BBNT.docx` exists
- verify deployment artifact includes `template/`

### SMB local upload issues

- verify SMB share folder path and system write accessibility
- if SMB settings absent, fallback to Mezon default upload will be used
