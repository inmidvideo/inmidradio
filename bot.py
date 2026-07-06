import logging
import os
import sys

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from atc import is_valid_feed, normalize_feed, parse_pls, pls_url, search_url
from playlist import load_playlist, next_index

# Configure logging at the start
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("inmidradio")

# LiveATC's /play/ endpoint sits behind a Cloudflare "managed challenge" that
# 403s minimal user-agents (e.g. a bare "Mozilla/5.0"). A full, realistic browser
# UA passes it, so use one for both the playlist fetch and the ffmpeg stream pull.
BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# ffmpeg input options for live network streams: follow redirects and reconnect
# on transient drops so an ATC feed keeps playing across brief network hiccups.
ATC_FFMPEG_OPTIONS = (
    f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -user_agent "{BROWSER_UA}"'
)


class RadioBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.current_track = 0
        self.mode = None  # "music", "atc", or None

    async def setup_hook(self):
        self.playlist = load_playlist("./music")
        logger.info(f"Found {len(self.playlist)} songs")

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")

    async def play_next(self, voice_client):
        if self.mode != "music" or not voice_client.is_connected():
            return

        if self.playlist:
            # Play current track
            audio = discord.FFmpegPCMAudio(f"music/{self.playlist[self.current_track]}")

            def after_playing(error):
                if error:
                    logger.error(f"Error playing audio: {error}")
                elif self.mode == "music":
                    # Move to next track, loop back to start if at end
                    self.current_track = next_index(self.current_track, len(self.playlist))
                    # Schedule next track
                    self.loop.create_task(self.play_next(voice_client))

            voice_client.play(audio, after=after_playing)
            logger.info(f"Now playing: {self.playlist[self.current_track]}")

    async def resolve_atc_stream(self, feed):
        """Fetch the LiveATC .pls for ``feed`` and return its stream URL, or None."""
        url = pls_url(feed)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": BROWSER_UA},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return None
                    text = await resp.text()
        except Exception as e:
            logger.error(f"Error fetching ATC playlist for {feed}: {e}")
            return None
        return parse_pls(text)


bot = RadioBot()


@bot.event
async def on_ready():
    logger.info(f"Bot is ready! Logged in as {bot.user}")


@bot.tree.command(name="play", description="Start playing music")
async def play(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("You need to be in a voice channel!")

    channel = interaction.user.voice.channel

    try:
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        if bot.mode == "music" and voice_client.is_playing():
            return await interaction.response.send_message("Already playing the playlist! 🎵")

        # Set the mode before stopping so a switch away from ATC doesn't get
        # resurrected by a stale callback.
        was_atc = bot.mode == "atc"
        bot.mode = "music"
        if was_atc and voice_client.is_playing():
            voice_client.stop()
        await interaction.response.send_message("Starting playlist! 🎵")
        await bot.play_next(voice_client)
    except Exception as e:
        logger.error(f"Error connecting to voice: {e}")
        await interaction.response.send_message("Error starting playback!")


@bot.tree.command(name="stop", description="Stop playing music or ATC audio")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        # Clear the mode before stopping so the music loop doesn't reschedule.
        bot.mode = None
        interaction.guild.voice_client.stop()
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Stopped playing")
    else:
        await interaction.response.send_message("Not playing anything!")


@bot.tree.command(name="next", description="Skip to next track")
async def next_track(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if bot.mode == "music" and voice_client and voice_client.is_playing():
        # This will trigger the after_playing callback
        voice_client.stop()
        await interaction.response.send_message("Skipping to next track...")
    else:
        await interaction.response.send_message("Not playing the playlist!")


@bot.tree.command(name="atc", description="Play a live LiveATC feed (e.g. kord1s1_atis)")
@app_commands.describe(feed="LiveATC feed ID, e.g. kord1s1_atis — find IDs at liveatc.net")
async def atc(interaction: discord.Interaction, feed: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("You need to be in a voice channel!")

    feed = normalize_feed(feed)
    if not is_valid_feed(feed):
        return await interaction.response.send_message(
            "Invalid feed ID. Use letters, numbers, and underscores, e.g. `kord1s1_atis`."
        )

    # Resolving the feed makes a network request, so defer to avoid the 3s timeout.
    await interaction.response.defer()

    stream_url = await bot.resolve_atc_stream(feed)
    if not stream_url:
        return await interaction.followup.send(
            f"No live feed found for `{feed}`. Find the exact feed ID at <{search_url(feed)}>."
        )

    channel = interaction.user.voice.channel
    try:
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        # Set the mode before stopping so the music loop can't resurrect itself.
        bot.mode = "atc"
        if voice_client.is_playing():
            voice_client.stop()

        source = discord.FFmpegPCMAudio(stream_url, before_options=ATC_FFMPEG_OPTIONS)
        voice_client.play(
            source,
            after=lambda e: logger.error(f"ATC stream error: {e}") if e else None,
        )
        logger.info(f"Now playing ATC feed: {feed}")
        await interaction.followup.send(f"📡 Playing live ATC feed `{feed}`")
    except Exception as e:
        logger.error(f"Error starting ATC feed: {e}")
        await interaction.followup.send("Error starting the ATC feed!")


def main():
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN is not set. Copy .env.example to .env and add your token.")
        sys.exit(1)
    bot.run(token)


if __name__ == "__main__":
    main()
