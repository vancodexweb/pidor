# Telegram Booking Platform

A multi-bot Telegram platform for accepting requests and booking clients.

A single **main constructor bot** lets any user connect their own Telegram bot
(created via [@BotFather](https://t.me/BotFather)) by pasting its token. Every
connected **child bot** then runs its own independent booking flow: the owner
adds free time slots through an admin panel, and clients pick a date and time,
leave their name and phone number, and get an instant confirmation — with the
owner notified immediately.

One backend process serves all of it. There is no per-bot container, no
webhook, no reverse proxy, no domain — just Telegram long polling, PostgreSQL,
and Docker.

## Requirements

- A VPS (or any machine) with Docker and Docker Compose installed.
- A Telegram bot token for the main constructor bot, from [@BotFather](https://t.me/BotFather).

## Setup

```bash
cp .env.example .env
```

Open `.env` and fill in:

- `MAIN_BOT_TOKEN` — the token of your main constructor bot.
- `POSTGRES_PASSWORD` — pick a real password.
- `ENCRYPTION_KEY` — a Fernet key used to encrypt every connected bot's token
  at rest. Generate one with:

  ```bash
  docker compose run --rm app python -c "from app.core.security import generate_encryption_key; print(generate_encryption_key())"
  ```

  Keep this key secret and never change it once bots are connected — doing so
  makes their already-stored tokens permanently undecryptable.

## Run

```bash
docker compose up -d --build
```

This builds the app image, starts PostgreSQL, waits for it to be healthy,
runs database migrations automatically, and starts the bot. That's it.

## Verify

```bash
docker compose ps
```

Both `app` and `postgres` should show as `running`/`healthy`.

## Logs

```bash
docker compose logs -f app
```

## Restart

```bash
docker compose restart
```

## Stop

```bash
docker compose down
```

(Add `-v` only if you also want to delete the database volume — this is
destructive and removes all bots, bookings, and settings.)

## Migrations

Migrations run automatically on every `docker compose up`. To run them
manually (e.g. after pulling a new version with new migrations, without a
full restart):

```bash
docker compose exec app alembic upgrade head
```

## Backup and restore

Back up the whole database to a file on the host:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > backup.sql
```

Restore it into a fresh database:

```bash
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < backup.sql
```

(`$POSTGRES_USER` / `$POSTGRES_DB` are the values you set in `.env` — either
export them into your shell first, or substitute them directly.)

## Deploying to a fresh VPS

1. Get an Ubuntu VPS.
2. Install Docker: `curl -fsSL https://get.docker.com | sh` (or follow
   [Docker's official install guide](https://docs.docker.com/engine/install/ubuntu/)).
3. Upload this project folder to the VPS (`git clone`, `scp`, or any method
   you like).
4. `cp .env.example .env` and fill it in as described above.
5. `docker compose up -d --build`
6. `docker compose ps` to confirm both containers are healthy.
7. `docker compose logs -f app` to watch it start up.

No Nginx, no domain, no SSL, no reverse proxy — the bot talks to Telegram
directly over polling. An HTTP API and a web panel can be layered on top
later without touching this deployment model.

## Using it

1. Open your main bot in Telegram and send `/start`.
2. Tap **➕ Создать бота**, follow the instructions to get a token from
   @BotFather, and paste it in.
3. The new bot starts running immediately. Open it and tap
   **👩‍💼 Админ-панель** (visible only to you, the owner) to set your
   welcome text, sticker/image, button labels, and timezone, and to add your
   free time slots.
4. Share the child bot's link with clients. They pick a free slot, leave
   their name and phone number, confirm, and you get notified instantly.
5. Manage all your connected bots (pause, resume, disconnect) from
   **🤖 Мои боты** in the main bot.

## Architecture notes

- **Multi-bot isolation**: every child bot runs as its own `asyncio.Task`
  wrapping an independent `aiogram.Bot` + `Dispatcher` pair, built fresh by
  `BotManager` (`app/services/bot_manager.py`). One bot crashing, being
  stopped, or being disconnected never touches any other bot's polling loop
  or FSM state. On startup, `BotManager.restore_bots()` reloads every active
  bot from the database and resumes polling; a failure restoring one bot is
  logged and skipped rather than blocking the rest.
- **Per-bot context**: `BotContextMiddleware` resolves which child bot an
  update belongs to straight from the token (`Bot.id`, no extra API call),
  loads that bot's row and settings, and injects them into every handler.
  Admin actions are additionally gated by an `IsOwner` filter that checks the
  sender's Telegram ID against the bot's `owner_id` on every request — never
  trusting callback data alone.
- **No double-booking**: `BookingService.create_booking` takes a
  `SELECT ... FOR UPDATE` row lock on the slot inside the same transaction as
  the insert, and a partial unique index
  (`bookings(slot_id) WHERE status = 'confirmed'`) backstops it at the
  database level. Verified under 10 concurrent booking attempts for the same
  slot: exactly one succeeds, the rest are cleanly rejected.
- **Token security**: connected bot tokens are encrypted with Fernet before
  being stored, decrypted only in memory when starting a poll, and never
  logged or echoed back to the user. The Telegram message containing a raw
  token is deleted immediately after being read.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

These cover the pure business-logic utilities (phone normalization, token
encryption, date/time parsing). The double-booking and full booking-flow
logic were additionally verified against a real PostgreSQL instance during
development.
