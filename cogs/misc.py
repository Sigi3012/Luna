from discord.ext import commands
from main import Config
import discord
from datetime import datetime
from random import randint

config = Config.getMainInstance()

# --------- #

class Misc(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        
        self.options = [
            "guild_update", "channel_create", "channel_update", "channel_delete", "overwrite_create",
            "overwrite_update", "overwrite_delete", "kick", "ban", "unban", "member_update",
            "member_role_update", "member_move", "member_disconnect", "role_create", "role_update",
            "role_delete", "invite_create", "invite_delete", "emoji_create", "emoji_update", "emoji_delete",
            "sticker_create", "sticker_update", "sticker_delete", "message_delete", "message_pin",
            "message_unpin", "automod_block_message", "automod_flag_message"
        ]
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog: {__name__} has loaded")
        self.moderationChannel = self.client.get_channel(int(config.modchannel))
        
    # --------- #
        
    async def buildEmbed(self, action, user, before, after, target):
        print("New entry")
        _before = dict(before)
        _after = dict(after)
        
        try:
            targetName = target.name
            targetDescription = target.description
            
            targetString = f"Target: {targetName}\n{targetDescription}\n\n"
        except AttributeError:
            targetString = None

        for key, value in _before.items():
            beforekey = key
            beforevalue = value
            
        for key, value in _after.items():
            afterkey = key
            aftervalue = value
            
        e = discord.Embed(
            title = action,
            description = f"{targetString}Before: {beforekey} = {beforevalue}\nAfter: {afterkey} = {aftervalue}",
            colour = 0x383cc6,
            timestamp = datetime.now()
        )
        e.set_author(name = user.global_name, icon_url = user.avatar.url)
        await self.moderationChannel.send(embed = e)
        
    # --------- #

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if config.modchannel == None:
            return
        
        print("cute and fnny")
        print(entry.action.name)
        print(entry.user.global_name)
        print(entry.before)
        print(entry.after)
        print(entry.target)
        
        await self.buildEmbed(
            entry.action.name,
            entry.user,
            entry.before,
            entry.after,
            entry.target
        )
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        
        options = [
            "https://tenor.com/view/bronya-seele-bronyaseele-seele-x-bronya-bronya-x-seele-gif-22095999",
            "https://tenor.com/view/kiss-anime-engage-kiss-maribel-hearn-usami-renko-gif-15812160006411953887"
            "https://tenor.com/view/hop-on-ffxiv-hop-on-hop-on-ff14-lunatwt-lunanoko-gif-25665714",
            "https://tenor.com/view/bloom-into-you-yagate-kimi-ni-naru-yuri-kiss-gif-21637575",
            "https://tenor.com/view/yuri-couple-lgbt-kiss-gif-12095090",
            "https://tenor.com/view/anime-cuddle-cute-gif-12668872",
            "https://tenor.com/view/bloom-into-you-yagate-kimi-ni-naru-yuu-koito-touko-nanami-yuri-gif-23478164",
            "https://tenor.com/view/bed-animeyuri-aoi-hana-sweetblueflowers-gif-23212941",
            "https://tenor.com/view/kiss-kiss-girl-kiss-girl-anime-kiss-girl-manga-anime-gif-14374952",
            "https://tenor.com/view/anime-yuri-kiss-make-out-sakura-trick-gif-15788996"
        ]
        
        items = len(options)
        
        choice = randint(1, items)
        
        if message.content == "!gay":
            await message.reply(options[choice - 1])

# --------- #


async def setup(client:commands.Bot) -> None:
    await client.add_cog(Misc(client))
