import discord
from discord import app_commands
from discord.ext import commands
import os
import logging

# Configure logging at the start
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('inmidradio')


class RadioBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        super().__init__(command_prefix='!', intents=intents)
        self.current_track = 0

    async def setup_hook(self):
        # Load and sort tracks alphabetically
        self.playlist = sorted(
            [f for f in os.listdir('./music') if f.endswith('.mp3')])
        logger.info(f"Found {len(self.playlist)} songs")

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")

    async def play_next(self, voice_client):
        if not voice_client.is_connected():
            return

        if self.playlist:
            # Play current track
            audio = discord.FFmpegPCMAudio(
                f'music/{self.playlist[self.current_track]}')

            def after_playing(error):
                if error:
                    logger.error(f"Error playing audio: {error}")
                else:
                    # Move to next track, loop back to start if at end
                    self.current_track = (
                        self.current_track + 1) % len(self.playlist)
                    # Schedule next track
                    self.loop.create_task(self.play_next(voice_client))

            voice_client.play(audio, after=after_playing)
            logger.info(f"Now playing: {self.playlist[self.current_track]}")


bot = RadioBot()


@bot.event
async def on_ready():
    logger.info(f'Bot is ready! Logged in as {bot.user}')


@bot.tree.command(name="play", description="Start playing music")
async def play(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message(
            "You need to be in a voice channel!"
        )

    channel = interaction.user.voice.channel

    try:
        voice_client = await channel.connect()
        await interaction.response.send_message("Starting playlist! 🎵")
        await bot.play_next(voice_client)
    except Exception as e:
        logger.error(f"Error connecting to voice: {e}")
        await interaction.response.send_message("Error starting playback!")


@bot.tree.command(name="stop", description="Stop playing music")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Stopped playing")
    else:
        await interaction.response.send_message("Not playing anything!")


@bot.tree.command(name="next", description="Skip to next track")
async def next_track(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        # This will trigger the after_playing callback
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipping to next track...")
    else:
        await interaction.response.send_message("Not playing anything!")

bot.run(os.environ['DISCORD_TOKEN'])
