import discord
from discord.ext import commands
import helpers.checks as checks
from helpers.configSetup import Config
from helpers.database import createTables
import signal
import platform
import sys
import os

# --------- #

config = Config.getMainInstance()

class Luna(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = "-",
            intents = discord.Intents().all()
        )

    async def on_ready(self):
        print(f"Logged in as {self.user.name}")
        print(f"Python version: {str(platform.python_version())}")
        print(f"Discord.py version: {discord.__version__}")
        for key, value in vars(config).items():
            print(f"{key}: {value}")
            
        await createTables()
        
        activity = discord.Game("Watching for links...")
        await client.change_presence(status = discord.Status.online, activity = activity)
        print(activity)

    async def setup_hook(self):
        for ext in os.listdir("./cogs"):
            if ext.endswith(".py"):
                await self.load_extension(f"cogs.{ext[:-3]}")
        if config.qoutechannelid == "":
            await self.unload_extension("cogs.quotes")

client = Luna()

# --------- #

if __name__ == "__main__":
    if checks.check() == False:
        exit()
    else:
        pass

    config.load()
    client.run(config.token)

def signal_handler(filler, filler2):
    print("\n\nImproper shutdown please use /shutdown instead.")
    config.save()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
