from discord.ext import commands
from discord import app_commands
from main import Config
import discord
import time, datetime

# This cog is for the /status command and it cannot be reloaded (unless the bug is fixed)
# The reason it has it's own cog is because the command breaks upon being reloaded (make a PR if you know how to fix it!)
# discord.app_commands.errors.CommandInvokeError: Command 'status' raised an exception: TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'

config = Config.getMainInstance()

# --------- #

class Status(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.startUptime = None

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")
        self.startUptime = time.time()

    @app_commands.command(
            name = "status",
            description = "shows the status of the bot")
    async def status(self, interaction: discord.Interaction):
        uptime = str(datetime.timedelta(seconds=int(round(time.time() - self.startUptime))))
        def enabled():
            if config.enabled:
                # 🟩
                return("\U0001F7E9")
            else:
                # 🟥
                return("\U0001F7E5")
        
        embed = discord.Embed(
            title="Status",
            description=f"Enabled: {enabled()}\nTotal links fixed: {config.totalFixed}\nUptime: {uptime}\nAdmin: <@{config.admin}>",
            colour=0x00b0f4,
            timestamp=datetime.datetime.now())
        embed.set_footer(text="Made by @.Sigi")
        await interaction.response.send_message(embed=embed)

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Status(client))