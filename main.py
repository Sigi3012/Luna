import discord
from discord.ext import commands
import helpers.checks as checks
from helpers.configSetup import Config
import signal
import platform
import sys
import os

# --------- #

config = Config.getMainInstance()

class embedFixer(commands.Bot):
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

    async def setup_hook(self):
        for ext in os.listdir("./cogs"):
            if ext.endswith(".py"):
                await self.load_extension(f"cogs.{ext[:-3]}")

client = embedFixer()

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
