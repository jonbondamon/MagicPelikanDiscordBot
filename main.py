import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.threads = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

@bot.tree.command(name="list", description="List all active threads in this channel")
async def list_threads(interaction: discord.Interaction):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("This command must be used in a text channel.", ephemeral=True)
        return

    threads = await channel.threads()
    if not threads:
        await interaction.response.send_message("There are no active threads in this channel.")
        return

    thread_list = "\n".join(f"• {thread.name}" for thread in threads)
    await interaction.response.send_message(f"🧵 Active threads:\n{thread_list}")

# Run the bot
import os
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
