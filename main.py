import discord
from discord import app_commands
import json
import time
import re
import asyncio
import checks

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

with open("config.json", "r") as file:
    config = json.load(file)

checks.check()

def currentTime():
    return time.strftime("%H:%M:%S", time.localtime())

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(emoji="\U0001F5D1", style=discord.ButtonStyle.red)
    async def gray_button(self, interaction: discord.Interaction, button:discord.ui.Button):
        message = interaction.message.content

        # This takes the message sent by the bot and finds the id of the user who sent the original message
        originalAuthorID = re.sub("[@<>:]", "", message).split(" ", 1)[0]
        
        if interaction.user.id != int(originalAuthorID):
            await interaction.response.send_message("You are not the author of this message!", ephemeral=True)
        else:
            await interaction.message.delete()
    
@tree.command(
    name = "toggle",
    description = "This enables or disables the fixer")
async def togglefixer(interaction):
    if interaction.user.id == int(config["admin"]):
        config['enabled'] = not config['enabled']
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await interaction.response.send_message(f"Toggled to {config['enabled']}", ephemeral=True)
        print(f"Toggled to: {config['enabled']}@{currentTime()}")
    else:
        await checks.missingPermissions(interaction)
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not config["enabled"]:
        return
    
    async def match(result):
        print("Match found")
        await message.reply(f"<@{message.author.id}>: {result}", silent=True, view=Buttons())
        await asyncio.sleep(1e-3)
        await message.delete()
        
    VXPATTERN = r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)(?:/photo/\d)?'
    VXREPLACEMENT = r'https://vxtwitter.com/\1/status/\2'
    DDPATTERN = r'https?://(?:www\.)?instagram\.com\/reel\/([a-zA-Z0-9_-]+)(\/\?igshid=[a-zA-Z0-9_-]+)?'
    DDREPLACEMENT = r'https://ddinstagram.com/reel/\1\2'
    TTPATTERN = r'https:\/\/(?:www\.|vm\.)?tiktok\.com\/@([^\/]+)\/video\/(\d+)'
    TTREPLACEMENT = r'https://vxtiktok.com/@\1/video/\2'
    VMPATTERN = r'https:\/\/vm\.tiktok\.com\/([\[A-Za-z0-9]+)'
    VMREPLACEMENT = r'https://vm.vxtiktok.com/\1'
    PXPATTERN = r'https:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?(?:artworks|member_illust)\/(\d+)'
    PXREPLACEMENT = r'https://phixiv.net/artworks/\1'
    RXPATTERN = r'https?:\/\/(?:www\.)?(reddit\.com)\/(.*)'
    RXREPLACEMENT = r'https://rxddit.com/\2'
    
    endResult = re.sub(VXPATTERN, VXREPLACEMENT, message.content)
    endResult = re.sub(DDPATTERN, DDREPLACEMENT, endResult)
    endResult = re.sub(TTPATTERN, TTREPLACEMENT, endResult)
    endResult = re.sub(VMPATTERN, VMREPLACEMENT, endResult)
    endResult = re.sub(PXPATTERN, PXREPLACEMENT, endResult)
    endResult = re.sub(RXPATTERN, RXREPLACEMENT, endResult)
    if endResult != message.content:
        await match(endResult)
    
@tree.command(name= "shutdown", description = "turns off the bot!")
async def shutdown(interaction):
    if interaction.user.id == int(config["admin"]):
        await interaction.response.send_message("Shutting down...", delete_after=3.0, ephemeral=True)
        print(f"Bot offline@{currentTime()}")
        await client.close()
    else:
        await checks.missingPermissions(interaction)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Online!@{currentTime()}")
    print(f"Config loaded!@{currentTime()}")

if __name__ == "__main__":    
    client.run(config["token"])