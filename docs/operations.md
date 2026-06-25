# Operations

## Environment Notes

- `.env` is loaded with override behavior
- Required keys: `APP_ENV`, `DB_URI`, `MEZON_CLIENT_ID`, `MEZON_API_KEY`
- Optional SMB keys live in `app/core/settings/app.py`
- `APP_ENV=dev` enables Swagger and ReDoc

## Native Deployment

Deploy natively using the provided automation scripts:

### Linux / macOS

```bash
chmod +x deploy.sh
./deploy.sh
```

### Windows (PowerShell)

```powershell
.\deploy.ps1
```

Both scripts will automatically:
1. Load environment variables from `.env.prod`.
2. Sync the dependencies using `uv`.
3. Run Alembic migrations on the SQLite database.
4. Launch the FastAPI bot natively.

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
- verify mention requirement setting (`MEZON_BOT_REQUIRE_MENTION`)
- verify command prefix or mention alias path

### Database issues (SQLite)

- Confirm `DB_URI` starts with `sqlite+aiosqlite:///` followed by the filename (e.g. `ips-bot.db`).
- Check file system permissions in the folder containing `ips-bot.db`. The application must have read/write access.
- Run `uv run alembic upgrade head` manually if schema tables are missing.

### Word export issues

- verify `template/Template_HDCG.docx` exists
- verify `template/Template_BBNT.docx` exists

### SMB local upload issues

- verify SMB share folder path and system write accessibility
- if SMB settings absent, fallback to Mezon default upload will be used
