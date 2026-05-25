# Bot Commands

Handler manager registers top-level commands from decorator metadata.

## Top-Level Commands

- `*expert`
- `*program`
- `*contract`

Rule:

- Empty invocation path must show help, not generic error

## Expert Commands

- `*expert`
- `*expert list`
- `*expert add`
- `*expert edit <cccd|tên>`
- `*expert delete <cccd|tên>`
- `*expert find name <tên>`
- `*expert find id <cccd>`

Behavior notes:

- `edit` without argument opens selectable list
- `edit` and `delete` resolve by CCCD or name
- ambiguous matches produce resolution buttons
- list view is paginated

## Program Commands

- `*program`
- `*program list`
- `*program add`
- `*program <mã>`
- `*program find <mã>`
- `*program edit <mã>`
- `*program delete <mã>`

Behavior notes:

- unknown subcommand path falls back to code lookup
- program detail view includes button to list contracts under program
- list view is paginated

## Contract Commands

- `*contract`
- `*contract expert list year <YYYY>`

Behavior notes:

- `*contract` shows help
- only supported CLI path today is yearly expert contract listing
- yearly list is paginated

## Mention Rules

- If `MEZON_BOT_REQUIRE_MENTION=true`, bot ignores unmentioned messages
- When bot is mentioned, alias form without prefix works for top-level command names
- Mention-only example: `@Bot expert`

## Where Commands Live

- `app/services/bot/handlers/expert.py`
- `app/services/bot/handlers/program.py`
- command decorator: `app/services/bot/handlers/base.py`
