import discord
from discord.ext import commands
from helpers.constants import *
from main import Config
import re

# This cog is the link fixer

config = Config.getMainInstance()

# --------- #

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=config.timeoutTime):
        super().__init__(timeout=timeout)

    async def on_timeout(self):
        self.clear_items()
        
        await self.message.edit(view=self)

    @discord.ui.button(emoji="\U0001F5D1", style=discord.ButtonStyle.red)
    async def gray_button(self, interaction: discord.Interaction, button:discord.ui.Button):
        message = interaction.message.content

        # This takes the message sent by the bot and finds the id of the user who sent the original message
        originalAuthorID = re.sub("[@<>:]", "", message).split(" ", 1)[0]

        if interaction.user.id != int(originalAuthorID):
            await interaction.response.send_message("You are not the author of this message!", ephemeral=True)
        else:
            await interaction.message.delete()

# --------- #

class Fixer(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")

    # --------- #

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if not config.enabled:
            return
        
        async def match(result):
            print("Match found")
            config.update(totalFixed = config.totalFixed + 1)
            view = Buttons()
            view.message = await message.reply(f"<@{message.author.id}>: {result}", silent=True, view=view)
            await message.delete()
        
        endResult = re.sub(VXPATTERN, VXREPLACEMENT, message.content)
        endResult = re.sub(DDPOSTPATTERN, DDPOSTREPLACEMENT, endResult)
        endResult = re.sub(DDREELPATTERN, DDREELREPLACEMENT, endResult)
        endResult = re.sub(TTPATTERN, TTREPLACEMENT, endResult)
        endResult = re.sub(VMPATTERN, VMREPLACEMENT, endResult)
        endResult = re.sub(PXPATTERN, PXREPLACEMENT, endResult)
        endResult = re.sub(RXPATTERN, RXREPLACEMENT, endResult)
        if endResult != message.content:
            await match(endResult)

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Fixer(client))