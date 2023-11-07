import discord
from discord.ext import commands
from discord import app_commands
from helpers.checks import missingPermissions
from typing import Literal
from pathlib import Path
import json

# This cog is for reloading other cogs

currentDir = Path(__file__).resolve().parent
parrent = currentDir.parent
configLocation = parrent / "config.json"

with open(configLocation, "r") as file:
    config = json.load(file)

# --------- #

class Reload(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
            name = "reload",
            description = "Reloads a cog")
    async def reload(self, interaction: discord.Interaction, cog: Literal["fixer", "utility"]):
        if interaction.user.id == int(config["admin"]):
            try:
                await self.client.reload_extension(name = f"cogs.{cog}")
                await interaction.response.send_message(f"Successfully reloaded **{cog}**")
            except Exception as e:
                await interaction.response.send_message(f"Failed to reload **{cog}**! See error below\n```{e}```", ephemeral = True)
        else:
            await missingPermissions(interaction)

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Reload(client))