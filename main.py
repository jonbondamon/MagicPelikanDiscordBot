import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# Bot class
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

# Instantiate bot
bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

# /list command
@bot.tree.command(name="list", description="Show a summary of the 5 most recent active threads in this channel")
async def list_threads(interaction: discord.Interaction):
    await interaction.response.defer()

    channel = interaction.channel
    if isinstance(channel, discord.Thread):
        channel = channel.parent

    if not isinstance(channel, discord.TextChannel):
        await interaction.followup.send("This command must be used in a text channel or thread.", ephemeral=True)
        return

    all_threads = await interaction.guild.active_threads()
    threads = [t for t in all_threads if t.parent_id == channel.id]
    threads = sorted(threads, key=lambda t: t.created_at or t.id, reverse=True)[:5]

    if not threads:
        await interaction.followup.send("There are no active threads in this channel.")
        return

    embed = discord.Embed(
        title=f"🧵 Last {len(threads)} Active Threads in #{channel.name}",
        color=discord.Color.gold()
    )

    for index, thread in enumerate(threads):
        # Creator and created time
        try:
            first_msg = [msg async for msg in thread.history(limit=1, oldest_first=True)][0]
            creator = first_msg.author.mention
            created_at = first_msg.created_at.strftime("%b %d, %Y @ %I:%M %p")
        except Exception:
            creator = "Unknown"
            created_at = "?"

        # Last updated time
        try:
            last_msg = [msg async for msg in thread.history(limit=1, oldest_first=False)][0]
            updated_at = last_msg.created_at.strftime("%b %d, %Y @ %I:%M %p")
        except Exception:
            updated_at = "?"

        # Participants
        messages = [m async for m in thread.history(limit=50)]
        participants = set(m.author.mention for m in messages if not m.author.bot)
        participants_display = ", ".join(list(participants)[:5])
        if len(participants) > 5:
            participants_display += f" and {len(participants) - 5} more..."
        participant_count = len(participants)

        # Thread link
        thread_url = f"https://discord.com/channels/{interaction.guild.id}/{thread.id}"

        embed.add_field(
            name=f"{thread_url}",
            value=(
                f"👤 **Created by:** {creator}\n"
                f"📅 **Created:** {created_at}\n"
                f"⏱ **Last updated:** {updated_at}\n"
                f"👥 **Participants ({participant_count}):** {participants_display or 'None'}"
            ),
            inline=False
        )

        # Spacer line after each thread (except last)
        if index < len(threads) - 1:
            embed.add_field(name="\u200b", value="\u200b", inline=False)

    await interaction.followup.send(embed=embed)

# /lock command
@bot.tree.command(name="lock", description="Lock the current thread and mark it as complete")
async def lock_thread(interaction: discord.Interaction):
    thread = interaction.channel
    if not isinstance(thread, discord.Thread):
        await interaction.response.send_message("You can only use this inside a thread.", ephemeral=True)
        return

    try:
        await thread.edit(locked=True)
        new_name = f"🟢 {thread.name.lstrip('🟡').strip()}"
        await thread.edit(name=new_name)
        await interaction.response.send_message("🔒 Thread locked and marked as complete.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to lock this thread.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Failed to lock the thread: {e}", ephemeral=True)

# /unlock command
@bot.tree.command(name="unlock", description="Unlock the current thread and mark it as in progress")
async def unlock_thread(interaction: discord.Interaction):
    thread = interaction.channel
    if not isinstance(thread, discord.Thread):
        await interaction.response.send_message("You can only use this inside a thread.", ephemeral=True)
        return

    try:
        await thread.edit(locked=False)
        new_name = f"🟡 {thread.name.lstrip('🟢').strip()}"
        await thread.edit(name=new_name)
        await interaction.response.send_message("🔓 Thread unlocked and marked as in progress.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to unlock this thread.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Failed to unlock the thread: {e}", ephemeral=True)

# Auto-switch icons based on locked status
@bot.event
async def on_thread_update(before: discord.Thread, after: discord.Thread):
    if before.locked != after.locked:
        target_channels = ["todos", "bugs", "qol"]
        yellow_icon = "🟡"
        green_icon = "🟢"

        if after.parent and after.parent.name.lower() in target_channels:
            current_name = after.name
            for icon in [yellow_icon, green_icon]:
                if current_name.startswith(icon):
                    current_name = current_name[len(icon):].strip()
            new_icon = green_icon if after.locked else yellow_icon
            new_name = f"{new_icon} {current_name}"

            try:
                await after.edit(name=new_name)
                print(f"Updated thread status icon: {new_name}")
            except discord.Forbidden:
                print(f"Missing permission to rename thread: {after.name}")
            except discord.HTTPException as e:
                print(f"Failed to rename thread: {e}")

# Add 🟡 to new threads
@bot.event
async def on_thread_create(thread: discord.Thread):
    target_channels = ["todos", "bugs", "qol"]
    yellow_icon = "🟡"

    if thread.parent and thread.parent.name.lower() in target_channels:
        if not thread.name.startswith(yellow_icon):
            new_name = f"{yellow_icon} {thread.name}"
            try:
                await thread.edit(name=new_name)
                print(f"Thread renamed to: {new_name}")
            except discord.Forbidden:
                print(f"Permission error: cannot rename thread {thread.name}")
            except discord.HTTPException as e:
                print(f"HTTP error when renaming thread: {e}")

# Run bot
bot.run(TOKEN)
