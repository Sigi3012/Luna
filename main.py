import discord
from discord.ext import commands
import helpers.checks as checks
import json
import time
import platform

with open("config.json", "r") as file:
    config = json.load(file)

checks.check()

# --------- #

class embedFixer(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = "-",
            intents = discord.Intents().all()
        )
        self.cogslist = ["fixer", "utility", "reload", "status"]

    async def on_ready(self):
        syncedCommands = await self.tree.sync()
        print(f"Logged in as {self.user.name}")
        print(f"Python version: {str(platform.python_version())}")
        print(f"Discord.py version: {discord.__version__}")
        print(f"Synced {str(len(syncedCommands))} commands")
        global startUptime
        startUptime = time.time()
        
    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(f"cogs.{ext}")

client = embedFixer()

# --------- #

if __name__ == "__main__":
    client.run(config["token"])