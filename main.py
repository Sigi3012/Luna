import discord
from discord import app_commands
import json
import time
import re

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

with open("config.json", "r") as file:
    config = json.load(file)

def currentTime():
    return time.strftime("%H:%M:%S", time.localtime())

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=60):
        super().__init__(timeout=timeout)

    async def on_timeout(self):
        self.clear_items()
        
        await self.message.edit(view=self)

    @discord.ui.button(emoji="\U0001F5D1", style=discord.ButtonStyle.red)
    async def gray_button(self, interaction: discord.Interaction, button:discord.ui.Button):
        message = interaction.message.content

        originalAuthorID = re.sub("[@<>:]", "", message).split(" ", 1)[0]

        if interaction.user.id != int(originalAuthorID):
            await interaction.response.send_message("You are not the author of this message!", ephemeral=True)
        else:
            await interaction.message.delete()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.nsfw:
        if config["nsfwAllowed"] != True:
            return
        else:
            pass
    else:
        pass

    async def match(result):
        print("Match found")
        view = Buttons()
        view.message = await message.reply(f"<@{message.author.id}>: {result}", silent=True, view=view)
        await message.delete()

    VXPATTERN = r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)(?:/photo/\d)?'
    VXREPLACEMENT = r'https://vxtwitter.com/\1/status/\2'
    DDREELPATTERN = r'https?://(?:www\.)?instagram\.com\/reel\/([a-zA-Z0-9_-]+)(\/\?igshid=[a-zA-Z0-9_-]+)?'
    DDREELREPLACEMENT = r'https://ddinstagram.com/reel/\1\2'
    DDPOSTPATTERN= r'https://(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)(/\?utm_source=ig_web_copy_link)?'
    DDPOSTREPLACEMENT = r'https://ddinstagram.com/p/\1'
    TTPATTERN = r'https:\/\/(?:www\.|vm\.)?tiktok\.com\/@([^\/]+)\/video\/(\d+)'
    TTREPLACEMENT = r'https://vxtiktok.com/@\1/video/\2'
    VMPATTERN = r'https:\/\/vm\.tiktok\.com\/([\[A-Za-z0-9]+)'
    VMREPLACEMENT = r'https://vm.vxtiktok.com/\1'
    PXPATTERN = r'https:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?(?:artworks|member_illust)\/(\d+)'
    PXREPLACEMENT = r'https://phixiv.net/artworks/\1'
    RXPATTERN = r'https?:\/\/(?:www\.)?(reddit\.com)\/(.*)'
    RXREPLACEMENT = r'https://rxddit.com/\2'

    endResult = re.sub(VXPATTERN, VXREPLACEMENT, message.content)
    endResult = re.sub(DDPOSTPATTERN, DDPOSTREPLACEMENT, endResult)
    endResult = re.sub(DDREELPATTERN, DDREELREPLACEMENT, endResult)
    endResult = re.sub(TTPATTERN, TTREPLACEMENT, endResult)
    endResult = re.sub(VMPATTERN, VMREPLACEMENT, endResult)
    endResult = re.sub(PXPATTERN, PXREPLACEMENT, endResult)
    endResult = re.sub(RXPATTERN, RXREPLACEMENT, endResult)
    if endResult != message.content:
        await match(endResult)

@tree.command(name= "shutdown", description = "turns off the bot!")
@app_commands.checks.has_permissions(administrator=True)
async def shutdown(interaction):
    await interaction.response.send_message("Shutting down...", delete_after=3.0, ephemeral=True)
    print(f"Bot offline@{currentTime()}")
    await client.close()
@tree.error
async def on_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You don't have permissions to do this!", ephemeral=True)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Online!@{currentTime()}")

if __name__ == "__main__":
    client.run(config["token"])