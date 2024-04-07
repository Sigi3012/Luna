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
    
    # Append "private." to load, unload or reload private cogs
    @commands.is_owner()
    @commands.command()
    async def load(self, ctx: commands.Context, cog: str):
        try:
            await self.client.load_extension(name = f"cogs.{cog}")
            await ctx.reply(f"Successfully loaded **{cog}**")
            print(f"Successfully loaded {cog}")
        except Exception as e:
            await ctx.reply(f"Failed to load **{cog}**! See error below\n```{e}```")
    
    @commands.is_owner()
    @commands.command()
    async def unload(self, ctx: commands.Context, cog: str):
        if cog == "reload":
            await ctx.reply("You cannot unload this cog as it is a core cog")
            return
        
        try:
            await self.client.unload_extension(name = f"cogs.{cog}")
            await ctx.reply(f"Successfully unloaded **{cog}**")
            print(f"Successfully unloaded {cog}")
        except Exception as e:
            await ctx.reply(f"Failed to unload **{cog}**! See error below\n```{e}```")
    
    @commands.is_owner()
    @commands.command()
    async def reload(self, ctx: commands.Context, cog):
        if cog == "reload":
            await ctx.reply("You cannot unload this cog as it is a core cog")
            return
        
        try:
            await self.client.reload_extension(name = f"cogs.{cog}")
            await ctx.reply(f"Successfully reloaded **{cog}**", ephemeral = True)
            print(f"Successfully reloaded {cog}")
        except Exception as e:
            await ctx.reply(f"Failed to reload **{cog}**! See error below\n```{e}```")

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Reload(client))