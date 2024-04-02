import discord
from discord import app_commands, ui
from discord.ext import commands

from main import Config
from helpers.checks import missingPermissions

from typing import Literal

config = Config.getMainInstance()

remoteHost: str = None
secretKey: str = None
enabled: bool = False
channel: int = 0

# --------- #

class InputForm(ui.Modal, title = "Generate an image!"):
    pass

class SetupForm(ui.Modal, title = "Setup"):
    host = ui.TextInput(label="Host", placeholder = "127.0.0.1:3000", required = True)
    secret = ui.TextInput(label = "Secret key", placeholder = "2a7c...", required = True)

    async def on_submit(self, interaction: discord.Interaction):
        global remoteHost
        global secretKey
        remoteHost = str(self.host)
        secretKey = str(self.secret)
        await interaction.response.send_message(f"```Set host to: {self.host}\nSet secret to {str(self.secret)[:5]}...```", ephemeral = True)
       
# --------- #

class Ai(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")
    
    generate = app_commands.Group(name = "generate", description = "Image generation")
    
    @generate.command(name = "image", description = "Generates an image!")
    async def generateImage(self, interaction: discord.Interaction):
        raise NotImplementedError

    @generate.command(name = "setup")            
    async def setup(self, interaction: discord.Interaction):
        if interaction.user.id == int(config.admin):
            await interaction.response.send_modal(SetupForm())
        else:
            await missingPermissions()
    
    @generate.command(name = "enabled")    
    async def enabled(self, interaction: discord.Interaction, option: Literal["True", "False"]):
        if interaction.user.id == int(config.admin):
            async def response(message = f"Switched to {option}"):
                await interaction.response.send_message(content = message, ephemeral = True)
                
            global enabled
            global channel
            
            if option == "True":
                if remoteHost is not None and secretKey is not None:
                    # TODO check host connection
                    enabled = True
                    channel == interaction.channel_id
                    await response()
                else:
                    await response(message = "Please set the host and secret key")
            if option == "False":
                enabled == False
                await response()
        else:
            await missingPermissions()
            
    # Testing only will be removed in release
    @commands.is_owner()
    @commands.command()
    async def teststatus(self, ctx: commands.Context):
        await ctx.reply(f"remote host: {remoteHost}\nsecret key: {secretKey}\nenabled: {enabled}\nchannel: {channel}")
    

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Ai(client))    