import discord
from discord import app_commands, ui
from discord.ext import commands, tasks

from main import Config
from helpers.checks import missingPermissions
from helpers.database import checkCooldown, addToBlacklist, removeFromBlacklist, loadBlacklist

import aiohttp
import socket

import os
import base64
import asyncio

from datetime import datetime

from typing import Literal, Optional

config = Config.getMainInstance()

remoteHost: str = None 
secretKey: str = None 
enabled: bool = False 
channel: int = 0

class _Configuration():
    steps: int = 25
    height: int = 512
    width: int = 512

# --------- #

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
                raise ApiException(f"[AI][ERROR] {response.status}: Error while contacting api")

def handleDecode(userId: int, response):
    if not os.path.exists(path = f"./cache/{userId}"):
        os.makedirs(f"./cache/{userId}")
    
    with open(f"./cache/{userId}/aiOutput.png", "wb") as file:
        try:
            file.write(base64.b64decode(response["images"][0]))
            print("[AI][INFO] Successfully wrote bytes to image")
        except Exception as e:
            print(e)
            
async def handleLogging(userId: int, prompt: str, negativePrompt: Optional[str]):
    # Meant to be ran AFTER handleDecode()
    
    with open(f"./cache/{userId}/promptLog.txt", "a") as file:
        try:
            file.write(f"Prompt: {prompt}\nNegative Prompt: {negativePrompt}\nTimestamp: {datetime.now()}\n\n")
            print("[AI][INFO] Successfully wrote to log")
        except Exception as e:
            print(e)

# --------- #

class InputForm(ui.Modal, title = "Generate an image!"):
    prompt = ui.TextInput(label="Prompt", placeholder = "1girl, best_quality, ...", required = True)
    negativePrompt = ui.TextInput(label = "Negative Prompt", placeholder = "bad quality, worst quality", required = False)
    
    async def on_submit(self, interaction: discord.Interaction):
        payload = {
            "prompt": str(self.prompt),
            "negativePrompt": str(self.negativePrompt),
            "steps": _Configuration.steps,
            "height": _Configuration.height,
            "width": _Configuration.width
        }
        
        print("[AI][INFO] Attempting to generate image")
        print(payload)
        
        try:
            await interaction.response.send_message(content = "Please wait..", ephemeral = True, delete_after = 5)
            res = await fetchImage(payload)
        except Exception as e:
            await interaction.response.send_message(content = e, ephemeral = True)
            return

        userId = interaction.user.id
        
        handleDecode(userId, res)
        await handleLogging(userId, str(self.prompt), str(self.negativePrompt))
        
        try:
            instance = await Ai.getInstance()
            channel = await instance.getChannel(id = interaction.channel_id)

            prompt = str(self.prompt)
            negativePrompt = str(self.negativePrompt)

            if len(prompt) > 50:
                prompt = f"{prompt}..."
            if len(negativePrompt) > 50:
                negativePrompt = f"{negativePrompt}..."
            
            await channel.send(content = f"<@{interaction.user.id}>\n```Prompt: {prompt}\nNegative Prompt: {negativePrompt}```", file = discord.File(f"./cache/{interaction.user.id}/aiOutput.png"))
            print(f"[AI][INFO] Successfully sent image to {interaction.channel_id}")
        except Exception as e:
            print(f"[AI][ERROR] Something went wrong! Error: {e}")
        
class SetupForm(ui.Modal, title = "Setup"):
    host = ui.TextInput(label="Host", placeholder = "127.0.0.1:3000", required = True)
    secret = ui.TextInput(label = "Secret key", placeholder = "2a7c...", required = True)

    async def on_submit(self, interaction: discord.Interaction):
        global remoteHost
        global secretKey
        remoteHost = str(self.host)
        secretKey = str(self.secret)
        print(f"[AI][INFO] Set host to: {self.host}\nSet secret to {str(self.secret)}")
        await interaction.response.send_message(f"```Set host to: {self.host}\nSet secret to {str(self.secret)[:5]}...```", ephemeral = True)
        
class ConfigurationForm(ui.Modal, title = "Change default prompt settings"):
    steps = ui.TextInput(label = "Steps", placeholder = "25", required = True)
    height = ui.TextInput(label = "Height", placeholder = "512", required = True)
    width = ui.TextInput(label = "Width", placeholder = "512", required = True)
    
    async def on_submit(self, interaction: discord.Interaction):
        _Configuration.steps = int(self.steps.value)
        _Configuration.height = int(self.height.value)
        _Configuration.width = int(self.width.value)
       
        print(f"[AI][INFO] Configuration updated to:\nSteps: {self.steps}\nHeight: {self.height}\nWidth: {self.width}")
        await interaction.response.send_message(f"Set configuration to\n```Steps: {self.steps}\nHeight: {self.height}\nWidth: {self.width}```", ephemeral = True)
       
# --------- #

class Ai(commands.Cog):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            raise Exception("An instance of the client already exists.")
    
    async def async__init__(self, client: commands.Bot):
        self.client = client

        blacklist = await loadBlacklist()
        self.blacklistedUsers = blacklist

    def __init__(self, client: commands.Bot):
        asyncio.create_task(self.async__init__(client))

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")

    async def handleBlacklist(self):
        databaseIds = await loadBlacklist()
        # If in local list not in db
        newUsers = [a for a in self.blacklistedUsers if a not in databaseIds]
        # If in db not in local list
        removedUsers = [b for b in databaseIds if b not in self.blacklistedUsers]

        for id in newUsers:
            await addToBlacklist(id)

        for id in removedUsers:
            await removeFromBlacklist(id)

    @tasks.loop(minutes = 30)
    async def blacklistTask(self):
        try:
            await self.handleBlacklist()
        except Exception as e:
            print("[TASK][ERROR] Something went wrong with the blacklist task loop, see error below.")
            print(e)

    async def cog_unload(self):
        await self.handleBlacklist()

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
        if interaction.channel_id != channel:
            await interaction.response.send_message("You cannot use that command here!")
            return

        # Implement this better another time
        remainingTime = await checkCooldown(interaction.user.id)
        if remainingTime > 0:
            remainingTime /= 60
            await interaction.response.send_message(f"This command is on cooldown, you can use it in {remainingTime:.2f} minutes.", ephemeral=True)
            return

        if interaction.user.id in self.blacklistedUsers:
            await interaction.response.send_message("You are not allowed to use this command", ephemeral = True)
            print(f"[AI][INFO] A blacklisted user {interaction.user.id} tried to generate an image!")
            return
        
        await interaction.response.send_modal(InputForm())

    @generate.command(name = "setup", description = "Sets up configuration")            
    async def setup(self, interaction: discord.Interaction):
        if interaction.user.id == int(config.admin):
            await interaction.response.send_modal(SetupForm())
        else:
            await missingPermissions(interaction)
    
    @generate.command(name = "enabled")    
    async def enabled(self, interaction: discord.Interaction, option: Literal["True", "False"]):
        if interaction.user.id == int(config.admin):    
            global enabled
            global channel
            
            if option == "True":
                if remoteHost is not None and secretKey is not None:
                    try:
                        connector = aiohttp.TCPConnector(family = socket.AF_INET)
                        async with aiohttp.ClientSession(connector = connector) as session:
                            async with session.get(url = f"{remoteHost}/ping") as response:
                                if response.status == 200:
                                    pass
                    except aiohttp.ClientConnectionError as e:
                        await interaction.response.send_message(content = f"Connection refused\n```{e}```", ephemeral = True)
                        return
                    
                    enabled = True
                    channel = interaction.channel_id
                    await interaction.response.send_message(content = f"Successfully enabled in <#{channel}>", ephemeral = True)
                else:
                    await interaction.response.send_message(content = "Please set a host and secret key", ephemeral = True)
            if option == "False":
                enabled = False
                channel = 0
                
                try:
                    connector = aiohttp.TCPConnector(family = socket.AF_INET)
                    headers = {
                        "Authorization": "secret"
                    }
                    async with aiohttp.ClientSession(connector = connector, headers = headers) as session:
                        async with session.delete(url = f"{remoteHost}/shutdown") as response:
                            if response.status == 401:
                                print(response)
                            else:
                                pass
                except aiohttp.ClientConnectionError:
                    # I couldnt figure out how to return and then close the elysiajs server after the reponse so oh well
                    pass
                
                await interaction.response.send_message(content = "Successfully disabled", ephemeral = True)
        else:
            await missingPermissions(interaction)
    
    @generate.command(name = "configurate")
    async def configurate(self, interaction: discord.Interaction):
        if interaction.user.id == int(config.admin):
           await interaction.response.send_modal(ConfigurationForm()) 
        else:
            await missingPermissions(interaction)

    @generate.command(name = "blacklist")
    async def blacklist(self, interaction: discord.Interaction, mode: Literal["Add", "Remove"], userid: str):
        if interaction.user.id == int(config.admin):
            userId = int(userid)
            if mode == "Add":
                self.blacklistedUsers.append(userId)
                await interaction.response.send_message(f"<@{userId}> has been added to the blacklist", ephemeral = True)
            if mode == "Remove":
                if userId not in self.blacklistedUsers:
                    await interaction.response.send_message("This user is not in the blacklist", ephemeral = True)
                self.blacklistedUsers.remove(userId)
                await interaction.response.send_message(f"<@{userId}> has been removed from the blacklist", ephemeral = True)
        else:
            await missingPermissions(interaction)
        
# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Ai(client)) 