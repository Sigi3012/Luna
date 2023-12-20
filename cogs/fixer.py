import discord
from discord.ext import commands
from helpers.constants import *
from helpers.pinterestEmbed import scrapeHTML, getData
from main import Config
import re
from datetime import datetime

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
        
        if message.channel.nsfw and config.nsfwAllowed != True:
            return
        
        endResult = re.sub(FXPATTERN, FXREPLACEMENT, message.content)
        endResult = re.sub(DDPOSTPATTERN, DDPOSTREPLACEMENT, endResult)
        endResult = re.sub(DDREELPATTERN, DDREELREPLACEMENT, endResult)
        endResult = re.sub(TTPATTERN, TTREPLACEMENT, endResult)
        endResult = re.sub(VMPATTERN, VMREPLACEMENT, endResult)
        endResult = re.sub(PXPATTERN, PXREPLACEMENT, endResult)
        endResult = re.sub(RXPATTERN, RXREPLACEMENT, endResult)
        
        pinterestCheck = re.match(PNPATTERN, endResult)
        if pinterestCheck:
            pinID = pinterestCheck.group(1)
            
            html = await scrapeHTML(pinID)
            
            if html == None:
                await message.reply("Something went wrong!")
                return
            
            data = await getData(html)
            
            embed = discord.Embed(
                title = data[1],
                url = pinterestCheck.group(0),
                colour = 0xfc4f6a,
                timestamp = datetime.now(),
            )
            embed.set_image(url = data[0])
            embed.set_footer(text = data[2])
            
            content = re.sub(PNPATTERN, "", endResult)
            
            view = Buttons()
            view.message = await message.reply(f"<@{message.author.id}>: {content}", silent=True, embed=embed, view=view)
            
            await message.delete()
            return
        
        if endResult != message.content:
            print("Match found")
            config.update(totalFixed = config.totalFixed + 1)
            
            view = Buttons()
            view.message = await message.reply(f"<@{message.author.id}>: {endResult}", silent=True, view=view)
            
            await message.delete()
            return

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Fixer(client))