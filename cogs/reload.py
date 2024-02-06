import discord
from discord.ext import commands
from discord import app_commands
from helpers.checks import missingPermissions
from main import Config
from typing import Literal

# This cog is for reloading other cogs

config = Config.getMainInstance()

# --------- #

class Reload(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")

    @app_commands.command(
            name = "reload",
            description = "Reloads a cog")
    async def reload(self, interaction: discord.Interaction, cog: Literal["fixer", "utility", "quotes", "misc", "maps"]):
        if interaction.user.id == int(config.admin):
            try:
                await self.client.reload_extension(name = f"cogs.{cog}")
                await interaction.response.send_message(f"Successfully reloaded **{cog}**")
                print(f"Reloaded {cog}")
            except Exception as e:
                await interaction.response.send_message(f"Failed to reload **{cog}**! See error below\n```{e}```", ephemeral = True)
        else:
            await missingPermissions(interaction)

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Reload(client))