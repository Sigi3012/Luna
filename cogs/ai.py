import discord
from discord import app_commands, ui
from discord.ext import commands

from main import Config
from helpers.checks import missingPermissions

import aiohttp
import socket

import os
import base64

from typing import Literal

config = Config.getMainInstance()

remoteHost: str = "http://127.0.0.1:727"
secretKey: str = "secret"
enabled: bool = True
channel: int = 0

class ApiException(Exception):
    def __init__(self, m):
        self.message = m
    def __str__(self):
        return self.message

async def fetchImage(payload):
    connector = aiohttp.TCPConnector(family = socket.AF_INET)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "secret"
    }
    async with aiohttp.ClientSession(connector = connector, headers = headers) as session:
        async with session.post(url = f"{remoteHost}/image", json = payload) as response:
            if response.status == 200:
                json = await response.json()
                return json
            else:
                raise ApiException(f"{response.status}: Error while contacting api")

def handleDecode(userId: int, response):
    if not os.path.exists(path = f"./cache/{userId}"):
        os.makedirs(f"./cache/{userId}")
    
    with open(f"./cache/{userId}/aiOutput.png", "wb") as file:
        try:
            file.write(base64.b64decode(response["images"][0]))
            print("successfully wrote to file")
        except Exception as e:
            print(e)

# --------- #

class InputForm(ui.Modal, title = "Generate an image!"):
    prompt = ui.TextInput(label="Prompt", placeholder = "1girl, best_quality, ...", required = True)
    negativePrompt = ui.TextInput(label = "Negative Prompt", placeholder = "bad quality, worst quality", required = False)
    
    async def on_submit(self, interaction: discord.Interaction):
        print("submitted")
        payload = {
            "prompt": str(self.prompt),
            "negativePrompt": str(self.negativePrompt)
        }
        
        try:
            await interaction.response.send_message(content = "Please wait..", ephemeral = True, delete_after = 5)
            res = await fetchImage(payload)
        except Exception as e:
            await interaction.response.send_message(content = e, ephemeral = True)
            return

        handleDecode(interaction.user.id, res)

        print(interaction.channel_id)
        instance = await Ai.getInstance()
        channel = await instance.getChannel(id = interaction.channel_id)
        await channel.send(content = f"<@{interaction.user.id}>", file = discord.File(f"./cache/{interaction.user.id}/aiOutput.png"))
        
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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            raise Exception("An instance of the client already exists.")
    
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")
    
    @classmethod
    async def getInstance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    async def getChannel(self, id):
        return self.client.get_channel(id)
    
    generate = app_commands.Group(name = "generate", description = "Image generation")
    
    @generate.command(name = "image", description = "Generates an image!")
    async def generateImage(self, interaction: discord.Interaction):
        await interaction.response.send_modal(InputForm())

    @generate.command(name = "setup")            
    async def setup(self, interaction: discord.Interaction):
        if interaction.user.id == int(config.admin):
            await interaction.response.send_modal(SetupForm())
        else:
            await missingPermissions(interaction)
    
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
            await missingPermissions(interaction)
            
    # Testing only will be removed in release
    @commands.is_owner()
    @commands.command()
    async def teststatus(self, ctx: commands.Context):
        await ctx.reply(f"remote host: {remoteHost}\nsecret key: {secretKey}\nenabled: {enabled}\nchannel: {channel}")
    

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Ai(client))    