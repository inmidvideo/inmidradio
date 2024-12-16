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
