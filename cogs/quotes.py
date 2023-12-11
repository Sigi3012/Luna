import discord
from discord.ext import commands
from discord import app_commands

from main import Config
from helpers.imageGenerator import createQuoteImage
from helpers.database import checkCooldown

config = Config.getMainInstance()

# --------- #

class Quotes(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.ctx_menu = app_commands.ContextMenu(
            name = 'Quote this message',
            callback = self.quoteThis
        )
        self.client.tree.add_command(self.ctx_menu)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")

    async def cog_unload(self) -> None:
        self.client.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def quoteThis(self, interaction: discord.Interaction, message: discord.Message):
        remainingTime = await checkCooldown(interaction.user.id)
        if remainingTime > 0:
            remainingTime /= 60
            await interaction.response.send_message(f"This command is on cooldown, you can use it in {remainingTime:.2f} minutes.", ephemeral=True)
            return
        
        await createQuoteImage(
            message.content,
            message.author.display_avatar.url,
            message.author.display_name,
            message.author.id,
            message.author.colour,
            message.created_at
        )
        
        jumpButton = discord.ui.Button(label="Jump to original message", url=message.jump_url)
        view = discord.ui.View()
        view.add_item(jumpButton)
        
        quoteChannel = self.client.get_channel(int(config.qoutechannelid))
        await quoteChannel.send(
            content = f"Quoted by <@{interaction.user.id}>",
            file = discord.File(r'./cache/quoteOutput.png'),
            view = view
        )

        print(f"Quote sent to {quoteChannel} channel")
        await interaction.response.send_message("Quoted!")

# --------- #

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Quotes(client))
