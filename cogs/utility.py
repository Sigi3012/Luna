import discord
from discord.ext import commands
from discord import app_commands
from helpers.checks import missingPermissions
from main import Config
from datetime import datetime
import time

# This cog is for general commands eg. shutdown, toggle, status

config = Config.getMainInstance()

def currentTime():
    return time.strftime("%H:%M:%S", time.localtime())

# --------- #

class Utility(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")
    
    # --------- #

    @app_commands.command(
        name = "toggle",
        description = "This enables or disables the link fixer")
    async def togglefixer(self, interaction):
        if interaction.user.id == int(config.admin):
            config.toggle()
            await interaction.response.send_message(f"Toggled to {config.enabled}", ephemeral=True)
            print(f"Toggled to: {config.enabled}@{currentTime()}")
        else:
            await missingPermissions(interaction)

    # --------- #

    @app_commands.command(
        name = "shutdown",
        description = "turns off the bot!")
    async def shutdown(self, interaction):
        if interaction.user.id == int(config.admin):
            await interaction.response.send_message("Shutting down...", delete_after=3.0, ephemeral=True)
            print(f"Bot offline@{currentTime()}")
            config.save()
            await self.client.close()
        else:
            await missingPermissions(interaction)

    # --------- #

    @app_commands.command(
        name = "sync",
        description = "syncs new commands"
    )
    async def sync(self, interaction):
        if interaction.user.id == int(config.admin):
            syncedCommands = await self.client.tree.sync()
            names = []
            for synced in syncedCommands:
                names.append(synced.name)
            await interaction.response.send_message(f"Synced {str(len(syncedCommands))} commands. {names}")
        else:
            await missingPermissions(interaction)

    @app_commands.command(
        name = "ping",
        description = "Sends the latency of the bot!"
    )
    async def ping(self, interaction):
        latency = self.client.latency
        await interaction.response.send_message(f"My latency is: {round(latency, 1)}ms!")
     
    @commands.command()
    async def userbanner(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            member = ctx.author
        
        member = await self.client.fetch_user(member.id)

        if member.banner is None:
            await ctx.reply(content = f"<@{member.id}> has no banner!")
        else:
            embed = discord.Embed(
                timestamp = datetime.now()
            )
            embed.set_image(url = member.banner.url)
            await ctx.reply(embed = embed)
            
    @commands.command()
    async def userpfp(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            member = ctx.author
      
        if member.avatar is None:
            await ctx.reply(content = f"<@{member.id}> has a default pfp!")
        else:
            embed = discord.Embed(
                timestamp = datetime.now()
            )
            embed.set_image(url = member.avatar.url)
            await ctx.reply(embed = embed)

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Utility(client))