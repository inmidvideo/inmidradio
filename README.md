# inmidradio

A Discord bot that streams mp3s in the `music` folder to a voice channel.

## Getting Started

1. Create a "New Application" in the [Discord Developer Portal](https://discord.com/developers/applications)
2. On the "OAuth2" page, select the `bot` and `application.commands` "Scopes", and the `Send Messages`, `Connect`, and `Speak` "Bot Permissions"
3. Use the "Generated URL" below to add the bot to your guild
4. Copy `.env.example` to `.env`, add `DISCORD_TOKEN` from the "Bot" page
5. `docker compose up --build -d` to start
6. Join a voice channel, then use `/play`, `/next`, or `/stop` in any text channel
7. `docker compose logs -f bot` to view logs
8. `docker compose down` to stop

## Local development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.
You'll also need [ffmpeg](https://ffmpeg.org/) on your `PATH`.

```bash
uv sync                          # create the venv and install deps
uv run ruff check .              # lint
uv run ruff format .             # format
uv run pytest                    # run tests
DISCORD_TOKEN=... uv run bot.py  # run the bot locally
```

CI runs the lint, format, and test steps on every push and pull request.
